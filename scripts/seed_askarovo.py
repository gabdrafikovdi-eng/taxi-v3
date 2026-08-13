"""Seed-скрипт: загружает данные из ``docs/askarovo.yaml`` в БД через ORM-модели.

Использование::

    python scripts/seed_askarovo.py
    python scripts/seed_askarovo.py --yaml docs/askarovo.yaml --base-price 300

Скрипт идемпотентен: повторный запуск не создаёт дубликаты
(города/районы/улицы ищутся по имени и переиспользуются).
"""

from __future__ import annotations

import argparse
import ast
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy import select

from app.core.database import async_session_factory
from app.models.address import District, Street, Town

DEFAULT_YAML = Path(__file__).resolve().parent.parent / "docs" / "askarovo.yaml"


# --------------------------------------------------------------------------
# Парсер YAML
# --------------------------------------------------------------------------


def _unquote(value: str) -> str:
    """Снимает кавычки со скалярного значения YAML."""
    value = value.strip()
    if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
        try:
            return ast.literal_eval(value)
        except (SyntaxError, ValueError):
            return value[1:-1]
    return value


def _parse_simple_yaml(text: str) -> dict:
    """Минимальный парсер YAML для структуры ``docs/askarovo.yaml``.

    Используется как fallback, когда в окружении не установлен PyYAML.
    Поддерживает вложенные mapping'и, последовательности и кавычки
    (одинарные/двойные) — этого достаточно для файла с адресами.

    Результат для этой структуры эквивалентен ``yaml.safe_load``::

        {"town": [{"name": "Аскарово"}, {"districts": [...]}]}
    """
    lines: list[tuple[int, str]] = []
    for raw in text.splitlines():
        line = raw.rstrip()
        if not line.strip() or line.strip().startswith("#"):
            continue
        stripped = line.lstrip()
        lines.append((len(line) - len(stripped), stripped))

    # ``startswith("- ")`` обозначает элемент последовательности.
    def is_seq(ind: int, text: str) -> bool:
        return text.startswith("- ")

    # Читает блок, начинающийся со строки ``idx`` (может быть mapping или
    # последовательностью). Возвращает (значение, индекс первой необработанной
    # строки).
    def parse_block(idx: int) -> tuple[object, int]:
        ind, text = lines[idx]
        if is_seq(ind, text):
            return parse_seq(idx, ind)
        return parse_map(idx, ind)

    def parse_map(idx: int, key_col: int) -> tuple[dict, int]:
        node: dict = {}
        while idx < len(lines) and lines[idx][0] == key_col and not is_seq(*lines[idx]):
            key, _, value = lines[idx][1].partition(":")
            value = value.strip()
            idx += 1
            if value:  # скаляр на той же строке
                node[_unquote(key)] = _unquote(value)
            elif idx < len(lines) and lines[idx][0] > key_col:
                node[_unquote(key)], idx = parse_block(idx)
            else:
                node[_unquote(key)] = {}
        return node, idx

    def parse_seq_item(
        idx: int, item_col: int, first: str
    ) -> tuple[dict, int]:
        """Разбирает mapping-элемент последовательности вида ``- key[: value]``.

        Подхватывает и «родственные» ключи (на той же ``item_col``),
        например ``streets:`` после ``- name: "Центр"``.
        """
        node: dict = {}
        key, _, value = first.partition(":")
        value = value.strip()
        if value:
            node[_unquote(key)] = _unquote(value)
        elif idx < len(lines) and lines[idx][0] >= item_col:
            # Вложенное значение (в т.ч. block-sequence на той же колонке, как
            # ``- districts:`` -> следующий ``- name: ...``).
            node[_unquote(key)], idx = parse_block(idx)
        else:
            node[_unquote(key)] = {}

        # Продолжаем текущий mapping элементами на той же колонке.
        while (
            idx < len(lines)
            and lines[idx][0] == item_col
            and not is_seq(*lines[idx])
        ):
            k, _, v = lines[idx][1].partition(":")
            v = v.strip()
            idx += 1
            if v:
                node[_unquote(k)] = _unquote(v)
            elif idx < len(lines) and lines[idx][0] > item_col:
                node[_unquote(k)], idx = parse_block(idx)
            else:
                node[_unquote(k)] = {}
        return node, idx

    def parse_seq(idx: int, list_col: int) -> tuple[list, int]:
        node: list = []
        while idx < len(lines) and lines[idx][0] == list_col and is_seq(*lines[idx]):
            text = lines[idx][1]
            item_col = list_col + 2  # колонка текста после "- "
            first = text[1:].strip()
            idx += 1
            if first.startswith(("\"", "'")) or ":" not in first:
                node.append(_unquote(first) if first else None)
            elif first.startswith("- "):
                # элемент — вложенная последовательность
                sub, idx = parse_seq(idx - 1, item_col)
                node.append(sub)
            else:
                item, idx = parse_seq_item(idx, item_col, first)
                node.append(item)
        return node, idx

    if not lines:
        return {}
    doc, _ = parse_block(0)
    return doc


def _load_data(path: Path) -> dict:
    """Читает YAML-файл. Предпочитает PyYAML, при его отсутствии — fallback-парсер."""
    text = path.read_text(encoding="utf-8")
    try:
        import yaml  # noqa: PLC0415
    except ImportError:
        return _parse_simple_yaml(text)
    return yaml.safe_load(text)


def _extract(data: dict) -> tuple[str, list[dict]]:
    """Достаёт из структуры файла название города и список районов с улицами.

    Ожидаемая структура::

        town:
          - name: "Аскарово"
          - districts:
            - name: "Центр"
              streets:
                - "Ленина"
    """
    town_items = data.get("town")
    if not isinstance(town_items, list) or not town_items:
        raise ValueError("В YAML не найдена секция 'town' со списком")

    town_name: str | None = None
    districts_raw: list = []
    for item in town_items:
        if not isinstance(item, dict):
            continue
        if "name" in item and town_name is None:
            town_name = item["name"]
        if isinstance(item.get("districts"), list):
            districts_raw = item["districts"]

    if not town_name:
        raise ValueError("В YAML не найдено название города (town[].name)")

    districts: list[dict] = []
    for district in districts_raw:
        if not isinstance(district, dict) or not district.get("name"):
            continue
        streets = district.get("streets")
        districts.append(
            {
                "name": district["name"],
                "streets": [s for s in (streets or []) if s],
            }
        )
    return town_name, districts


# --------------------------------------------------------------------------
# Запись в БД через ORM-модели address
# --------------------------------------------------------------------------


class SeedCounts:
    """Счётчики созданных и пропущенных записей."""

    def __init__(self) -> None:
        self.towns_created = 0
        self.districts_created = 0
        self.streets_created = 0
        self.districts_skipped = 0
        self.streets_skipped = 0


async def run_seed(
    town_name: str, base_price: int, districts: list[dict]
) -> SeedCounts:
    counts = SeedCounts()

    async with async_session_factory() as session:
        # --- Город (Town) ---
        town = await session.scalar(select(Town).where(Town.name == town_name))
        if town is None:
            town = Town(name=town_name, base_price=base_price)
            session.add(town)
            await session.flush()  # нужен id города для районов
            counts.towns_created = 1

        # --- Районы (District) и улицы (Street) ---
        for district_data in districts:
            district = await session.scalar(
                select(District).where(
                    District.town_id == town.id,
                    District.name == district_data["name"],
                )
            )
            if district is None:
                district = District(town_id=town.id, name=district_data["name"])
                session.add(district)
                await session.flush()  # нужен id района для улиц
                counts.districts_created += 1
            else:
                counts.districts_skipped += 1

            for street_name in district_data["streets"]:
                street = await session.scalar(
                    select(Street).where(
                        Street.district_id == district.id,
                        Street.name == street_name,
                    )
                )
                if street is None:
                    session.add(Street(district_id=district.id, name=street_name))
                    counts.streets_created += 1
                else:
                    counts.streets_skipped += 1

        await session.commit()

    return counts


# --------------------------------------------------------------------------
# CLI
# --------------------------------------------------------------------------


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Загружает данные из docs/askarovo.yaml в БД через ORM-модели address."
    )
    parser.add_argument(
        "--yaml",
        type=Path,
        default=DEFAULT_YAML,
        help="Путь к YAML-файлу с адресами (по умолчанию docs/askarovo.yaml)",
    )
    parser.add_argument(
        "--base-price",
        type=int,
        default=0,
        help="Базовая цена поездки по городу (поле Town.base_price, обязательное)",
    )
    args = parser.parse_args()

    if not args.yaml.is_file():
        parser.error(f"Файл не найден: {args.yaml}")

    data = _load_data(args.yaml)
    town_name, districts = _extract(data)

    total_streets = sum(len(d["streets"]) for d in districts)
    print(
        f"Город: {town_name!r}; районов: {len(districts)}; улиц: {total_streets}."
    )
    print("Загружаю в БД...")

    counts = asyncio.run(run_seed(town_name, args.base_price, districts))

    print()
    print("Готово.")
    print(f"  Городов создано:      {counts.towns_created}")
    print(f"  Районов создано:      {counts.districts_created}")
    print(f"  Районов пропущено:    {counts.districts_skipped}")
    print(f"  Улиц создано:         {counts.streets_created}")
    print(f"  Улиц пропущено:       {counts.streets_skipped}")

    if counts.districts_skipped or counts.streets_skipped:
        print("Пропущены записи, которые уже были в БД (скрипт идемпотентен).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())