"""Генератор актуального Markdown-снимка (snapshot) адресных данных БД.

Скрипт при каждом запуске подключается к текущей БД через стандартный механизм
проекта (``app.core.database.async_session_factory``) и формирует подробный отчёт
о РЕАЛЬНОМ состоянии всех адресных сущностей (Town, District, Street, House,
StreetSynonym, Landmark), включая разбор номеров домов существующим парсером
``app.services.address.house_number_parser.parse_house_number``.

Отчёт записывается в ``docs/``:

- ``address_database_snapshot_YYYY-MM-DD_HH-MM-SS.md`` — снимок с датой/временем;
- ``address_database_snapshot_latest.md`` — «последний» снимок (перезаписывается).

Использование (из корня проекта)::

    python scripts/generate_address_snapshot.py
    uv run python scripts/generate_address_snapshot.py

    # другой каталог для отчёта
    python scripts/generate_address_snapshot.py --docs-dir docs

Скрипт строго read-only: только SELECT, никаких INSERT/UPDATE/DELETE/COMMIT.
Никаких секретов/паролей/DSN в отчёт не попадает.
"""

from __future__ import annotations

import argparse
import asyncio
import re
import sys
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

# Импорты приложения делаем «мягко»: если не поднимется конфигурация
# (например, нет .env), пользователь получит понятную ошибку вместо traceback.
_IMPORT_ERROR: Exception | None = None
try:
    from sqlalchemy import select  # noqa: E402
    from sqlalchemy.orm import selectinload  # noqa: E402

    from app.core.database import async_session_factory  # noqa: E402
    from app.core.config import config_settings  # noqa: E402
    from app.models.address import (  # noqa: E402
        District,
        House,
        Landmark,
        Street,
        StreetSynonym,
        Town,
    )
    from app.schemas.address import HouseNumberParts, HouseNumberType  # noqa: E402
    from app.services.address.house_number_parser import (  # noqa: E402
        parse_house_number,
    )
except Exception as exc:  # pragma: no cover
    _IMPORT_ERROR = exc

# Порядок вывода моделей в разделе ORM Schema (по зависимостям).
ADDRESS_MODELS = (Town, District, Street, House, StreetSynonym, Landmark)

DEFAULT_DOCS_DIR = ROOT / "docs"

# Буквы для построения примеров потенциальных вводов (suggestion cases).
_CYRILLIC_LETTERS = "абвгдежзийклмнопрстуфхцчшщъыьэюя"

# ---------------------------------------------------------------------------
# ORM Schema (интроспекция моделей, без запросов к БД)
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class ColumnInfo:
    name: str
    type: str
    nullable: bool
    primary_key: bool
    foreign_key: str | None


@dataclass(frozen=True)
class RelationshipInfo:
    name: str
    target: str
    uselist: bool
    back_populates: str | None


@dataclass(frozen=True)
class ModelSchema:
    name: str
    table_name: str
    columns: list[ColumnInfo]
    relationships: list[RelationshipInfo]


def _format_column_type(col_type) -> str:
    """Форматирует тип колонки SQLAlchemy в строку, например ``String(50)``."""
    type_name = type(col_type).__name__
    length = getattr(col_type, "length", None)
    if length is not None:
        return f"{type_name}({length})"
    return type_name


def load_address_schema() -> list[ModelSchema]:
    """Строит описание ORM-схемы адресов прямо из моделей проекта.

    Никаких запросов к БД — используется только SQLAlchemy mapper.
    """
    schemas: list[ModelSchema] = []
    for model in ADDRESS_MODELS:
        mapper = model.__mapper__

        columns: list[ColumnInfo] = []
        for column in mapper.columns:
            foreign_key = None
            if column.foreign_keys:
                targets = sorted(fk.target_fullname for fk in column.foreign_keys)
                foreign_key = ", ".join(targets)
            columns.append(
                ColumnInfo(
                    name=column.name,
                    type=_format_column_type(column.type),
                    nullable=column.nullable,
                    primary_key=column.primary_key,
                    foreign_key=foreign_key,
                )
            )
        columns.sort(key=lambda c: (not c.primary_key, c.name))

        relationships: list[RelationshipInfo] = []
        for rel in mapper.relationships:
            target = rel.mapper.class_.__name__
            relationships.append(
                RelationshipInfo(
                    name=rel.key,
                    target=target,
                    uselist=rel.uselist,
                    back_populates=rel.back_populates,
                )
            )
        relationships.sort(key=lambda r: r.name)

        schemas.append(
            ModelSchema(
                name=model.__name__,
                table_name=model.__tablename__,
                columns=columns,
                relationships=relationships,
            )
        )
    return schemas



# ---------------------------------------------------------------------------
# Загрузка данных (один граф с eager loading, без N+1)
# ---------------------------------------------------------------------------


@dataclass
class HouseRecord:
    house: House
    street: Street
    district: District
    town: Town
    parsed: HouseNumberParts | None


@dataclass
class LandmarkRecord:
    landmark: Landmark
    street: Street | None
    district: District | None
    town: Town | None
    house: House | None


@dataclass
class LoadedDB:
    towns: list[Town]
    houses: list[HouseRecord]
    landmarks: list[LandmarkRecord]
    schema: list[ModelSchema] = field(default_factory=list)
    alembic_version: str | None = None

    @property
    def districts(self) -> list[District]:
        return [d for t in self.towns for d in t.districts]

    @property
    def streets(self) -> list[Street]:
        return [s for t in self.towns for d in t.districts for s in d.streets]

    @property
    def synonyms(self) -> list[StreetSynonym]:
        return [syn for s in self.streets for syn in s.synonyms]


async def _load_alembic_version(session) -> str | None:
    """Возвращает ревизию схемы (alembic_version) либо None, если её нет."""
    from sqlalchemy import text

    try:
        result = await session.execute(text("SELECT version_num FROM alembic_version"))
        return result.scalar()
    except Exception:
        return None


async def load_database() -> LoadedDB:
    """Загружает ВСЮ адресную иерархию одним графом объектов.

    Используется ``selectinload``: всего несколько SQL-запросов на всю БД
    (по одному на каждую цепочку relationship), без N+1.
    """
    stmt = (
        select(Town)
        .options(
            selectinload(Town.districts)
            .selectinload(District.streets)
            .selectinload(Street.houses),
            selectinload(Town.districts)
            .selectinload(District.streets)
            .selectinload(Street.synonyms),
            selectinload(Town.districts)
            .selectinload(District.streets)
            .selectinload(Street.landmarks)
            .selectinload(Landmark.house),
        )
        .order_by(Town.id)
    )

    async with async_session_factory() as session:
        alembic_version = await _load_alembic_version(session)
        result = await session.execute(stmt)
        towns = list(result.scalars().unique().all())

        # Явно «замораживаем» обратные ссылки (back_populates), пока сессия
        # открыта: selectinload заполняет forward-стороны, но доступ к
        # ``district.town`` / ``street.district`` и т.п. после закрытия сессии
        # вызвал бы lazy load. Здесь эти атрибуты попадают в __dict__ объектов.
        for town in towns:
            for district in town.districts:
                _ = district.town
                for street in district.streets:
                    _ = street.district
                    for house in street.houses:
                        _ = house.street
                    for landmark in street.landmarks:
                        _ = landmark.street
                        if landmark.house is not None:
                            _ = landmark.house

    # Все нужные relationship уже загружены (expire_on_commit=False,
    # сессия закрыта, но атрибуты лежат в объектах).

    houses: list[HouseRecord] = []
    landmarks: list[LandmarkRecord] = []
    for town in towns:
        for district in town.districts:
            for street in district.streets:
                for house in street.houses:
                    houses.append(
                        HouseRecord(
                            house=house,
                            street=street,
                            district=district,
                            town=town,
                            parsed=parse_house_number(house.number),
                        )
                    )
                for landmark in street.landmarks:
                    landmarks.append(
                        LandmarkRecord(
                            landmark=landmark,
                            street=street,
                            district=district,
                            town=town,
                            house=landmark.house,
                        )
                    )

    houses.sort(key=_house_sort_key)
    return LoadedDB(
        towns=towns,
        houses=houses,
        landmarks=landmarks,
        schema=load_address_schema(),
        alembic_version=alembic_version,
    )


def _house_sort_key(rec: HouseRecord) -> tuple:
    """Сортировка домов: base (числовой) → тип → суффикс → исходный номер."""
    parsed = rec.parsed
    if parsed is None:
        return (1, 0, "", 0, "", rec.house.number)

    base = parsed.base
    if base.isdigit():
        base_num = int(base)
        base_str = ""
    else:
        base_num = 10**9
        base_str = base

    type_order = {
        HouseNumberType.PLAIN: 0,
        HouseNumberType.LETTER: 1,
        HouseNumberType.CORPUS: 2,
        HouseNumberType.FRACTION: 3,
    }
    suffix = parsed.suffix or ""
    return (
        0,
        base_num,
        base_str,
        type_order.get(parsed.type, 99),
        suffix,
        rec.house.number,
    )


def _normalize_name(value: str | None) -> str:
    """Нормализация имени для поиска дубликатов (нижний регистр, сжатие пробелов)."""
    if not value:
        return ""
    return re.sub(r"\s+", " ", value.strip().lower())

# ---------------------------------------------------------------------------
# Анализ данных
# ---------------------------------------------------------------------------


def build_house_number_groups(db: LoadedDB) -> list[dict]:
    """Группирует дома по (street, base) для раздела House Number Groups.

    Возвращает список ``{street, district, town, base, numbers: [rec, ...]}``,
    отсортированный по городу → району → улице → base.
    """
    groups: dict[tuple[int, str], list[HouseRecord]] = {}
    for rec in db.houses:
        if rec.parsed is None:
            continue
        groups.setdefault((rec.house.street_id, rec.parsed.base), []).append(rec)

    result = []
    for rec in db.houses:
        if rec.parsed is None:
            continue
        key = (rec.house.street_id, rec.parsed.base)
        # берём запись один раз на группу
        if any((g["street"].id, g["base"]) == key for g in result):
            continue
        result.append(
            {
                "street": rec.street,
                "district": rec.district,
                "town": rec.town,
                "base": rec.parsed.base,
                "records": sorted(groups[key], key=_house_sort_key),
            }
        )

    result.sort(
        key=lambda g: (
            _normalize_name(g["town"].name),
            _normalize_name(g["district"].name),
            _normalize_name(g["street"].name),
            _numeric_base(g["base"]),
        )
    )
    return result


def _numeric_base(base: str) -> tuple:
    if base.isdigit():
        return (0, int(base))
    return (1, base)


def build_suggestion_cases(db: LoadedDB) -> list[dict]:
    """На основе фактических групп (street, base) строит потенциальные
    suggestion-комбинации, обнаруживаемые существующей логикой
    AddressSuggestionService. Это только наблюдаемые факты данных, а не
    бизнес-утверждение о корректности suggestion.
    """
    cases: list[dict] = []
    for group in build_house_number_groups(db):
        type_groups: dict[HouseNumberType, list[str]] = {}
        for r in group["records"]:
            if r.parsed is None:
                continue
            type_groups.setdefault(r.parsed.type, []).append(r.house.number)

        entry = {
            "town": group["town"],
            "district": group["district"],
            "street": group["street"],
            "base": group["base"],
            "records": group["records"],
            "scenarios": [],
        }

        corpus = type_groups.get(HouseNumberType.CORPUS, [])
        if len(corpus) >= 2:
            entry["scenarios"].append(_corpus_scenario(group["base"], corpus))

        fraction = type_groups.get(HouseNumberType.FRACTION, [])
        if len(fraction) >= 2:
            entry["scenarios"].append(_fraction_scenario(group["base"], fraction))

        letters = type_groups.get(HouseNumberType.LETTER, [])
        if len(letters) >= 2:
            entry["scenarios"].append(_letter_scenario(group["base"], letters))

        non_plain = [
            r.house.number
            for r in group["records"]
            if r.parsed is not None and r.parsed.type is not HouseNumberType.PLAIN
        ]
        if non_plain:
            entry["scenarios"].append(
                {
                    "kind": "plain_request",
                    "label": "Дом без указания варианта (PLAIN)",
                    "input": group["base"],
                    "candidates": non_plain,
                }
            )

        if entry["scenarios"]:
            cases.append(entry)

    return cases


def _letter_scenario(base: str, letters: list[str]) -> dict:
    present = {s[-1] for s in letters}
    example = None
    for ch in _CYRILLIC_LETTERS:
        if ch not in present:
            example = f"{base}{ch}"
            break
    return {
        "kind": "letter",
        "label": "Литера у дома (LETTER)",
        "input": example or f"{base}<буква>",
        "candidates": sorted(set(letters)),
    }


def _corpus_scenario(base: str, corpora: list[str]) -> dict:
    present = set()
    for c in corpora:
        m = re.search(r"(\d+)$", c)
        if m:
            present.add(int(m.group(1)))
    example = "к1"
    for n in range(1, 100):
        if n not in present:
            example = f"к{n}"
            break
    return {
        "kind": "corpus",
        "label": "Корпус (CORPUS)",
        "input": f"{base}{example}",
        "candidates": sorted(set(corpora)),
    }


def _fraction_scenario(base: str, fractions: list[str]) -> dict:
    present = set()
    for f in fractions:
        m = re.search(r"/(\d+)$", f)
        if m:
            present.add(int(m.group(1)))
    example = "1"
    for n in range(1, 100):
        if n not in present:
            example = str(n)
            break
    return {
        "kind": "fraction",
        "label": "Дробь (FRACTION)",
        "input": f"{base}/{example}",
        "candidates": sorted(set(fractions)),
    }


def analyze_duplicates(db: LoadedDB) -> dict:
    """Ищет потенциальные дубликаты улиц/домов/ориентиров."""
    # Street: (town_id, district_id, normalized name)
    street_groups: dict[tuple, list[Street]] = {}
    for street in db.streets:
        key = (
            street.district.town_id,
            street.district_id,
            _normalize_name(street.name),
        )
        street_groups.setdefault(key, []).append(street)

    # House: (street_id, number) — есть UNIQUE constraint, но проверим факт.
    house_groups: dict[tuple, list[HouseRecord]] = {}
    for rec in db.houses:
        key = (rec.house.street_id, rec.house.number)
        house_groups.setdefault(key, []).append(rec)

    # Landmark: (street_id, normalized name)
    landmark_groups: dict[tuple, list[LandmarkRecord]] = {}
    for rec in db.landmarks:
        if rec.landmark.street_id is None:
            continue
        key = (rec.landmark.street_id, _normalize_name(rec.landmark.name))
        landmark_groups.setdefault(key, []).append(rec)

    return {
        "streets": {
            key: grp for key, grp in street_groups.items() if len(grp) > 1
        },
        "houses": {key: grp for key, grp in house_groups.items() if len(grp) > 1},
        "landmarks": {
            key: grp for key, grp in landmark_groups.items() if len(grp) > 1
        },
    }


def analyze_anomalies(db: LoadedDB) -> dict:
    """Находит данные, полезные для тестирования. Не считаем аномалией
    легальные NULL, которые ORM разрешает как валидные (например, Landmark
    без дома — это допустимое состояние)."""
    town_without_districts = [t for t in db.towns if not t.districts]
    streets_without_districts = [s for s in db.streets if s.district_id is None]
    district_without_streets = [
        d for t in db.towns for d in t.districts if not d.streets
    ]
    street_without_houses = [s for s in db.streets if not s.houses]
    # Дома без улицы невозможны из-за NOT NULL + FK, но проверяем факт.
    house_without_street = [r for r in db.houses if r.house.street_id is None]
    landmark_without_street = [
        r for r in db.landmarks if r.landmark.street_id is None
    ]
    landmark_without_house = [
        r for r in db.landmarks if r.landmark.house_id is None
    ]
    unparseable = [r for r in db.houses if r.parsed is None]

    return {
        "town_without_districts": town_without_districts,
        "streets_without_districts": streets_without_districts,
        "district_without_streets": district_without_streets,
        "street_without_houses": street_without_houses,
        "house_without_street": house_without_street,
        "landmark_without_street": landmark_without_street,
        "landmark_without_house": landmark_without_house,
        "unparseable": unparseable,
    }


def _type_counts(db: LoadedDB) -> dict[str, int]:
    counts: dict[str, int] = {
        "plain": 0, "letter": 0, "corpus": 0, "fraction": 0, "unparseable": 0,
    }
    for rec in db.houses:
        if rec.parsed is None:
            counts["unparseable"] += 1
        else:
            key = rec.parsed.type.value
            counts[key] = counts.get(key, 0) + 1
    return counts


# ---------------------------------------------------------------------------
# Рендеринг Markdown
# ---------------------------------------------------------------------------


def _esc(value: object) -> str:
    """Экранирует значение для ячейки Markdown-таблицы."""
    text = _fmt(value)
    return text.replace("|", "\\|").replace("\n", " ")


def _fmt(value: object) -> str:
    """Форматирует любое значение (включая None) в строку/«—»."""
    if value is None:
        return "—"
    if isinstance(value, bool):
        return "true" if value else "false"
    return str(value)


def _markdown_table(columns: list[str], rows: list[list[object]]) -> list[str]:
    lines = [
        "| " + " | ".join(columns) + " |",
        "|" + "|".join(["---"] * len(columns)) + "|",
    ]
    for row in rows:
        lines.append("| " + " | ".join(_esc(c) for c in row) + " |")
    return lines


def _database_environment() -> str:
    """Возвращает строку окружения БД БЕЗ логина/пароля/DSN."""
    try:
        host = config_settings.POSTGRES_HOST
        port = config_settings.POSTGRES_PORT
        db = config_settings.POSTGRES_DB
        return f"{host}:{port}/{db}"
    except Exception:
        return "<unknown>"


def render_header(db: LoadedDB, generated_at: datetime) -> list[str]:
    lines = [
        "# Address Database Snapshot",
        "",
        f"- Generated at: {generated_at.isoformat(timespec='seconds')}",
        f"- Database environment: {_database_environment()}",
        f"- Towns: {len(db.towns)}",
        f"- Districts: {len(db.districts)}",
        f"- Streets: {len(db.streets)}",
        f"- Houses: {len(db.houses)}",
        f"- Landmarks: {len(db.landmarks)}",
    ]
    if db.alembic_version:
        lines.append(f"- Schema revision (Alembic): `{db.alembic_version}`")
    lines.extend(
        [
            "",
            "> Снимок формируется автоматически при каждом запуске "
            "``scripts/generate_address_snapshot.py`` и отражает РЕАЛЬНОЕ "
            "состояние БД на момент запуска. Секреты/пароли/DSN не выводятся.",
            "",
            "## Содержимое",
            "",
            "1. ORM Schema — структура адресных моделей (колонки и relationships).",
            "2. Towns / Districts / Streets / Houses / Landmarks — все записи с контекстом.",
            "3. House Number Groups — группировка домов по (улица, base).",
            "4. Potential House Suggestion Cases — фактические suggestion-комбинации.",
            "5. Potential Duplicates / Data Anomalies / Unparseable House Numbers.",
            "6. Statistics — сводные счётчики.",
            "",
        ]
    )
    return lines


def render_statistics(db: LoadedDB) -> list[str]:
    counts = _type_counts(db)
    lines = [
        "# Statistics",
        "",
        "| Entity | Count |",
        "|---|---:|",
        f"| Towns | {len(db.towns)} |",
        f"| Districts | {len(db.districts)} |",
        f"| Streets | {len(db.streets)} |",
        f"| Houses | {len(db.houses)} |",
        f"| Landmarks | {len(db.landmarks)} |",
        f"| Street aliases (synonyms) | {len(db.synonyms)} |",
        f"| House number groups | {len(build_house_number_groups(db))} |",
        "",
        "## House number type breakdown",
        "",
        "| Type | Count |",
        "|---|---:|",
        f"| PLAIN | {counts['plain']} |",
        f"| LETTER | {counts['letter']} |",
        f"| CORPUS | {counts['corpus']} |",
        f"| FRACTION | {counts['fraction']} |",
        f"| Unparseable | {counts['unparseable']} |",
        "",
    ]
    return lines


def render_orm_schema(db: LoadedDB) -> list[str]:
    lines = ["# ORM Schema", ""]
    lines.append("Фактическая структура адресных ORM-моделей проекта "
                 "(интроспекция SQLAlchemy mapper, без выдуманных полей).")
    lines.append("")
    for schema in db.schema:
        lines.append(f"## {schema.name}")
        lines.append("")
        lines.append(f"Таблица: `{schema.table_name}`")
        lines.append("")
        lines.append("### Columns")
        lines.append("")
        col_rows = [
            [
                c.name,
                c.type,
                "yes" if c.nullable else "no",
                "yes" if c.primary_key else "no",
                c.foreign_key if c.foreign_key else "-",
            ]
            for c in schema.columns
        ]
        lines.extend(
            _markdown_table(
                ["Column", "Type", "Nullable", "Primary Key", "Foreign Key"],
                col_rows,
            )
        )
        lines.append("")
        lines.append("### Relationships")
        lines.append("")
        if schema.relationships:
            for rel in schema.relationships:
                tag = "list" if rel.uselist else "single"
                back = f" (back: {rel.back_populates})" if rel.back_populates else ""
                lines.append(f"- {rel.name} → {rel.target} [{tag}]{back}")
        else:
            lines.append("- —")
        lines.append("")
    return lines


def render_towns(db: LoadedDB) -> list[str]:
    lines = ["# Towns", ""]
    sorted_towns = sorted(db.towns, key=lambda t: _normalize_name(t.name))
    for town in sorted_towns:
        districts = town.districts
        streets = [s for d in districts for s in d.streets]
        houses = [h for d in districts for s in d.streets for h in s.houses]
        landmarks = [
            lm for d in districts for s in d.streets for lm in s.landmarks
        ]
        lines.append(f"## Town: {town.name}")
        lines.append("")
        lines.append(f"- ID: {town.id}")
        lines.append(f"- Base price: {town.base_price}")
        lines.append(f"- Districts: {len(districts)}")
        lines.append(f"- Streets: {len(streets)}")
        lines.append(f"- Houses: {len(houses)}")
        lines.append(f"- Landmarks: {len(landmarks)}")
        lines.append("")
    return lines


def render_districts(db: LoadedDB) -> list[str]:
    lines = ["# Districts", ""]
    districts = sorted(
        db.districts,
        key=lambda d: (_normalize_name(d.town.name), _normalize_name(d.name)),
    )
    for district in districts:
        streets = district.streets
        houses = [h for s in streets for h in s.houses]
        landmarks = [lm for s in streets for lm in s.landmarks]
        lines.append(f"## District: {district.name}")
        lines.append("")
        lines.append(f"- ID: {district.id}")
        lines.append(f"- Town: {district.town.name}")
        lines.append(f"- Town ID: {district.town_id}")
        lines.append(f"- Price override: {_fmt(district.price_override)}")
        lines.append(f"- Streets: {len(streets)}")
        lines.append(f"- Houses: {len(houses)}")
        lines.append(f"- Landmarks: {len(landmarks)}")
        lines.append("")
    return lines


def render_streets(db: LoadedDB) -> list[str]:
    lines = ["# Streets", ""]
    streets = sorted(
        db.streets,
        key=lambda s: (
            _normalize_name(s.district.town.name),
            _normalize_name(s.district.name),
            _normalize_name(s.name),
        ),
    )
    for street in streets:
        houses = street.houses
        landmarks = street.landmarks
        lines.append(f"## Street: {street.name}")
        lines.append("")
        lines.append(f"- ID: {street.id}")
        lines.append(f"- Town: {street.district.town.name} (ID: {street.district.town_id})")
        lines.append(f"- District: {street.district.name} (ID: {street.district_id})")
        lines.append(f"- Price override: {_fmt(street.price_override)}")
        lines.append(f"- Houses: {len(houses)}")
        lines.append(f"- Landmarks: {len(landmarks)}")
        if street.synonyms:
            lines.append("")
            lines.append("### Synonyms")
            lines.append("")
            for syn in sorted(street.synonyms, key=lambda x: x.name):
                syn_id = f" (ID: {syn.id})" if syn.id is not None else ""
                lines.append(f"- {syn.name}{syn_id}")
        else:
            lines.append("- Synonyms: —")
        lines.append("")
    return lines


def render_houses(db: LoadedDB) -> list[str]:
    lines = ["# Houses", ""]
    lines.append("Все дома, сгруппированные по иерархии Town → District → Street. "
                 "Для каждого номера показан результат существующего "
                 "``parse_house_number()``: base / type / suffix.")
    lines.append("")
    lines.append(f"Всего домов: **{len(db.houses)}**.")
    lines.append("")

    towns = sorted(db.towns, key=lambda t: _normalize_name(t.name))
    for town in towns:
        lines.append(f"## Town: {town.name} (ID: {town.id})")
        lines.append("")
        districts = sorted(
            town.districts, key=lambda d: _normalize_name(d.name)
        )
        for district in districts:
            lines.append(f"### District: {district.name} (ID: {district.id})")
            lines.append("")
            streets = sorted(
                district.streets, key=lambda s: _normalize_name(s.name)
            )
            for street in streets:
                recs = sorted(
                    (r for r in db.houses if r.house.street_id == street.id),
                    key=_house_sort_key,
                )
                lines.append(f"#### Street: {street.name} (ID: {street.id})")
                lines.append("")
                lines.append(f"Кол-во домов: {len(recs)}")
                lines.append("")
                rows = [
                    [
                        r.house.id,
                        r.house.number,
                        r.parsed.base if r.parsed else "—",
                        r.parsed.type.value.upper() if r.parsed else "UNPARSEABLE",
                        r.parsed.suffix if (r.parsed and r.parsed.suffix is not None) else "-",
                    ]
                    for r in recs
                ]
                lines.extend(
                    _markdown_table(
                        ["House ID", "Number", "Base", "Type", "Suffix"],
                        rows,
                    )
                )
                lines.append("")
    return lines


def render_house_number_groups(db: LoadedDB) -> list[str]:
    lines = ["# House Number Groups", ""]
    lines.append("Дома, сгруппированные по (улица, base). Такие группы — "
                 "источник реальных данных для тестов address resolution.")
    lines.append("")
    groups = build_house_number_groups(db)
    lines.append(f"Всего групп: **{len(groups)}**.")
    lines.append("")
    for group in groups:
        street = group["street"]
        district = group["district"]
        town = group["town"]
        lines.append(f"## {street.name} / base={group['base']}")
        lines.append("")
        lines.append(f"- Town: {town.name} (ID: {town.id})")
        lines.append(f"- District: {district.name} (ID: {district.id})")
        lines.append(f"- Street ID: {street.id}")
        lines.append("")
        for rec in group["records"]:
            lines.append(f"- {rec.house.number}")
        lines.append("")
    return lines


def render_suggestion_cases(db: LoadedDB) -> list[str]:
    lines = ["# Potential House Suggestion Cases", ""]
    lines.append(
        "Фактические группы данных, для которых существующая логика "
        "``AddressSuggestionService`` может сформировать кандидатов. Это НЕ "
        "утверждение о бизнес-валидности suggestion — только наблюдаемые "
        "комбинации данных БД и существующих правил совместимости "
        "(одинаковый base + совместимый тип)."
    )
    lines.append("")
    cases = build_suggestion_cases(db)
    lines.append(f"Всего потенциальных групп: **{len(cases)}**.")
    lines.append("")
    for case in cases:
        street = case["street"]
        town = case["town"]
        district = case["district"]
        lines.append(f"## {street.name} / base={case['base']}")
        lines.append("")
        lines.append(f"- Town: {town.name} (ID: {town.id})")
        lines.append(f"- District: {district.name} (ID: {district.id})")
        lines.append(f"- Street ID: {street.id}")
        available = [r.house.number for r in case["records"]]
        lines.append(f"- Available candidates: {', '.join(available)}")
        lines.append("")
        lines.append("### Potential input patterns")
        lines.append("")
        for scenario in case["scenarios"]:
            cands = ", ".join(scenario["candidates"])
            lines.append(f"- **{scenario['label']}**: `{scenario['input']}` → {cands}")
        lines.append("")
    return lines
def render_landmarks(db: LoadedDB) -> list[str]:
    lines = ["# Landmarks", ""]
    lines.append(
        "Landmark может существовать без улицы/дома (это разрешено ORM: "
        "``street_id`` nullable, ``house_id`` nullable) — в таких случаях "
        "вместо данных ставится «—»."
    )
    lines.append("")
    landmarks = sorted(
        db.landmarks,
        key=lambda r: (
            r.town.name if r.town else "",
            r.district.name if r.district else "",
            r.street.name if r.street else "",
            r.landmark.name or "",
        ),
    )
    lines.append(f"Всего ориентиров: **{len(landmarks)}**.")
    lines.append("")
    for rec in landmarks:
        lm = rec.landmark
        lines.append(f"## Landmark: {lm.name}")
        lines.append("")
        lines.append(f"- ID: {lm.id}")
        if rec.street is not None:
            lines.append(f"- Street: {rec.street.name} (ID: {rec.street.id})")
        else:
            lines.append("- Street: —")
        if rec.house is not None:
            lines.append(f"- House: {rec.house.number} (ID: {rec.house.id})")
        else:
            lines.append("- House: —")
        if rec.district is not None:
            lines.append(
                f"- District: {rec.district.name} (ID: {rec.district.id})"
            )
        else:
            lines.append("- District: —")
        if rec.town is not None:
            lines.append(f"- Town: {rec.town.name} (ID: {rec.town.id})")
        else:
            lines.append("- Town: —")
        lines.append(f"- Description: {_fmt(lm.description)}")
        lines.append("")
    return lines


def render_address_hierarchy(db: LoadedDB) -> list[str]:
    lines = ["# Address Hierarchy", ""]
    lines.append("## Ожидаемая иерархия")
    lines.append("")
    lines.append("```")
    lines.append("Town")
    lines.append(" └── District")
    lines.append("      └── Street")
    lines.append("           └── House")
    lines.append("")
    lines.append("Town")
    lines.append(" └── District")
    lines.append("      └── Street")
    lines.append("           └── Landmark")
    lines.append("```")
    lines.append("")
    lines.append("## Фактическая иерархия (по данным БД)")
    lines.append("")

    towns = sorted(db.towns, key=lambda t: _normalize_name(t.name))
    for town in towns:
        lines.append(f"### Town: {town.name} (ID: {town.id}) — "
                     f"районов: {len(town.districts)}")
        lines.append("")
        districts = sorted(
            town.districts, key=lambda d: _normalize_name(d.name)
        )
        for district in districts:
            n_streets = len(district.streets)
            n_houses = sum(len(s.houses) for s in district.streets)
            n_landmarks = sum(len(s.landmarks) for s in district.streets)
            lines.append(f"└── District: {district.name} (ID: {district.id}) — "
                         f"улиц: {n_streets}, домов: {n_houses}, "
                         f"ориентиров: {n_landmarks}")
            streets = sorted(
                district.streets, key=lambda s: _normalize_name(s.name)
            )
            for street in streets:
                lines.append(f"    └── Street: {street.name} (ID: {street.id}) — "
                             f"домов: {len(street.houses)}, "
                             f"ориентиров: {len(street.landmarks)}")
        lines.append("")
    return lines

def render_duplicates(db: LoadedDB) -> list[str]:
    lines = ["# Potential Duplicates", ""]
    dupes = analyze_duplicates(db)

    # --- Streets ---
    lines.append("## Streets")
    lines.append("")
    lines.append("Ключ: `(town_id, district_id, normalized name)`.")
    lines.append("")
    if dupes["streets"]:
        for key, group in dupes["streets"].items():
            town_id, district_id, norm = key
            lines.append(f"### Дубликаты улиц по ключу (town={town_id}, "
                         f"district={district_id}, norm={norm!r})")
            lines.append("")
            for street in sorted(group, key=lambda s: s.id):
                lines.append(
                    f"- ID {street.id}: {street.name} "
                    f"(район id={street.district_id}, town id={street.district.town_id})"
                )
            lines.append("")
    else:
        lines.append("Не найдено.")
        lines.append("")

    # --- Houses ---
    lines.append("## Houses")
    lines.append("")
    lines.append("Ключ: `(street_id, number)`. Ожидается 0 дубликатов "
                 "(constraint ``uq_house_street_number``).")
    lines.append("")
    if dupes["houses"]:
        for key, group in dupes["houses"].items():
            street_id, number = key
            lines.append(f"### Дубликаты домов по ключу (street={street_id}, "
                         f"number={number!r})")
            lines.append("")
            for rec in group:
                lines.append(f"- House ID {rec.house.id}: {rec.house.number}")
            lines.append("")
    else:
        lines.append("Не найдено.")
        lines.append("")

    # --- Landmarks ---
    lines.append("## Landmarks")
    lines.append("")
    lines.append("Ключ: `(street_id, normalized name)`.")
    lines.append("")
    if dupes["landmarks"]:
        for key, group in dupes["landmarks"].items():
            street_id, norm = key
            lines.append(f"### Дубликаты ориентиров по ключу (street={street_id}, "
                         f"norm={norm!r})")
            lines.append("")
            for rec in group:
                lm = rec.landmark
                lines.append(f"- ID {lm.id}: {lm.name} (house_id={lm.house_id})")
            lines.append("")
    else:
        lines.append("Не найдено.")
        lines.append("")

    return lines

def render_anomalies(db: LoadedDB) -> list[str]:
    lines = ["# Data Anomalies", ""]
    lines.append(
        "Данные, которые могут быть полезны для тестирования. Не считаются "
        "аномалиями состояния, которые ORM-модели разрешают как валидные "
        "(например, Landmark без дома — это нормально, у модели Landmark "
        "колонки street_id и house_id nullable)."
    )
    lines.append("")
    anomalies = analyze_anomalies(db)

    def dump_streets(title: str, streets: list[Street]) -> None:
        lines.append(f"## {title} ({len(streets)})")
        lines.append("")
        if not streets:
            lines.append("Нет.")
        else:
            for s in sorted(streets, key=lambda x: x.id):
                town_id = s.district.town_id if s.district else "—"
                lines.append(
                    f"- ID {s.id}: {s.name} (район id={s.district_id}, "
                    f"town id={town_id})"
                )
        lines.append("")

    def dump_towns(title: str, towns: list[Town]) -> None:
        lines.append(f"## {title} ({len(towns)})")
        lines.append("")
        if not towns:
            lines.append("Нет.")
        else:
            for t in sorted(towns, key=lambda x: x.id):
                lines.append(f"- ID {t.id}: {t.name}")
        lines.append("")

    def dump_districts(title: str, districts: list[District]) -> None:
        lines.append(f"## {title} ({len(districts)})")
        lines.append("")
        if not districts:
            lines.append("Нет.")
        else:
            for d in sorted(districts, key=lambda x: x.id):
                town = d.town.name if d.town else "—"
                lines.append(f"- ID {d.id}: {d.name} (town: {town}, id={d.town_id})")
        lines.append("")

    def dump_landmarks(title: str, records: list[LandmarkRecord]) -> None:
        lines.append(f"## {title} ({len(records)})")
        lines.append("")
        if not records:
            lines.append("Нет.")
        else:
            for r in sorted(records, key=lambda x: x.landmark.id):
                lm = r.landmark
                where = []
                if r.street is not None:
                    where.append(f"street={r.street.name}(id={r.street.id})")
                if r.house is not None:
                    where.append(f"house={r.house.number}(id={r.house.id})")
                lines.append(
                    f"- ID {lm.id}: {lm.name} "
                    f"({'; '.join(where) if where else 'без street/house'})"
                )
        lines.append("")

    dump_towns("Towns without districts", anomalies["town_without_districts"])
    dump_streets("Streets without districts", anomalies["streets_without_districts"])
    dump_districts("Districts without streets", anomalies["district_without_streets"])
    dump_streets("Streets without houses", anomalies["street_without_houses"])

    lines.append(f"## Houses without street ({len(anomalies['house_without_street'])})")
    lines.append("")
    if anomalies["house_without_street"]:
        for r in anomalies["house_without_street"]:
            lines.append(f"- House ID {r.house.id}: {r.house.number}")
    else:
        lines.append("Нет (обязательный NOT NULL FK — невозможны).")
    lines.append("")

    dump_landmarks("Landmarks without street", anomalies["landmark_without_street"])
    dump_landmarks("Landmarks without house", anomalies["landmark_without_house"])

    lines.append(
        f"## Unparseable house numbers ({len(anomalies['unparseable'])})"
    )
    lines.append("")
    lines.append("Подробности в разделе \"# Unparseable House Numbers\".")
    lines.append("")
    return lines


def render_unparseable(db: LoadedDB) -> list[str]:
    lines = ["# Unparseable House Numbers", ""]
    lines.append(
        "Номера домов, которые существующий ``parse_house_number()`` вернул как "
        "``None``. Важно для дальнейшего расширения parser и тестов."
    )
    lines.append("")
    unparseable = sorted(
        (r for r in db.houses if r.parsed is None),
        key=lambda r: (r.town.id, r.district.id, r.street.id, r.house.number),
    )
    lines.append(f"Всего: **{len(unparseable)}**.")
    lines.append("")
    if not unparseable:
        lines.append("Нет нераспознанных номеров домов.")
        lines.append("")
        return lines

    rows = [
        [
            r.house.id,
            r.house.number,
            r.street.name,
            r.district.name,
            r.town.name,
        ]
        for r in unparseable
    ]
    lines.extend(
        _markdown_table(
            ["House ID", "Number", "Street", "District", "Town"],
            rows,
        )
    )
    lines.append("")
    return lines

# ---------------------------------------------------------------------------
# Сборка, запись и CLI
# ---------------------------------------------------------------------------

# Все разделы отчёта. Каждый рендерер возвращает список строк; ошибки в одном
# разделе не прерывают остальные (обрабатывается в render_all).
SECTIONS: list[tuple[str, object]] = [
    ("Statistics", render_statistics),
    ("ORM Schema", render_orm_schema),
    ("Towns", render_towns),
    ("Districts", render_districts),
    ("Streets", render_streets),
    ("Houses", render_houses),
    ("House Number Groups", render_house_number_groups),
    ("Potential House Suggestion Cases", render_suggestion_cases),
    ("Landmarks", render_landmarks),
    ("Address Hierarchy", render_address_hierarchy),
    ("Potential Duplicates", render_duplicates),
    ("Data Anomalies", render_anomalies),
    ("Unparseable House Numbers", render_unparseable),
]


def render_all(db: LoadedDB, generated_at: datetime) -> tuple[list[str], list[str]]:
    """Собирает весь Markdown. Возвращает (строки, список ошибок разделов)."""
    lines: list[str] = []
    errors: list[str] = []

    lines.extend(render_header(db, generated_at))
    lines.append("---")

    for title, renderer in SECTIONS:
        lines.append("")
        try:
            section_lines = renderer(db)
            lines.extend(section_lines)
        except Exception as exc:  # не скрываем ошибку, продолжаем остальные разделы
            err = f"Ошибка при формировании раздела «{title}»: {exc!r}"
            errors.append(err)
            print(f"ERROR: {err}", file=sys.stderr)
            lines.append(f"# {title}")
            lines.append("")
            lines.append(f"> ⚠️ {err}")
            lines.append("")
        lines.append("---")

    return lines, errors


def write_report(
    lines: list[str], docs_dir: Path, generated_at: datetime
) -> list[Path]:
    """Пишет timestamp-снимок и «latest»-снимок. Возвращает созданные пути."""
    docs_dir.mkdir(parents=True, exist_ok=True)
    stamp = generated_at.strftime("%Y-%m-%d_%H-%M-%S")
    timestamped = docs_dir / f"address_database_snapshot_{stamp}.md"
    latest = docs_dir / "address_database_snapshot_latest.md"

    content = "\n".join(lines)
    timestamped.write_text(content, encoding="utf-8")
    latest.write_text(content, encoding="utf-8")
    return [timestamped, latest]


def main() -> int:
    if _IMPORT_ERROR is not None:
        print(
            f"ERROR: не удалось инициализировать приложение "
            f"(проверьте .env и зависимости):\n  {_IMPORT_ERROR}",
            file=sys.stderr,
        )
        return 2

    parser = argparse.ArgumentParser(
        description=(
            "Генерирует актуальный Markdown-снимок адресных данных БД "
            "в docs/ (read-only, без изменения БД)."
        )
    )
    parser.add_argument(
        "--docs-dir",
        type=Path,
        default=DEFAULT_DOCS_DIR,
        help="Каталог для отчёта (по умолчанию docs/)",
    )
    args = parser.parse_args()

    generated_at = datetime.now().astimezone()

    print("Загружаю адресные данные из БД...")
    try:
        db = asyncio.run(load_database())
    except Exception as exc:
        print(
            f"ERROR: не удалось подключиться/прочитать БД "
            f"(пустой отчёт НЕ создан):\n  {exc!r}",
            file=sys.stderr,
        )
        return 1

    lines, errors = render_all(db, generated_at)

    try:
        written = write_report(lines, args.docs_dir, generated_at)
    except OSError as exc:
        print(f"ERROR: не удалось записать отчёт: {exc!r}", file=sys.stderr)
        return 1

    for path in written:
        print(f"OK: отчёт записан в {path.relative_to(ROOT)}")

    print(
        "Снимок содержит: "
        f"towns={len(db.towns)}, districts={len(db.districts)}, "
        f"streets={len(db.streets)}, houses={len(db.houses)}, "
        f"landmarks={len(db.landmarks)}, "
        f"synonyms={len(db.synonyms)}"
    )

    if errors:
        print("Завершено с ошибками в отдельных разделах (см. выше).", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

