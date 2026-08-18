"""Unit-тесты внутренней логики AddressSuggestionService и парсера номеров домов.

Основная покрывающая логика живёт в test_address_scenarios.py (сценарии из
JSON через AddressService.resolve_address). Здесь дополнительно проверяется
внутренняя логика suggestion-сервиса и парсера house number.

==============================================================================
КАК ЗАПУСКАТЬ
==============================================================================
    .venv/bin/python -m pytest tests/test_suggestion_service_unit.py -v
==============================================================================
"""

from __future__ import annotations

import pytest
from sqlalchemy import text

from app.schemas.address import HouseNumberType
from app.services.address.house_number_parser import parse_house_number


# ---------------------------------------------------------------------------
# Парсер номеров домов (синхронные unit-тесты, БД не нужна)
# ---------------------------------------------------------------------------


def test_parse_plain():
    parts = parse_house_number("5")
    assert parts is not None
    assert parts.base == "5"
    assert parts.type is HouseNumberType.PLAIN
    assert parts.suffix is None


def test_parse_letter():
    parts = parse_house_number("14а")
    assert parts is not None
    assert parts.base == "14"
    assert parts.type is HouseNumberType.LETTER
    assert parts.suffix == "а"


def test_parse_letter_upper():
    parts = parse_house_number("51А")
    assert parts is not None
    assert parts.type is HouseNumberType.LETTER


def test_parse_corpus():
    parts = parse_house_number("14к1")
    assert parts is not None
    assert parts.base == "14"
    assert parts.type is HouseNumberType.CORPUS
    assert parts.suffix == "1"


def test_parse_fraction():
    parts = parse_house_number("127/1")
    assert parts is not None
    assert parts.base == "127"
    assert parts.type is HouseNumberType.FRACTION
    assert parts.suffix == "1"


def test_parse_incomplete_prefixes_return_none():
    # Неполные префиксы НЕ должны парситься как letter/corpus.
    assert parse_house_number("14к") is None
    assert parse_house_number("14/") is None


def test_parse_empty_and_none():
    assert parse_house_number("") is None
    assert parse_house_number(None) is None
    assert parse_house_number("   ") is None


# ---------------------------------------------------------------------------
# AddressSuggestionService (реальная БД)
# ---------------------------------------------------------------------------


async def _street_id(session, street_name: str, district_name: str) -> int:
    result = await session.execute(
        text(
            "select s.id from streets s "
            "join districts d on d.id = s.district_id "
            "where s.name = :street and d.name = :district"
        ),
        {"street": street_name, "district": district_name},
    )
    street_id = result.scalar_one_or_none()
    assert street_id is not None, f"street {street_name!r}/{district_name!r} not found"
    return street_id


@pytest.mark.asyncio
async def test_suggest_house_corpus(session, suggestion_service):
    street_id = await _street_id(session, "Ленина", "Центр")
    suggestions = await suggestion_service.suggest_house(street_id, "14к9")

    numbers = [s.house_number for s in suggestions]
    assert "14к1" in numbers
    # Все suggestions — корпусные варианты того же base.
    for suggestion in suggestions:
        parts = parse_house_number(suggestion.house_number or "")
        assert parts is not None
        assert parts.base == "14"
        assert parts.type is HouseNumberType.CORPUS


@pytest.mark.asyncio
async def test_suggest_house_letter(session, suggestion_service):
    street_id = await _street_id(session, "Шаймуратова", "Центр")
    suggestions = await suggestion_service.suggest_house(street_id, "12б")

    numbers = [s.house_number for s in suggestions]
    # На Шаймуратова (Центр) есть 12а -> только она и подходит.
    assert numbers == ["12а"]


@pytest.mark.asyncio
async def test_suggest_house_fraction(session, suggestion_service):
    street_id = await _street_id(session, "Шаймуратова", "Центр")
    suggestions = await suggestion_service.suggest_house(street_id, "14/9")

    numbers = [s.house_number for s in suggestions]
    assert "14/1" in numbers
    assert all(
        parse_house_number(s.house_number or "").type is HouseNumberType.FRACTION
        for s in suggestions
    )


@pytest.mark.asyncio
async def test_suggest_house_plain(session, suggestion_service):
    street_id = await _street_id(session, "Гагарина", "Центр")
    suggestions = await suggestion_service.suggest_house(street_id, "2")

    numbers = [s.house_number for s in suggestions]
    assert "2а" in numbers
    assert "2" not in numbers  # plain requested -> plain excluded


@pytest.mark.asyncio
async def test_suggest_house_no_compatible(session, suggestion_service):
    street_id = await _street_id(session, "Гагарина", "Центр")
    assert await suggestion_service.suggest_house(street_id, "500") == []


@pytest.mark.asyncio
async def test_suggest_house_limit(session, suggestion_service):
    street_id = await _street_id(session, "Ленина", "Центр")
    suggestions = await suggestion_service.suggest_house(street_id, "14к9", limit=1)
    assert len(suggestions) <= 1


@pytest.mark.asyncio
async def test_suggest_house_limit_zero(session, suggestion_service):
    street_id = await _street_id(session, "Гагарина", "Центр")
    assert await suggestion_service.suggest_house(street_id, "2", limit=0) == []


@pytest.mark.asyncio
async def test_suggest_house_unparseable_request(session, suggestion_service):
    street_id = await _street_id(session, "Ленина", "Центр")
    assert await suggestion_service.suggest_house(street_id, "14к") == []
    assert await suggestion_service.suggest_house(street_id, "14/") == []
