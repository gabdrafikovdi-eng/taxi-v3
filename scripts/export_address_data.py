"""
Полная выгрузка адресных данных из БД в Markdown-файл.

Что выгружается (всё, что связано с адресами):
  - справочник адресов: towns, districts, streets, houses,
    street_synonyms, landmarks;
  - адресные поля заказов: orders, waypoints (подача, назначение, остановки);
  - call_sessions — как справочная информация для заказов (FK).

Результат записывается в docs/db_address_data.md.

Запуск из корня проекта:
    .venv/bin/python scripts/export_address_data.py
"""

from __future__ import annotations

import asyncio
import sys
from datetime import date, datetime
from pathlib import Path
from uuid import UUID

from sqlalchemy import text

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from app.core.database import async_session_factory  # noqa: E402

OUT_FILE = ROOT / "docs" / "db_address_data.md"

# Таблицы-справочники адресов + таблицы с адресными полями заказов.
# Порядок: ссылочные таблицы идут после тех, на которые ссылаются.
REFERENCE_TABLES = (
    ("towns", "Города"),
    ("districts", "Районы"),
    ("streets", "Улицы"),
    ("houses", "Дома"),
    ("street_synonyms", "Синонимы улиц"),
    ("landmarks", "Ориентиры"),
)

ORDER_TABLES = (
    ("orders", "Заказы (адресные поля)"),
    ("waypoints", "Промежуточные остановки заказов"),
    ("call_sessions", "Сессии звонков (справочно для заказов)"),
)
def _fmt(value: object) -> str:
    """Преобразует значение из БД в строку для Markdown-ячейки."""
    if value is None:
        return "—"
    if isinstance(value, (datetime, date)):
        if isinstance(value, datetime):
            return value.isoformat(timespec="seconds")
        return value.isoformat()
    if isinstance(value, UUID):
        return str(value)
    if isinstance(value, bool):
        return "true" if value else "false"
    return str(value)


def _esc(value: str) -> str:
    """Экранирует ячейку Markdown-таблицы."""
    return value.replace("|", "\\|").replace("\n", " ")


def markdown_table(columns: list[str], rows: list[dict]) -> str:
    header = "| " + " | ".join(_esc(c) for c in columns) + " |"
    sep = "|" + "|".join(["---"] * len(columns)) + "|"
    body = [
        "| " + " | ".join(_esc(_fmt(r.get(c))) for c in columns) + " |"
        for r in rows
    ]
    return "\n".join([header, sep, *body]) if rows else header + "\n" + sep


async def fetch_table(session, table: str) -> tuple[list[str], list[dict]]:
    """Возвращает (колонки, строки) для таблицы."""
    result = await session.execute(text(f"SELECT * FROM {table} ORDER BY 1"))
    keys = list(result.keys())
    rows = [dict(zip(keys, row)) for row in result.all()]
    return keys, rows






def build_reference_section(session_data: dict) -> list[str]:
    """Секция со справочником адресов (все записи)."""
    lines: list[str] = []

    lines.append("## 1. Справочник адресов")
    lines.append("")

    # --- Сводка по количеству записей ---
    lines.append("### Сводка")
    lines.append("")
    lines.append("| Таблица | Описание | Записей |")
    lines.append("|---|---|---:|")
    summaries = {
        "towns": "Города",
        "districts": "Районы",
        "streets": "Улицы",
        "houses": "Дома",
        "street_synonyms": "Синонимы улиц",
        "landmarks": "Ориентиры",
    }
    for tbl, desc in summaries.items():
        lines.append(f"| `{tbl}` | {desc} | {len(session_data[tbl][1])} |")
    lines.append("")

    districts = {d["id"]: d["name"] for d in session_data["districts"][1]}

    # --- Города ---
    lines.append("### 1.1 Города — `towns`")
    lines.append("")
    cols, rows = session_data["towns"]
    lines.append(markdown_table(cols, rows))
    lines.append("")

    # --- Районы ---
    lines.append("### 1.2 Районы — `districts`")
    lines.append("")
    cols, rows = session_data["districts"]
    display_cols = ["id", "name", "town_id", "price_override", "created_at", "updated_at"]
    lines.append(markdown_table(display_cols, rows))
    lines.append("")

    # --- Улицы (сгруппированы по районам) ---
    lines.append("### 1.3 Улицы — `streets`")
    lines.append("")
    cols, rows = session_data["streets"]
    streets_by_district: dict[int, list[dict]] = {}
    for r in rows:
        streets_by_district.setdefault(r["district_id"], []).append(r)
    for district_id in sorted(streets_by_district, key=lambda k: districts.get(k, "")):
        dname = districts.get(district_id, f"район id={district_id}")
        srows = sorted(streets_by_district[district_id], key=lambda r: r["name"])
        lines.append(f"**Район: {dname}** (улиц: {len(srows)})")
        lines.append("")
        lines.append(markdown_table(cols, srows))
        lines.append("")

    # --- Дома (сгруппированы по улицам) ---
    lines.append("### 1.4 Дома — `houses`")
    lines.append("")
    cols, rows = session_data["houses"]
    houses_by_street: dict[int, list[dict]] = {}
    for r in rows:
        houses_by_street.setdefault(r["street_id"], []).append(r)
    total = len(rows)
    lines.append(f"Всего домов: **{total}**.")
    lines.append("")
    # Карта street_id -> (улица, район)
    street_meta = {}
    for r in session_data["streets"][1]:
        street_meta[r["id"]] = (r["name"], districts.get(r["district_id"], "—"))
    for street_id in sorted(houses_by_street, key=lambda k: street_meta.get(k, ("", ""))[0]):
        street, district = street_meta.get(street_id, (f"улица id={street_id}", "—"))
        hrows = sorted(houses_by_street[street_id], key=lambda r: (r["number"] or ""))
        lines.append(
            f"**Улица: {street}** (id={street_id}, район: {district}, домов: {len(hrows)})"
        )
        lines.append("")
        lines.append(
            markdown_table(
                ["id", "number", "price_override", "created_at", "updated_at"], hrows
            )
        )
        lines.append("")

    # --- Синонимы улиц ---
    lines.append("### 1.5 Синонимы улиц — `street_synonyms`")
    lines.append("")
    cols, rows = session_data["street_synonyms"]
    if rows:
        lines.append(markdown_table(cols, rows))
    else:
        lines.append("Таблица пуста (записей нет).")
    lines.append("")

    # --- Ориентиры ---
    lines.append("### 1.6 Ориентиры — `landmarks`")
    lines.append("")
    cols, rows = session_data["landmarks"]
    if rows:
        lines.append(markdown_table(cols, rows))
    else:
        lines.append("Таблица пуста (записей нет).")
    lines.append("")

    return lines

def build_orders_section(session_data: dict) -> list[str]:
    """Секция с заказами, промежуточными остановками и сессиями."""
    lines: list[str] = []

    lines.append("## 2. Заказы и их адреса")
    lines.append("")

    # --- Заказы ---
    lines.append("### 2.1 Заказы — `orders`")
    lines.append("")
    _, rows = session_data["orders"]
    if not rows:
        lines.append("Таблица пуста (заказов нет).")
    else:
        address_cols = [
            "id", "call_session_id",
            "pickup_town", "pickup_town_id",
            "pickup_district", "pickup_district_id",
            "pickup_street", "pickup_street_id",
            "pickup_house", "pickup_house_id",
            "pickup_landmark", "pickup_landmark_id",
            "destination_town", "destination_town_id",
            "destination_district", "destination_district_id",
            "destination_street", "destination_street_id",
            "destination_house", "destination_house_id",
            "destination_landmark", "destination_landmark_id",
            "passenger_name", "comment", "price", "state",
            "created_at", "updated_at",
        ]
        for o in rows:
            lines.append(f"**Заказ `{o['id']}`** — статус `{o['state']}`")
            lines.append("")
            lines.append(markdown_table(address_cols, [o]))
            lines.append("")

    # --- Промежуточные остановки ---
    lines.append("### 2.2 Промежуточные остановки — `waypoints`")
    lines.append("")
    cols, rows = session_data["waypoints"]
    if rows:
        lines.append(markdown_table(cols, rows))
    else:
        lines.append("Таблица пуста (остановок нет).")
    lines.append("")

    # --- Сессии звонков ---
    lines.append("### 2.3 Сессии звонков — `call_sessions`")
    lines.append("")
    cols, rows = session_data["call_sessions"]
    if rows:
        lines.append(markdown_table(cols, rows))
    else:
        lines.append("Таблица пуста (сессий нет).")
    lines.append("")

    return lines


async def main() -> None:
    async with async_session_factory() as session:
        # Версия схемы (alembic)
        ver = await session.execute(text("SELECT version_num FROM alembic_version"))
        alembic_version = ver.scalar()

        session_data: dict = {}
        for tbl, _ in [*REFERENCE_TABLES, *ORDER_TABLES]:
            session_data[tbl] = await fetch_table(session, tbl)

    lines: list[str] = []
    lines.append("# Выгрузка адресных данных из БД проекта `taxi-v3`")
    lines.append("")
    stamp = datetime.now().astimezone().isoformat(timespec="seconds")
    lines.append(f"> Дата снимка: **{stamp}**")
    lines.append("> Источник: PostgreSQL (`taxi-db`, localhost:5432).")
    lines.append(f"> Ревизия схемы (Alembic): `{alembic_version}`")
    lines.append("> Назначение: полная выгрузка всех данных БД, связанных с адресами, —")
    lines.append("> справочник адресов (город/районы/улицы/дома/синонимы/ориентиры) и")
    lines.append("> адресные поля заказов (подача, назначение, промежуточные остановки).")
    lines.append("")
    lines.append("## Содержимое файла")
    lines.append("")
    lines.append("1. Справочник адресов (все записи): города, районы, улицы, дома, синонимы улиц, ориентиры.")
    lines.append("2. Заказы и их адреса: `orders`, `waypoints`, а также `call_sessions` (FK для заказов).")
    lines.append("")
    lines.append("---")
    lines.append("")

    lines += build_reference_section(session_data)
    lines.append("---")
    lines.append("")
    lines += build_orders_section(session_data)

    OUT_FILE.write_text("\n".join(lines), encoding="utf-8")
    print(f"OK: выгрузка записана в {OUT_FILE.relative_to(ROOT)}")


if __name__ == "__main__":
    asyncio.run(main())
