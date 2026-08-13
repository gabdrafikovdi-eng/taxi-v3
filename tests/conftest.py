"""Общие фикстуры и настройки тестового окружения."""

import os

# Устанавливаем переменные окружения ДО импорта app-модулей:
# app.core.database при импорте создаёт engine и читает DATABASE_URL,
# который строится из этих переменных.
os.environ.setdefault("POSTGRES_USER", "taxi_user")
os.environ.setdefault("POSTGRES_PASSWORD", "taxi_password")
os.environ.setdefault("POSTGRES_HOST", "localhost")
os.environ.setdefault("POSTGRES_PORT", "5432")
os.environ.setdefault("POSTGRES_DB", "taxi-db")
os.environ.setdefault("OPENAI_API_KEY", "test-key")
os.environ.setdefault("OPENAI_BASE_URL", "https://example.invalid")
os.environ.setdefault("OPENAI_MODEL", "test-model")

import pytest
import pytest_asyncio
import yaml
from pathlib import Path

from sqlalchemy import select, text

from app.core.database import Base, async_session_factory, engine
from app.models.address import District, House, Landmark, Street, Town
from app.models.order import Order
from app.models.order_state import OrderState
from app.repositories.address_repo import AddressRepository
from app.services.address_service import AddressService

# Путь к YAML с населённым пунктом Аскарово.
DOCS_ASKAROVO = Path(__file__).resolve().parent.parent / "docs" / "askarovo.yaml"

# Тестовые дома: (улица, район) -> номер дома.
TEST_HOUSES: dict[str, dict[str, str]] = {
    "Ленина": {"Центр": "40", "Северный": "12"},
    "Гагарина": {"Центр": "5"},
}

# Тестовый ориентир, привязанный к ул. Гагарина, д. 5 (район Центр).
TEST_LANDMARK: dict[str, str | None] = {
    "name": "Районная больница",
    "street": "Гагарина",
    "district": "Центр",
    "house": "5",
}


def _load_askarovo_yaml() -> tuple[str, list[dict]]:
    """Читает docs/askarovo.yaml и возвращает (название города, [районы с улицами])."""
    data = yaml.safe_load(DOCS_ASKAROVO.read_text(encoding="utf-8"))
    town_items = data["town"]

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
        raise ValueError("В docs/askarovo.yaml не найдено название города (town[].name)")

    districts: list[dict] = []
    for d in districts_raw:
        if not isinstance(d, dict) or not d.get("name"):
            continue
        streets = [s for s in (d.get("streets") or []) if s]
        districts.append({"name": d["name"], "streets": streets})

    return town_name, districts


@pytest_asyncio.fixture(scope="session")
async def seed_askarovo_db():
    """Наполняет основную БД районами и улицами Аскарово из YAML + тестовые дома и ориентир.

    Фикстура идемпотентна: уже существующие город/районы/улицы/дома/ориентиры
    не дублируются (учитываются unique-ограничения и проверки на существование).

    1. Активирует расширение pg_trgm (необходимо для fuzzy-поиска улиц).
    2. Создаёт таблицы, если их ещё нет (Base.metadata.create_all).
    3. Засеивает город/районы/улицы из docs/askarovo.yaml.
    4. Добавляет тестовые дома и ориентир «Районная больница».
    """
    async with engine.begin() as conn:
        await conn.execute(text("CREATE EXTENSION IF NOT EXISTS pg_trgm"))
        await conn.run_sync(Base.metadata.create_all)

    town_name, districts = _load_askarovo_yaml()

    async with async_session_factory() as session:
        # ---- Город ----
        town = await session.scalar(select(Town).where(Town.name == town_name))
        if town is None:
            town = Town(name=town_name, base_price=0)
            session.add(town)
            await session.flush()

        # ---- Районы и улицы ----
        for d in districts:
            district = await session.scalar(
                select(District).where(
                    District.town_id == town.id, District.name == d["name"]
                )
            )
            if district is None:
                district = District(town_id=town.id, name=d["name"])
                session.add(district)
                await session.flush()

            for street_name in d["streets"]:
                street = await session.scalar(
                    select(Street).where(
                        Street.district_id == district.id, Street.name == street_name
                    )
                )
                if street is None:
                    session.add(Street(district_id=district.id, name=street_name))

        # ---- Тестовые дома ----
        for street_name, district_numbers in TEST_HOUSES.items():
            for district_name, number in district_numbers.items():
                street = await session.scalar(
                    select(Street)
                    .join(District)
                    .where(Street.name == street_name, District.name == district_name)
                )
                if street is None:
                    continue
                house = await session.scalar(
                    select(House).where(
                        House.street_id == street.id, House.number == number
                    )
                )
                if house is None:
                    session.add(House(street_id=street.id, number=number))

        await session.commit()

        # ---- Ориентир (нужен id дома, поэтому отдельным блоком) ----
        landmark_street = await session.scalar(
            select(Street)
            .join(District)
            .where(
                Street.name == TEST_LANDMARK["street"],
                District.name == TEST_LANDMARK["district"],
            )
        )
        landmark_house = None
        if landmark_street is not None:
            landmark_house = await session.scalar(
                select(House).where(
                    House.street_id == landmark_street.id,
                    House.number == TEST_LANDMARK["house"],
                )
            )

        landmark = await session.scalar(
            select(Landmark).where(Landmark.name == TEST_LANDMARK["name"])
        )
        if landmark is None and landmark_street is not None:
            session.add(
                Landmark(
                    street_id=landmark_street.id,
                    house_id=landmark_house.id if landmark_house else None,
                    name=TEST_LANDMARK["name"],
                )
            )
        elif (
            landmark is not None
            and landmark.house_id is None
            and landmark_house is not None
        ):
            # Дозаполняем привязку к дому, если ориентир уже был создан без неё.
            landmark.house_id = landmark_house.id

        await session.commit()

    yield


@pytest_asyncio.fixture
async def db_session(seed_askarovo_db):
    """Асинхронная SQLAlchemy-сессия поверх засеянной БД."""
    async with async_session_factory() as session:
        yield session


@pytest.fixture
def address_repo(db_session) -> AddressRepository:
    """Репозиторий адресов, работающий с реальной БД."""
    return AddressRepository(db_session)


@pytest.fixture
def address_service(address_repo: AddressRepository) -> AddressService:
    """Сервис адресной воронки поверх реального репозитория."""
    return AddressService(address_repo)


@pytest.fixture
def draft_order() -> Order:
    """Заказ в состоянии DRAFT без адресов и цены."""
    return Order(state=OrderState.DRAFT)


@pytest.fixture
def confirmable_order() -> Order:
    """Заказ в DRAFT, готовый к подтверждению: оба адреса и цена."""
    order = Order(state=OrderState.DRAFT)
    order.pickup_street_id = 1
    order.destination_street_id = 2
    order.price = 500
    return order


@pytest.fixture
def confirmed_order() -> Order:
    """Заказ в состоянии CONFIRMED."""
    return Order(state=OrderState.CONFIRMED)


@pytest.fixture
def completed_order() -> Order:
    """Заказ в состоянии COMPLETED."""
    return Order(state=OrderState.COMPLETED)


@pytest.fixture
def cancelled_order() -> Order:
    """Заказ в состоянии CANCELLED."""
    return Order(state=OrderState.CANCELLED)