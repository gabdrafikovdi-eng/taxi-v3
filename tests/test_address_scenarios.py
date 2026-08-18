"""Integration/regression тесты AddressService по сценариям из JSON.

Сценарии загружаются из ``docs/test_case_address.json`` при КАЖДОМ запуске
pytest (на этапе сбора тестов): изменение JSON автоматически влияет на
следующий запуск. Сценарии не копируются в код вручную.

Каждый сценарий прогоняется через полный конвейер:

    input
    -> AddressService.resolve_address()
    -> AddressMatchResult

а затем проверяется по полям сценария (tests.checkers) и по assertion-
предикатам (tests.scenario_assertions).

==============================================================================
КАК ЗАПУСКАТЬ
==============================================================================

Предусловия:
1. Запущен PostgreSQL из docker-compose.yml (host=localhost, port=5432,
   db=taxi-db, user/password в .env). Проверка: ``pg_isready -h localhost``.
2. Виртуальное окружение проекта: ``.venv`` (создаётся командой
   ``python3.14 -m venv .venv``; зависимости фиксируются в pyproject.toml
   / uv.lock, устанавливаются ``uv sync`` или ``pip install -r`` из lock).
3. Файл сценариев ``docs/test_case_address.json`` существует и является
   валидным JSON (``json.load`` обязан проходить).

Команды (запуск из корня проекта taxi-v3):

    # весь тестовый набор (сценарии + sanity + unit AddressSuggestionService)
    .venv/bin/python -m pytest

    # только сценарии AddressService (verbose)
    PYTHONPATH=. .venv/bin/python -m pytest tests/test_address_scenarios.py -v

    # конкретный сценарий по id из JSON
    .venv/bin/python -m pytest -k "test_scenario_from_json[A08]"

    # несколько сценариев по маске (все landmark, все 14к9 и т.п.)
    .venv/bin/python -m pytest -k "test_scenario_from_json[S0 or A4]"

    # unit-тесты AddressSuggestionService / парсера номеров домов
    .venv/bin/python -m pytest tests/test_suggestion_service_unit.py

    # с отчётом о покрытии pytest
    # с отчётом о покрытии production-кода
    .venv/bin/python -m pytest --cov=app --cov-report=term-missing

Важно:
- Тесты выполняются против РЕАЛЬНОЙ БД и ничего в ней не создают и не
  изменяют (только SELECT).
- Число тестов = 150 сценариев + sanity-проверки + unit-тесты. Если в JSON
  добавить/изменить сценарий, следующий запуск pytest автоматически это
  подхватит (перезапускать pytest обязательно — кеша нет).
- Сценарии с текстовым полем ``assertion`` сопоставляются с предикатами в
  tests/scenario_assertions.py. Если assertion не распознан, тест падает с
  сообщением "unhandled assertion" — так нельзя молча игнорировать
  требования из JSON.
"""

from __future__ import annotations

import pytest

from app.schemas.address import AddressInput
from tests.checkers import check_scenario
from tests.scenario_assertions import run_assertions
from tests.scenario_loader import load_scenarios, load_scenarios_meta, SCENARIOS_PATH

# Считывается при сборе тестов -> при каждом запуске pytest.
_SCENARIOS = load_scenarios()
_META = load_scenarios_meta()


@pytest.mark.asyncio
@pytest.mark.parametrize("scenario", _SCENARIOS, ids=lambda scenario: scenario["id"])
async def test_scenario_from_json(scenario: dict, address_service) -> None:
    """Выполняет сценарий из JSON через AddressService и проверяет результат."""
    result = await address_service.resolve_address(AddressInput(**scenario["input"]))

    # Проверка полей сценария (expected_status, suggestions, contains/excludes...).
    check_scenario(scenario, result)

    # Проверка assertion-предикатов (человекочитаемые требования из JSON).
    await run_assertions(scenario, result, address_service)


def test_scenarios_source_file_exists() -> None:
    """Файл-источник сценариев обязан существовать и читаться как JSON."""
    assert SCENARIOS_PATH.is_file(), f"Scenarios file not found: {SCENARIOS_PATH}"
    assert _META["test_suite"] == "AddressService + Suggestions"


def test_scenario_ids_are_unique() -> None:
    """Идентификаторы сценариев в JSON должны быть уникальными."""
    ids = [scenario["id"] for scenario in _SCENARIOS]
    duplicates = {scenario_id for scenario_id in ids if ids.count(scenario_id) > 1}
    assert not duplicates, f"Duplicate scenario ids: {duplicates}"


def test_every_scenario_has_input() -> None:
    """Каждый сценарий обязан иметь поле input (объект AddressInput)."""
    for scenario in _SCENARIOS:
        assert "input" in scenario, f"{scenario['id']} has no input"
        assert isinstance(scenario["input"], dict)
