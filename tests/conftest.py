"""Общие фикстуры: сессия БД и собранный AddressService.

Тесты выполняются против РЕАЛЬНОЙ запущенной БД (см. .env / docker-compose.yml).

==============================================================================
КАК ЗАПУСКАТЬ (кратко; подробно — в docstring test_address_scenarios.py)
==============================================================================
    # весь набор: сценарии из docs/test_case_address.json + unit-тесты
    .venv/bin/python -m pytest

    # сценарии AddressService
    .venv/bin/python -m pytest tests/test_address_scenarios.py -v
==============================================================================
"""

from __future__ import annotations

import pytest_asyncio

from app.core.config import address_config
from app.core.database import async_session_factory
from app.repositories.address_repo import AddressRepository
from app.services.address.address_service import AddressService
from app.services.address.context_resolver import ContextResolver
from app.services.address.house_resolver import HouseResolver
from app.services.address.landmark_resolver import LandmarkResolver
from app.services.address.street_resolver import StreetResolver
from app.services.address.suggestion_service import AddressSuggestionService


def build_address_service(repo: AddressRepository) -> AddressService:
    """Собирает новый AddressService из резолверов и suggestion-сервиса."""
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


@pytest_asyncio.fixture(scope="session")
async def session():
    """Одна асинхронная сессия SQLAlchemy на всю тестовую сессию."""
    async with async_session_factory() as session:
        yield session


@pytest_asyncio.fixture(scope="session")
async def address_service(session) -> AddressService:
    """Полностью собранный AddressService, работающий с реальной БД."""
    return build_address_service(AddressRepository(session))


@pytest_asyncio.fixture(scope="session")
async def suggestion_service(session) -> AddressSuggestionService:
    """AddressSuggestionService для unit-проверок внутренней логики."""
    return AddressSuggestionService(AddressRepository(session))
