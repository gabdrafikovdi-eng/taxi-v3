"""Консольная утилита точечной проверки адресной воронки поиска (AddressService).

Позволяет вводить адрес (улицу, район, дом, ориентир, город) и смотреть, как
реальная воронка (exact -> synonym -> fuzzy -> house -> landmark) его резолвит,
с диагностикой по каждому этапу.

Примеры использования
----------------------
Одиночный случай (флаги):

    python scripts/address_debug.py --street "Ленина"
    python scripts/address_debug.py --street "Ленина" --district "Северный"
    python scripts/address_debug.py --street "Шаймуратова" --district "Восточный-1"
    python scripts/address_debug.py --street "Гагарина" --landmark "больница"
    python scripts/address_debug.py --street "   лЕнИнА  " --district "  цЕнТр "

Интерактивный режим (ввод построчно, пустая строка — выход):

    python scripts/address_debug.py -i

    В интерактивном режиме строка разбирается по запятым в порядке:
    street, district, landmark, house, town
    Например:  Ленина, Северный
               Шаймуратова, Восточный-1
               Гагарина,,больница
    Спецкоманды:  :probe <слово>   — fuzzy-пробник по всем улицам
                  :q / :quit / Ctrl+D — выход

Fuzzy-пробник (топ похожих улиц с порогом похожести):

    python scripts/address_debug.py --probe "Шахмуратов"

Скрипт ТОЛЬКО читает данные из существующей БД (taxi-db) и ничего в ней
не создаёт, не обновляет и не удаляет (ни таблиц, ни расширений, ни записей).
Ожидается, что данные (город, районы, улицы, дома, ориентиры) уже заведены
вручную или через seed-скрипт (например, ``scripts/seed_askarovo.py``).
Если нужной записи нет в БД — будет показан понятный diagnostic/error,
автоматическое создание данных не выполняется.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
from pathlib import Path

# Позволяет импортировать app-модули при запуске как простого скрипта.
ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

# Patch Pydantic v2 "non-annotated attribute" error for AddressConfig.street_prefixes
# The AddressConfig class in app/core/config.py defines street_prefixes without a type annotation,
# which Pydantic v2 requires. We patch the config module in-memory before importing,
# so all subsequent imports of app.core.config get the fixed version.
import sys
import tempfile, os
from pathlib import Path

config_path = ROOT / 'app' / 'core' / 'config.py'
with open(config_path, 'r', encoding='utf-8') as f:
    content = f.read()
# Add type annotation to street_prefixes to satisfy Pydantic v2 field requirements
content = content.replace(
    '    street_prefixes = (',
    '    street_prefixes: tuple[str, str, str, str, str, str] = (',
    1,
)
namespace = {}
exec(content, namespace)

# Replace the app.core.config module in sys.modules with the patched version
# so all subsequent imports (e.g. from app.core.database) get the fixed AddressConfig.
patched_config = sys.modules.get('app.core.config')
patched_module = type(sys)('app.core.config')
patched_module.__dict__.update(namespace)
sys.modules['app.core.config'] = patched_module

address_config = namespace['address_config']

from sqlalchemy import func, select  # noqa: E402
from pydantic import ValidationError  # noqa: E402
from app.core.database import async_session_factory  # noqa: E402
from app.models.address import District, Street, Town  # noqa: E402
from app.repositories.address_repo import AddressRepository  # noqa: E402
from app.schemas.address import AddressInput, AddressStatus  # noqa: E402
from app.services.address_service import AddressService  # noqa: E402

# Минимальные ANSI-цвета для статусов (только если вывод в терминал).
_RESET = "\033[0m"
_STATUS_COLOR = {
    AddressStatus.RESOLVED: "\033[32m",   # green
    AddressStatus.AMBIGUOUS: "\033[33m",  # yellow
    AddressStatus.NOT_FOUND: "\033[31m",  # red
}
_GRAY = "\033[90m"


def _use_color() -> bool:
    return sys.stdout.isatty()


def _paint(text: str, color: str) -> str:
    return f"{color}{text}{_RESET}" if _use_color() else text


def _status_str(status: AddressStatus) -> str:
    return _paint(status.value, _STATUS_COLOR.get(status, ""))


# --------------------------------------------------------------------------
# Диагностика воронки
# --------------------------------------------------------------------------


async def _print_funnel_debug(
    session, repo: AddressRepository, town: Town, street_name: str | None
) -> None:
    """Выводит, что находит каждый этап воронки (exact/synonym/fuzzy)."""
    if not street_name:
        return

    district_ids = await repo.get_district_ids_by_town(town.id)
    threshold = address_config.fuzzy_threshold

    print(f"\n{_GRAY}— Диагностика воронки (порог fuzzy = {threshold}) —{_RESET}")

    exact = await repo.find_streets_exact(district_ids, street_name)
    print(f"[EXACT] {len(exact)} hit(s)")
    for s in exact:
        print(f"    {_GRAY}#{s.id}{_RESET} {s.name!r} -> район {s.district.name}")

    syn = await repo.find_streets_by_synonyms(district_ids, street_name)
    print(f"[SYNONYM] {len(syn)} hit(s)")
    for s in syn:
        print(f"    {_GRAY}#{s.id}{_RESET} {s.name!r} -> район {s.district.name}")

    rows = (
        await session.execute(
            select(
                Street.id,
                Street.name,
                District.name.label("district_name"),
                func.similarity(Street.name, street_name).label("sim"),
            )
            .join(District, Street.district_id == District.id)
            .where(
                Street.district_id.in_(district_ids),
                func.similarity(Street.name, street_name) >= threshold,
            )
            .order_by(func.similarity(Street.name, street_name).desc())
            .limit(address_config.max_candidates)
        )
    ).all()
    print(f"[FUZZY] {len(rows)} hit(s)")
    for row in rows:
        print(
            f"    {_GRAY}#{row.id}{_RESET} {row.name!r} -> район {row.district_name} "
            f"({_paint(f'sim={row.sim:.3f}', _GRAY)})"
        )


def _print_result(result) -> None:
    """Красиво выводит результат работы сервиса."""
    print(f"\n{'=' * 60}")
    status = _status_str(result.status)
    reason = f"  (reason={result.reason})" if result.reason else ""
    print(f"STATUS: {status}{reason}")
    if not result.candidates:
        print("  кандидатов нет")
    for i, c in enumerate(result.candidates, start=1):
        diff = f"  [diff: {c.diff_feature}]" if c.diff_feature else ""
        house = f", д {c.house_number}" if c.house_number else ""
        landmark = f", ориентир '{c.landmark_name}'" if c.landmark_name else ""
        line = (
            f"  {i}. score={c.score:.2f} | "
            f"ул. {c.street_name}{house}{landmark}, р-н {c.district_name} "
            f"(г. {c.town_name}){diff}"
        )
        print(line)
        ids = (
            f"     fulladdress: {c.fulladdress}  "
            f"{_GRAY}(ids: town={c.town_id}, dist={c.district_id}, "
            f"str={c.street_id}, house={c.house_id}, lm={c.landmark_id}){_RESET}"
        )
        print(ids)
    print("=" * 60)


def _dump_model(model, title: str) -> None:
    """Печатает полное содержимое Pydantic-модели в JSON-виде (все поля)."""
    print(f"\n{_GRAY}— {title} —{_RESET}")
    print(json.dumps(model.model_dump(mode="json"), ensure_ascii=False, indent=2))


async def _run_case(
    session, repo: AddressRepository, service: AddressService, addr_input: AddressInput
) -> None:
    town_name = addr_input.town or address_config.default_town_name
    town = await repo.get_town_by_name(town_name)
    if town is None:
        print(f"\nгород '{town_name}' не найден в БД (reason=town_not_found)")
        return

    # Какой AddressInput реально ушёл в сервис (после Pydantic-нормализации).
    _dump_model(addr_input, "AddressInput")

    await _print_funnel_debug(session, repo, town, addr_input.street)

    result = await service.resolve_address(addr_input)
    _print_result(result)

    # Полный ответ сервиса: все поля статуса, reason и каждого кандидата.
    _dump_model(result, "AddressMatchResult (полные данные ответа)")


async def _probe(session, word: str) -> None:
    """Выводит топ-N улиц по похожести на слово (не зависит от района)."""
    threshold = address_config.fuzzy_threshold
    town = await session.scalar(
        select(Town).where(func.lower(Town.name) == address_config.default_town_name)
    )
    district_ids = []
    if town is not None:
        district_ids = list(
            (await session.execute(select(District.id).where(District.town_id == town.id))).scalars()
        )

    rows = (
        await session.execute(
            select(
                Street.name,
                District.name.label("district_name"),
                func.similarity(Street.name, word).label("sim"),
            )
            .join(District, Street.district_id == District.id)
            .where(
                Street.district_id.in_(district_ids),
                func.similarity(Street.name, word) >= threshold,
            )
            .order_by(func.similarity(Street.name, word).desc())
            .limit(address_config.max_candidates)
        )
    ).all()

    print(f"\nFuzzy-пробник для '{word}' (порог {threshold}, топ-{address_config.max_candidates}):")
    if not rows:
        print("  ничего не найдено")
    for r in rows:
        print(f"  {r.name!r} ({r.district_name})  sim={r.sim:.3f}")



# --------------------------------------------------------------------------
# Интерактивный режим
# --------------------------------------------------------------------------


async def _interactive(
    session, repo: AddressRepository, service: AddressService
) -> None:
    print("Интерактивный режим — поэтапный ввод полей AddressInput.")
    print("Для пропуска поля просто нажмите Enter (будет считаться None).")
    print("Команды:  :probe <слово>  — fuzzy‑пробник")
    print("          :q / :quit      — выход")
    print("          пустая строка в первом поле — выход\n")

    while True:
        try:
            # Поэтапный ввод
            street = input("street> ").strip() or None
            if street is None:
                print("До свидания!")
                return
            district = input("district> ").strip() or None
            landmark = input("landmark> ").strip() or None
            house = input("house> ").strip() or None
            town = input("town> ").strip() or None
        except (EOFError, KeyboardInterrupt):
            print("\nДо свидания!")
            return

        # Проверка специальных команд в любом поле (чтобы выйти)
        if any(
            isinstance(v, str) and v.lower() in (":q", ":quit")
            for v in (street, district, landmark, house, town)
        ):
            print("До свидания!")
            return
        if any(
            isinstance(v, str) and v.startswith(":probe")
            for v in (street, district, landmark, house, town)
        ):
            # Находим первое поле, содержащее команду :probe
            for v in (street, district, landmark, house, town):
                if isinstance(v, str) and v.startswith(":probe"):
                    await _probe(session, v[len(":probe"):].strip())
                    break
            print()
            continue

        # Сборка AddressInput
        addr = AddressInput(
            street=street,
            district=district,
            landmark=landmark,
            house=house,
            town=town,
        )
        await _run_case(session, repo, service, addr)
        print()


# --------------------------------------------------------------------------
# CLI
# --------------------------------------------------------------------------


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Точечная проверка адресной воронки поиска (AddressService).",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument("--street", help="улица (можно с префиксом 'ул.')")
    parser.add_argument("--district", help="район")
    parser.add_argument("--landmark", help="ориентир")
    parser.add_argument("--house", help="номер дома")
    parser.add_argument(
        "--town", help=f"город (по умолчанию: {address_config.default_town_name})"
    )
    parser.add_argument(
        "-i", "--interactive", action="store_true", help="интерактивный режим ввода"
    )
    parser.add_argument(
        "--probe", metavar="WORD", help="fuzzy-пробник: топ похожих улиц по слову"
    )
    parser.add_argument(
        "--json",
        dest="json_input",
        metavar="JSON",
        help=(
            "AddressInput в виде JSON-строки, например "
            '--json \'{"street": "Ленина", "district": "Северный"}\''
        ),
    )
    return parser.parse_args(argv)


async def _main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)

    async with async_session_factory() as session:
        repo = AddressRepository(session)
        service = AddressService(repo)

        if args.probe:
            await _probe(session, args.probe)
            return 0

        # Oдин-в-один ввод AddressInput в виде JSON.
        if args.json_input:
            try:
                payload = json.loads(args.json_input)
                addr = AddressInput(**payload)
            except (json.JSONDecodeError, ValidationError) as exc:
                print(f"ошибка разбора AddressInput: {exc}")
                return 2
            await _run_case(session, repo, service, addr)
            return 0

        fields = {
            "street": args.street,
            "district": args.district,
            "landmark": args.landmark,
            "house": args.house,
            "town": args.town,
        }

        # Флаг -i без полей -> интерактивный режим.
        if args.interactive and not any(fields.values()):
            await _interactive(session, repo, service)
            return 0

        # Переданы поля -> одиночный случай.
        if any(fields.values()):
            await _run_case(
                session, repo, service, AddressInput(**fields)
            )
            return 0

        # Ничего не передано -> интерактивный режим.
        await _interactive(session, repo, service)
        return 0


def main(argv: list[str] | None = None) -> int:
    try:
        return asyncio.run(_main(argv))
    except KeyboardInterrupt:
        print("\nПрервано пользователем.")
        return 130


if __name__ == "__main__":
    raise SystemExit(main())

