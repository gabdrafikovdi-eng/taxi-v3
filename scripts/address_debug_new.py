"""Консольная утилита проверки НОВОГО адресного сервиса (app.services.address).

Позволяет вводить адрес (улицу, дом, район, ориентир, город) и смотреть, как
новый `AddressService` (ContextResolver -> StreetResolver -> HouseResolver /
LandmarkResolver -> AddressSuggestionService) его резолвит, с диагностикой по
каждому этапу.

Отличие от старого scripts/address_debug.py:
    - собирает новый `app/services/address/address_service.py:AddressService`
      со всеми резолверами и `AddressSuggestionService`;
    - обязательное бизнес-правило нового сервиса: street + house ИЛИ landmark;
    - показывает нормализацию входа (включая срезку "ул."/"улица"/"пер."/...);
    - показывает подбор похожих номеров домов (suggestions), когда точный дом
      не найден;
    - проверяет наличие расширения pg_trgm (нужно для fuzzy-этапа).

Примеры использования
---------------------
Одиночный случай (флаги):

    python scripts/address_debug_new.py --street "Коммунистическая" --house "1"
    python scripts/address_debug_new.py --street "Гагарина" --house "2а" --district "Центр"
    python scripts/address_debug_new.py --street "   ул. лЕнИнА  " --house "33" --district "Восточный-1"
    python scripts/address_debug_new.py --landmark "больница"
    python scripts/address_debug_new.py --street "Коммунистическая" --house "1" --town "аскарово"

Интерактивный режим:

    python scripts/address_debug_new.py -i

Fuzzy-пробник (топ похожих улиц по слову):

    python scripts/address_debug_new.py --probe "Шахмуратов"

Скрипт ТОЛЬКО читает данные из существующей БД (taxi-db) и ничего в ней
не создаёт, не обновляет и не удаляет.
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

from sqlalchemy import func, select  # noqa: E402
from sqlalchemy.exc import ProgrammingError  # noqa: E402
from pydantic import ValidationError  # noqa: E402

from app.core.config import address_config  # noqa: E402
from app.core.database import async_session_factory  # noqa: E402
from app.models.address import District, Street, Town  # noqa: E402
from app.repositories.address_repo import AddressRepository  # noqa: E402
from app.schemas.address import AddressInput, AddressStatus  # noqa: E402
from app.services.address.address_service import AddressService  # noqa: E402
from app.services.address.context_resolver import ContextResolver  # noqa: E402
from app.services.address.house_resolver import HouseResolver  # noqa: E402
from app.services.address.landmark_resolver import LandmarkResolver  # noqa: E402
from app.services.address.street_resolver import StreetResolver  # noqa: E402
from app.services.address.suggestion_service import AddressSuggestionService  # noqa: E402

# Минимальные ANSI-цвета для статусов (только если вывод в терминал).
_RESET = "\033[0m"
_STATUS_COLOR = {
    AddressStatus.RESOLVED: "\033[32m",   # green
    AddressStatus.AMBIGUOUS: "\033[33m",  # yellow
    AddressStatus.NOT_FOUND: "\033[31m",  # red
    AddressStatus.INCOMPLETE: "\033[36m",  # cyan
}
_GRAY = "\033[90m"


def _use_color() -> bool:
    return sys.stdout.isatty()


def _paint(text: str, color: str) -> str:
    return f"{color}{text}{_RESET}" if _use_color() else text


def _status_str(status: AddressStatus) -> str:
    return _paint(status.value, _STATUS_COLOR.get(status, ""))


def _build_service(repo: AddressRepository) -> AddressService:
    """Собирает НОВЫЙ AddressService из резолверов и suggestion-сервиса."""
    return AddressService(
        address_repo=repo,
        context_resolver=ContextResolver(
            address_repo=repo,
            default_town_name=address_config.default_town_name,
        ),
        street_resolver=StreetResolver(
            address_repo=repo,
            fuzzy_threshold=address_config.fuzzy_threshold,
            max_candidate=address_config.max_candidates,
        ),
        house_resolver=HouseResolver(address_repo=repo),
        landmark_resolver=LandmarkResolver(address_repo=repo),
        address_suggestion_service=AddressSuggestionService(address_repo=repo),
    )


# --------------------------------------------------------------------------
# Диагностика этапов
# --------------------------------------------------------------------------


async def _check_pg_trgm(session) -> bool:
    """Проверяет наличие расширения pg_trgm (нужно для fuzzy-этапа)."""
    try:
        await session.execute(select(func.similarity("а", "а")))
        return True
    except ProgrammingError as exc:
        print(
            f"{_GRAY}[PG_TRGM] расширение pg_trgm недоступно: "
            f"{exc.orig if getattr(exc, 'orig', None) else exc}{_RESET}"
        )
        return False


async def _print_context_diag(
    service: AddressService, addr: AddressInput
):
    """Показывает, что вернул ContextResolver для города/района."""
    town_name = addr.town or address_config.default_town_name
    print(
        f"\n{_GRAY}— Этап 1: ContextResolver "
        f"(town={town_name!r}, district={addr.district!r}) —{_RESET}"
    )
    context = await service.context_resolver.resolve(
        town_name=addr.town,
        district_name=addr.district,
    )
    if context is None:
        print(
            f"  {_paint('context = None', _STATUS_COLOR[AddressStatus.NOT_FOUND])} "
            "-> город или район не найден"
        )
        return None
    print(f"  town_id = {context.town_id}")
    print(f"  district_ids = {context.district_ids}")
    return context


async def _print_street_diag(
    service: AddressService, district_ids, street_name: str
):
    """Показывает, что вернул StreetResolver (exact/synonym/fuzzy)."""
    print(
        f"\n{_GRAY}— Этап 2: StreetResolver "
        f"(name={street_name!r}, порог fuzzy="
        f"{address_config.fuzzy_threshold}) —{_RESET}"
    )
    try:
        matches = await service.street_resolver.resolve(
            district_ids=district_ids, name=street_name
        )
    except ProgrammingError as exc:
        print(
            "  "
            + _paint(
                "fuzzy-этап недоступен (pg_trgm): ",
                _STATUS_COLOR[AddressStatus.NOT_FOUND],
            )
            + f"{exc.orig if getattr(exc, 'orig', None) else exc}"
        )
        return []
    if not matches:
        print("  улиц не найдено")
        return []
    for m in matches:
        street = m.street
        print(
            f"  [{m.match_type.value.upper():<7}] "
            f"{_GRAY}#{street.id}{_RESET} {street.name!r} "
            f"-> р-н {street.district.name} (score={m.score:.3f})"
        )
    return matches


async def _print_house_diag(
    service: AddressService, streets, house_number: str
) -> None:
    """Показывает, какие дома нашёл HouseResolver по найденным улицам."""
    print(
        f"\n{_GRAY}— Этап 3: HouseResolver (house={house_number!r}) —{_RESET}"
    )
    candidates = await service.house_resolver.resolve(
        streets=streets, house_number=house_number
    )
    if not candidates:
        print("  дом не найден ни на одной из улиц")
        return
    for c in candidates:
        print(
            f"  {_GRAY}#{c.house_id}{_RESET} ул. {c.street_name}, "
            f"д. {c.house_number} -> р-н {c.district_name} "
            f"(score={c.score:.3f})"
        )


async def _print_suggestion_diag(
    service: AddressService, streets, house_number: str
) -> None:
    """Показывает, какие похожие дома подобрал AddressSuggestionService.

    Suggestions считаются только при одной найденной улице (иначе непонятно,
    для какой из неоднозначных улиц искать похожие номера домов).
    """
    print(
        f"\n{_GRAY}— Этап 3b: AddressSuggestionService "
        f"(house={house_number!r}) —{_RESET}"
    )
    if len(streets) != 1:
        print(
            f"  пропущено: найдено улиц {len(streets)} "
            "(для подбора похожих домов нужна ровно одна)"
        )
        return
    suggestions = await service.address_suggestion_service.suggest_house(
        street_id=streets[0].street.id,
        house_number=house_number,
        limit=3,
    )
    if not suggestions:
        print("  похожих домов не найдено")
        return
    for c in suggestions:
        print(
            f"  {_GRAY}#{c.house_id}{_RESET} ул. {c.street_name}, "
            f"д. {c.house_number} -> р-н {c.district_name} "
            "(suggestion, НЕ resolved)"
        )


async def _print_landmark_diag(
    service: AddressService, district_ids, landmark_name: str
) -> None:
    """Показывает, что вернул LandmarkResolver."""
    print(
        f"\n{_GRAY}— Этап (landmark): LandmarkResolver "
        f"(name={landmark_name!r}) —{_RESET}"
    )
    candidates = await service.landmark_resolver.resolve(
        district_ids=district_ids, name=landmark_name
    )
    if not candidates:
        print("  ориентиров не найдено")
        return
    for c in candidates:
        print(
            f"  {_GRAY}#{c.landmark_id}{_RESET} {c.landmark_name!r} "
            f"-> ул. {c.street_name}, д. {c.house_number or '-'} "
            f"(р-н {c.district_name})"
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
        landmark = (
            f", ориентир '{c.landmark_name}'" if c.landmark_name else ""
        )
        line = (
            f"  {i}. ул. {c.street_name}{house}{landmark}"
            f" -> р-н {c.district_name}{diff}"
        )
        print(line)
    if result.suggestions:
        print()
        print(f"  {_GRAY}— suggestions (похожие номера домов, НЕ resolved) —{_RESET}")
        for i, c in enumerate(result.suggestions, start=1):
            print(
                f"  {i}. ул. {c.street_name}, д. {c.house_number}"
                f" -> р-н {c.district_name}"
            )


def _dump_model(model, title: str) -> None:
    print(f"\n{_GRAY}— {title} —{_RESET}")
    print(json.dumps(model.model_dump(mode="json"), ensure_ascii=False, indent=2))


async def _run_case(
    session, repo, service: AddressService, addr: AddressInput
) -> None:
    """Прогоняет один кейс через диагностику и сервис."""
    addr_input = addr.model_copy(
        update={
            k: (v if v else None) for k, v in addr.model_dump().items()
        }
    )
    _dump_model(addr_input, "AddressInput (вход)")

    # Показываем, во что превращается вход после нормализации.
    normalized = service._normalize_input(addr_input)
    _dump_model(normalized, "NormalizedAddressInput (после нормализации)")

    # Проверяем наличие pg_trgm (для честной диагностики fuzzy).
    await _check_pg_trgm(session)

    context = await _print_context_diag(service, addr_input)

    if addr_input.landmark:
        if context is not None:
            await _print_landmark_diag(
                service, context.district_ids, addr_input.landmark
            )
    elif addr_input.street and addr_input.house:
        if context is not None:
            streets = await _print_street_diag(
                service, context.district_ids, normalized.street
            )
            if streets:
                await _print_house_diag(service, streets, normalized.house)
                await _print_suggestion_diag(service, streets, normalized.house)
    else:
        print(
            f"\n{_GRAY}(правило сервиса: street+house ИЛИ landmark — "
            f"иначе будет INCOMPLETE){_RESET}"
        )

    result = await service.resolve_address(addr_input)
    _print_result(result)
    _dump_model(result, "AddressMatchResult (полные данные ответа)")


# --------------------------------------------------------------------------
# Fuzzy-пробник
# --------------------------------------------------------------------------


async def _probe(session, word: str) -> None:
    """Выводит топ-N улиц по похожести на слово (не зависит от района)."""
    threshold = address_config.fuzzy_threshold
    town = await session.scalar(
        select(Town).where(
            func.lower(Town.name) == address_config.default_town_name
        )
    )
    district_ids: list[int] = []
    if town is not None:
        district_ids = list(
            (
                await session.execute(
                    select(District.id).where(District.town_id == town.id)
                )
            ).scalars()
        )

    try:
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
    except ProgrammingError as exc:
        print(
            "Fuzzy-пробник недоступен (pg_trgm не установлен): "
            f"{exc.orig if getattr(exc, 'orig', None) else exc}"
        )
        return

    print(
        f"\nFuzzy-пробник для '{word}' (порог {threshold}, "
        f"топ-{address_config.max_candidates}):"
    )
    if not rows:
        print("  ничего не найдено")
    for r in rows:
        print(f"  {r.name!r} ({r.district_name})  sim={r.sim:.3f}")


# --------------------------------------------------------------------------
# Интерактивный режим
# --------------------------------------------------------------------------


async def _interactive(session, repo, service: AddressService) -> None:
    print("Интерактивный режим — поэтапный ввод полей AddressInput.")
    print("Для пропуска поля просто нажмите Enter (будет считаться None).")
    print("Команды:  :probe <слово>  — fuzzy‑пробник")
    print("          :q / :quit      — выход")
    print("          Ctrl+D или все поля пустыми — выход\n")

    while True:
        try:
            street = input("street> ").strip() or None
            district = input("district> ").strip() or None
            landmark = input("landmark> ").strip() or None
            house = input("house> ").strip() or None
            town = input("town> ").strip() or None
        except (EOFError, KeyboardInterrupt):
            print("\nДо свидания!")
            return

        # Выход, только если пользователь ничего не ввёл ни в одно поле.
        if not any((street, district, landmark, house, town)):
            print("До свидания!")
            return

        # Спецкоманды в любом поле.
        all_values = (street, district, landmark, house, town)
        if any(
            isinstance(v, str) and v.lower() in (":q", ":quit")
            for v in all_values
        ):
            print("До свидания!")
            return
        probe_word = next(
            (
                v[len(":probe"):].strip()
                for v in all_values
                if isinstance(v, str) and v.startswith(":probe")
            ),
            None,
        )
        if probe_word is not None:
            await _probe(session, probe_word)
            print()
            continue

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
        description="Точечная проверка НОВОГО адресного сервиса "
                    "(app/services/address).",
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
            '--json \'{"street": "Гагарина", "house": "2а"}\''
        ),
    )
    return parser.parse_args(argv)


async def _main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)

    async with async_session_factory() as session:
        repo = AddressRepository(session)
        service = _build_service(repo)

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
            await _run_case(session, repo, service, AddressInput(**fields))
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



