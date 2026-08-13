"""Seed-скрипт: загружает улицы и дома Аскарово из данных parse_askarovo.

Источники данных (в ``scripts/parse_askarovo/``):

* ``askarovo_streets.json`` — улицы и номера домов (вид ``{street: {num: [...]}}``)
* ``askarovo_streets_district.txt`` — привязка улиц к районам
  (строки ``улица<TAB>район``, район может быть с префиксом ``=``)

Перед загрузкой скрипт очищает справочник адресов
(landmarks -> street_synonyms -> houses -> streets -> districts -> towns),
затем создаёт его заново. Поэтому повторный запуск безопасен (идемпотентен).

Использование::

    python scripts/seed_parse_askarovo.py
    python scripts/seed_parse_askarovo.py --base-price 300
    python scripts/seed_parse_askarovo.py --no-clear   # не чистить перед загрузкой
"""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy import delete, select

from app.core.database import async_session_factory
from app.models.address import (
    District,
    House,
    Landmark,
    Street,
    StreetSynonym,
    Town,
)

BASE_DIR = Path(__file__).resolve().parent.parent
PARSE_DIR = BASE_DIR / "scripts" / "parse_askarovo"
DEFAULT_JSON = PARSE_DIR / "askarovo_streets.json"
DEFAULT_DISTRICT_MAP = PARSE_DIR / "askarovo_streets_district.txt"

TOWN_NAME = "Аскарово"

# Суффиксы типа улицы, которые отрезаются от названия (из данных parse_askarovo).
STREET_TYPE_SUFFIXES = (
    " ул.",
    " улица",
    " переулок",
    " пер.",
    " проспект",
    " пр.",
    " шоссе",
    " бульвар",
)


def _strip_street_type(name: str) -> str:
    """Отрезает суффикс типа улицы: ``'Ленина ул.'`` -> ``'Ленина'``."""
    name = name.strip()
    for suffix in STREET_TYPE_SUFFIXES:
        if name.endswith(suffix):
            return name[: -len(suffix)].strip()
    return name


def _load_district_map(path: Path) -> dict[str, str]:
    """Читает txt-файл ``улица -> район`` и возвращает {название улицы: район}.

    Ключи (названия улиц) нормализуются — у них отрезается суффикс типа,
    чтобы совпадать с ключами из ``askarovo_streets.json``.
    """
    result: dict[str, str] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip() or line.startswith("улица"):
            continue
        parts = line.split("\t")
        if len(parts) < 2:
            continue
        street = _strip_street_type(parts[0])
        district = parts[1].strip().lstrip("=").strip()
        if street and district:
            result[street] = district
    return result


def _load_streets_json(path: Path) -> dict[str, dict[str, list[str]]]:
    """Читает JSON и возвращает ``{название улицы: {номер дома: [urls]}}``."""
    data = json.loads(path.read_text(encoding="utf-8"))
    return data["addresses"]


def _match_district(
    street: str,
    district_map: dict[str, str],
    strict_map: dict[str, str],
) -> str | None:
    """Находит район для улицы ``street``.

    Сначала точное совпадение по нормализованному имени. Если его нет —
    допускаем усечённое имя (например, ``'Шагали Шакман'`` из JSON против
    ``'Шагали Шакмана'`` в карте) — берём запись, которая начинается с имени.
    Возвращает название района или ``None``.
    """
    if street in district_map:
        return district_map[street]
    for mapped in strict_map:
        if mapped.startswith(street) or street.startswith(mapped):
            return district_map[mapped]
    return None


async def _clear_addresses(session) -> None:
    """Удаляет все записи справочника адресов (в порядке зависимостей)."""
    await session.execute(delete(Landmark))
    await session.execute(delete(StreetSynonym))
    await session.execute(delete(House))
    await session.execute(delete(Street))
    await session.execute(delete(District))
    await session.execute(delete(Town))


async def run_seed(
    streets_json: dict[str, dict[str, list[str]]],
    district_map: dict[str, str],
    base_price: int,
    clear: bool,
) -> dict:
    """Очищает справочник (опционально) и наполняет его улицами и домами.

    Возвращает словарь-сводку со счётчиками и предупреждениями.
    """
    strict_map = dict(district_map)  # полные имена (с суффиксом) для fallback
    unmatched: list[str] = []
    stats = {
        "towns_created": 0,
        "districts_created": 0,
        "streets_created": 0,
        "houses_created": 0,
        "houses_skipped": 0,
        "streets_skipped": 0,
    }

    async with async_session_factory() as session:
        if clear:
            await _clear_addresses(session)

        # --- Город ---
        town = await session.scalar(select(Town).where(Town.name == TOWN_NAME))
        if town is None:
            town = Town(name=TOWN_NAME, base_price=base_price)
            session.add(town)
            await session.flush()
            stats["towns_created"] = 1

        for street_key in sorted(streets_json):
            street_name = _strip_street_type(street_key)
            district_name = district_map.get(street_name) or _match_district(
                street_name, district_map, strict_map
            )
            if district_name is None:
                unmatched.append(street_key)
                continue

            district = await session.scalar(
                select(District).where(
                    District.town_id == town.id,
                    District.name == district_name,
                )
            )
            if district is None:
                district = District(town_id=town.id, name=district_name)
                session.add(district)
                await session.flush()
                stats["districts_created"] += 1

            street = await session.scalar(
                select(Street).where(
                    Street.district_id == district.id,
                    Street.name == street_name,
                )
            )
            if street is None:
                street = Street(district_id=district.id, name=street_name)
                session.add(street)
                await session.flush()
                stats["streets_created"] += 1
            else:
                stats["streets_skipped"] += 1

            for number in sorted(streets_json[street_key]):
                house = await session.scalar(
                    select(House).where(
                        House.street_id == street.id,
                        House.number == number,
                    )
                )
                if house is None:
                    session.add(House(street_id=street.id, number=number))
                    stats["houses_created"] += 1
                else:
                    stats["houses_skipped"] += 1

        await session.commit()

    stats["unmatched_streets"] = unmatched
    return stats


# --------------------------------------------------------------------------
# CLI
# --------------------------------------------------------------------------


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Загружает улицы и дома Аскарово из данных parse_askarovo."
    )
    parser.add_argument(
        "--streets-json",
        type=Path,
        default=DEFAULT_JSON,
        help="JSON с улицами и домами (по умолчанию scripts/parse_askarovo/askarovo_streets.json)",
    )
    parser.add_argument(
        "--district-map",
        type=Path,
        default=DEFAULT_DISTRICT_MAP,
        help="Файл соответствия улица->район (по умолчанию scripts/parse_askarovo/askarovo_streets_district.txt)",
    )
    parser.add_argument(
        "--base-price",
        type=int,
        default=0,
        help="Базовая цена поездки по городу (поле Town.base_price, обязательное)",
    )
    parser.add_argument(
        "--no-clear",
        action="store_true",
        help="Не очищать справочник адресов перед загрузкой",
    )
    args = parser.parse_args()

    if not args.streets_json.is_file():
        parser.error(f"Файл не найден: {args.streets_json}")
    if not args.district_map.is_file():
        parser.error(f"Файл не найден: {args.district_map}")

    streets_json = _load_streets_json(args.streets_json)
    district_map = _load_district_map(args.district_map)

    print(
        f"Источник: {args.streets_json.name} "
        f"(улиц: {len(streets_json)}, домов: "
        f"{sum(len(v) for v in streets_json.values())})."
    )
    print(f"Карта районов: {args.district_map.name} (улиц: {len(district_map)}).")
    print(
        "Загружаю в БД..."
        + (" (с очисткой справочника адресов)" if not args.no_clear else "")
    )

    stats = asyncio.run(
        run_seed(
            streets_json=streets_json,
            district_map=district_map,
            base_price=args.base_price,
            clear=not args.no_clear,
        )
    )

    print()
    print("Готово.")
    for label, key in (
        ("Городов создано:    ", "towns_created"),
        ("Районов создано:    ", "districts_created"),
        ("Улиц создано:       ", "streets_created"),
        ("Улиц пропущено:     ", "streets_skipped"),
        ("Домов создано:      ", "houses_created"),
        ("Домов пропущено:    ", "houses_skipped"),
    ):
        print(f"  {label}{stats[key]}")

    if stats["unmatched_streets"]:
        print()
        print("Улицы без района (пропущены):")
        for name in stats["unmatched_streets"]:
            print(f"  - {name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

