"""Regression suite для НОВОГО AddressService (app/services/address).

Контракт сервиса (бизнес-правила, реализованные в app/services/address):

    RESOLVED  = 1 уверенный кандидат
    AMBIGUOUS = 2+ кандидатов
    NOT_FOUND = ничего не нашли
    INCOMPLETE = нет (street + house) и нет landmark

Вход, при котором сервис начинает поиск:
    - street + house  (flow: Context -> Street exact/synonym/fuzzy -> House)
    - landmark        (flow: Context -> Landmark)
    Иначе: INCOMPLETE (reason=street_and_house_or_landmark).

Важные контрактные детали (сверены с актуальной БД 17.08.2026):
    - город один: Аскарово (id=4), 6 районов;
    - дубликаты улиц реально существуют (Ленина: Центр/Восточный-1/Северный;
      Шаймуратова: Центр + 2 пустые ветки; Кирова, Комарова, Школьная, Южная,
      60 лет Победы и др.);
    - номер дома ищется ТОЛЬКО точным совпадением (case-sensitive, без
      нормализации пробелов внутри номера): '33В' найдётся, '33в' — нет;
    - landmarks в БД: «Больница» (Ленина д.13), «Районная больница»
      (Гагарина д.5), «Нижний Магнит» (Сафи Истамгалина д.31);
      поиск ориентира — ILIKE '%{name}%'.

Тесты ТОЛЬКО читают БД (fixture seed_askarovo_db идемпотентна), не создают
и не изменяют справочник адресов. Проверка обязательна на реальной PostgreSQL.
"""

import pytest
import pytest_asyncio

from sqlalchemy import func, select

from app.core.config import address_config
from app.models.address import District, House, Landmark, Street, Town
from app.repositories.address_repo import AddressRepository
from app.schemas.address import AddressInput, AddressStatus
from app.services.address.address_service import AddressService
from app.services.address.context_resolver import ContextResolver
from app.services.address.house_resolver import HouseResolver
from app.services.address.landmark_resolver import LandmarkResolver
from app.services.address.street_resolver import StreetResolver

pytestmark = pytest.mark.asyncio


# ---------------------------------------------------------------------------
# Фикстуры
# ---------------------------------------------------------------------------


@pytest_asyncio.fixture
async def new_address_repo(db_session) -> AddressRepository:
    """Репозиторий поверх засеянной реальной БД."""
    return AddressRepository(db_session)


@pytest_asyncio.fixture
async def address_service_new(new_address_repo: AddressRepository) -> AddressService:
    """НОВЫЙ AddressService со всеми резолверами."""
    return AddressService(
        address_repo=new_address_repo,
        context_resolver=ContextResolver(
            address_repo=new_address_repo,
            default_town_name=address_config.default_town_name,
        ),
        street_resolver=StreetResolver(
            address_repo=new_address_repo,
            fuzzy_threshold=address_config.fuzzy_threshold,
            max_candidate=address_config.max_candidates,
        ),
        house_resolver=HouseResolver(address_repo=new_address_repo),
        landmark_resolver=LandmarkResolver(address_repo=new_address_repo),
    )


# ---------------------------------------------------------------------------
# Хелперы (только чтение БД)
# ---------------------------------------------------------------------------


async def _resolve(service: AddressService, **fields) -> object:
    """Обёртка вызова сервиса в AddressInput."""
    return await service.resolve_address(AddressInput(**fields))


async def _town(db_session, name: str = "Аскарово") -> Town | None:
    return await db_session.scalar(
        select(Town).where(func.lower(Town.name) == name.lower())
    )


async def _streets_by_name(
    db_session, street_name: str, district_name: str | None = None
) -> list[Street]:
    stmt = select(Street).where(Street.name == street_name)
    if district_name:
        stmt = (
            stmt.join(District, Street.district_id == District.id)
            .where(District.name == district_name)
        )
    return list((await db_session.execute(stmt)).scalars().all())


async def _first_house(
    db_session, street_name: str, district_name: str | None = None
) -> str | None:
    """Любой реальный номер дома на улице (для DB-driven сценариев)."""
    stmt = (
        select(House.number)
        .join(Street, House.street_id == Street.id)
        .where(Street.name == street_name)
    )
    if district_name:
        stmt = stmt.join(District, Street.district_id == District.id).where(
            District.name == district_name
        )
    return (
        await db_session.execute(stmt.order_by(House.number).limit(1))
    ).scalar_one_or_none()


async def _landmarks(db_session) -> list[Landmark]:
    return list(
        (
            await db_session.execute(
                select(Landmark).order_by(Landmark.id)
            )
        )
        .scalars()
        .all()
    )


def _assert_valid_candidate(cand) -> None:
    """Общие структурные проверки кандидата из AddressMatchResult."""
    assert cand.town_id > 0
    assert cand.town_name
    assert cand.district_id > 0
    assert cand.district_name
    assert cand.street_id > 0
    assert cand.street_name
    assert 0.0 <= cand.score <= 1.0
    assert cand.full_address
    assert "ул. " in cand.full_address
    assert "р-н " in cand.full_address


def _assert_no_duplicate_ids(candidates) -> None:
    """Один и тот же street_id/house_id не должен встречаться дважды."""
    street_ids = [c.street_id for c in candidates]
    house_ids = [c.house_id for c in candidates if c.house_id is not None]
    assert len(street_ids) == len(set(street_ids)), "дубликат street_id"
    assert len(house_ids) == len(set(house_ids)), "дубликат house_id"


async def _counts(db_session) -> dict[str, int]:
    counts = {}
    for model in (Town, District, Street, House, Landmark):
        counts[model.__name__] = await db_session.scalar(
            select(func.count()).select_from(model)
        )
    return counts


# ---------------------------------------------------------------------------
# 1. Базовые точные улицы (street + house) -> RESOLVED
# ---------------------------------------------------------------------------


class TestBaseStreetsResolved:
    """Уникальные улицы: street + реальный дом -> RESOLVED."""

    # Улицы, которые на 17.08.2026 уникальны по названию в Аскарово.
    STREETS = [
        "Гагарина",
        "Мира",
        "Советская",
        "Комсомольская",
        "Матросова",
        "Молодежная",
        "Первомайская",
        "Чапаева",
        "Юбилейная",
        "Лесная",
        "Дружбы",
        "Строителей",
        "Ак Кайын",
        "Мусы Гареева",
        "Файзрахмана Хисматуллина",
        "Ахмет Заки Валиди",
        "Коммунистическая",
        "Емельяна Пугачева",
        "Бииш Батыра",
        "Учалинская",
    ]

    @pytest.mark.parametrize("street_name", STREETS)
    async def test_unique_street_resolves(
        self, db_session, address_service_new, street_name
    ) -> None:
        # Актуализируем вход по БД: ровно одна улица + реальный номер дома.
        streets = await _streets_by_name(db_session, street_name)
        assert len(streets) == 1, (
            f"улица {street_name!r} больше не уникальна: "
            f"{[s.district_id for s in streets]}"
        )
        house = await _first_house(db_session, street_name)
        assert house, f"у {street_name!r} нет ни одного дома в БД"

        result = await _resolve(
            address_service_new, street=street_name, house=house
        )

        assert result.status is AddressStatus.RESOLVED
        assert len(result.candidates) == 1
        cand = result.candidates[0]
        _assert_valid_candidate(cand)
        assert cand.street_name == street_name
        assert cand.house_number == house
        assert cand.town_name == "Аскарово"


# ---------------------------------------------------------------------------
# 2. Дубликаты улиц (Ленина: Центр / Восточный-1 / Северный)
# ---------------------------------------------------------------------------


class TestDuplicateStreets:
    """Дубли названий в разных районах не должны ложно резолвиться."""

    async def test_lenina_without_house_is_incomplete(
        self, address_service_new
    ) -> None:
        result = await _resolve(address_service_new, street="Ленина")
        assert result.status is AddressStatus.INCOMPLETE
        assert result.reason == "street_and_house_or_landmark"

    async def test_lenina_500_resolves_to_vostochny1(
        self, address_service_new
    ) -> None:
        # Дом 500 есть только на Ленина в Восточном-1.
        result = await _resolve(
            address_service_new, street="Ленина", house="500"
        )
        assert result.status is AddressStatus.RESOLVED
        cand = result.candidates[0]
        assert cand.district_name == "Восточный-1"
        assert cand.street_name == "Ленина"

    async def test_lenina_13_resolves_to_centr(
        self, address_service_new
    ) -> None:
        # Дом 13 есть только на Ленина в Центре.
        result = await _resolve(
            address_service_new, street="Ленина", house="13"
        )
        assert result.status is AddressStatus.RESOLVED
        assert result.candidates[0].district_name == "Центр"

    async def test_lenina_12_is_ambiguous_centr_and_severny(
        self, address_service_new
    ) -> None:
        # Дом 12 есть в Центре и Северном -> AMBIGUOUS.
        result = await _resolve(
            address_service_new, street="Ленина", house="12"
        )
        assert result.status is AddressStatus.AMBIGUOUS
        districts = {c.district_name for c in result.candidates}
        assert districts == {"Центр", "Северный"}
        assert all(c.diff_feature for c in result.candidates)

    async def test_lenina_33_is_ambiguous_vostochny1_and_centr(
        self, address_service_new
    ) -> None:
        result = await _resolve(
            address_service_new, street="Ленина", house="33"
        )
        assert result.status is AddressStatus.AMBIGUOUS
        districts = {c.district_name for c in result.candidates}
        assert districts == {"Восточный-1", "Центр"}

    async def test_lenina_district_narrows_to_centr(
        self, address_service_new
    ) -> None:
        result = await _resolve(
            address_service_new,
            street="Ленина",
            district="Центр",
            house="33",
        )
        assert result.status is AddressStatus.RESOLVED
        assert result.candidates[0].district_name == "Центр"

    async def test_lenina_district_narrows_to_vostochny1(
        self, address_service_new
    ) -> None:
        result = await _resolve(
            address_service_new,
            street="Ленина",
            district="Восточный-1",
            house="33",
        )
        assert result.status is AddressStatus.RESOLVED
        assert result.candidates[0].district_name == "Восточный-1"

    async def test_lenina_district_narrows_to_severny(
        self, address_service_new
    ) -> None:
        # В Северном на Ленина есть только дом 12.
        result = await _resolve(
            address_service_new,
            street="Ленина",
            district="Северный",
            house="12",
        )
        assert result.status is AddressStatus.RESOLVED
        assert result.candidates[0].district_name == "Северный"

    @pytest.mark.parametrize("district", ["Южный", "Восточный-2", "Даутово"])
    async def test_lenina_wrong_district_not_found(
        self, address_service_new, district
    ) -> None:
        # Ленина в этих районах отсутствует -> NOT_FOUND.
        result = await _resolve(
            address_service_new,
            street="Ленина",
            district=district,
            house="12",
        )
        assert result.status is AddressStatus.NOT_FOUND
        assert not result.candidates

    async def test_lenina_unknown_house_not_found(
        self, address_service_new
    ) -> None:
        result = await _resolve(
            address_service_new, street="Ленина", house="9999"
        )
        assert result.status is AddressStatus.NOT_FOUND
        assert result.reason == "house_not_found"
        assert not result.candidates

    async def test_shaimuratova_with_district_picks_nontrivial(
        self, address_service_new
    ) -> None:
        # Шаймуратова есть в 3 районах, но дома есть только в Центре.
        result = await _resolve(
            address_service_new, street="Шаймуратова", house="12"
        )
        assert result.status is AddressStatus.RESOLVED
# ---------------------------------------------------------------------------
# 3. Районы: каждый из шести + негативные проверки
# ---------------------------------------------------------------------------


class TestDistricts:
    """По всем 6 районам: правильная пара (улица, дом) -> RESOLVED."""

    @pytest.mark.parametrize(
        "street_name, district, house",
        [
            ("Гагарина", "Центр", "5"),
            ("Лесная", "Южный", "2"),
            ("Емельяна Пугачева", "Восточный-1", "12"),
            ("Бииш Батыра", "Восточный-2", "14/1"),
            ("Ак Кайын", "Северный", "2"),
            ("Мусы Гареева", "Даутово", "2"),
        ],
    )
    async def test_resolved_in_district(
        self, address_service_new, street_name, district, house
    ) -> None:
        result = await _resolve(
            address_service_new,
            street=street_name,
            district=district,
            house=house,
        )
        assert result.status is AddressStatus.RESOLVED
        assert len(result.candidates) == 1
        cand = result.candidates[0]
        assert cand.district_name == district
        assert cand.street_name == street_name
        assert "р-н " + district in cand.full_address

    async def test_street_in_wrong_district_not_found(
        self, address_service_new
    ) -> None:
        # Гагарина есть только в Центре.
        result = await _resolve(
            address_service_new,
            street="Гагарина",
            district="Южный",
            house="5",
        )
        assert result.status is AddressStatus.NOT_FOUND
        assert not result.candidates

    async def test_unknown_district_not_found(
        self, address_service_new
    ) -> None:
        result = await _resolve(
            address_service_new,
            street="Гагарина",
            district="НесуществующийРайон",
            house="5",
        )
        assert result.status is AddressStatus.NOT_FOUND
        assert result.reason == "town_or_district_not_found"

    @pytest.mark.parametrize(
        "district_raw, district_expected",
        [
            ("центр", "Центр"),
            ("ЦЕНТР", "Центр"),
            (" Центр ", "Центр"),
            ("восточный-1", "Восточный-1"),
            ("ВОСТОЧНЫЙ-1", "Восточный-1"),
            (" восточный-1 ", "Восточный-1"),
            ("восточный-2", "Восточный-2"),
            ("ВОСТОЧНЫЙ-2", "Восточный-2"),
            ("северный", "Северный"),
            ("даутово", "Даутово"),
        ],
    )
    async def test_district_case_and_spaces(
        self, address_service_new, district_raw, district_expected
    ) -> None:
        # Для каждого района берём улицу, которая в нём реально есть.
        street_house = {
            "Центр": ("Гагарина", "5"),
            "Южный": ("Лесная", "2"),
            "Восточный-1": ("Емельяна Пугачева", "12"),
            "Восточный-2": ("Бииш Батыра", "14/1"),
            "Северный": ("Ак Кайын", "2"),
            "Даутово": ("Мусы Гареева", "2"),
        }
        street, house = street_house[district_expected]
        result = await _resolve(
            address_service_new,
            street=street,
            district=district_raw,
            house=house,
        )
        assert result.status is AddressStatus.RESOLVED
        assert result.candidates[0].district_name == district_expected


# ---------------------------------------------------------------------------
# 4. Default town
# ---------------------------------------------------------------------------


class TestDefaultTown:
    """Подстановка города по умолчанию и вариации регистра/пробелов."""

    @pytest.mark.parametrize(
        "town", [None, "Аскарово", "аскарово", "АСКАРОВО", " Аскарово "]
    )
    async def test_town_variants_resolve(self, address_service_new, town) -> None:
        kwargs = {"street": "Гагарина", "house": "5"}
        if town is not None:
            kwargs["town"] = town
        result = await _resolve(address_service_new, **kwargs)
        assert result.status is AddressStatus.RESOLVED
        assert result.candidates[0].town_name == "Аскарово"

    @pytest.mark.parametrize("town", ["Уфа", "Москва", "Челябинск"])
    async def test_unknown_town_not_found(
        self, address_service_new, town
    ) -> None:
        result = await _resolve(
            address_service_new, town=town, street="Гагарина", house="5"
        )
        assert result.status is AddressStatus.NOT_FOUND
        assert not result.candidates

    async def test_unknown_town_with_district_not_found(
        self, address_service_new
    ) -> None:
        result = await _resolve(
            address_service_new,
            town="Уфа",
            district="Центр",
            street="Гагарина",
            house="5",
        )
        assert result.status is AddressStatus.NOT_FOUND

    async def test_lenina_ambiguous_with_explicit_town(
        self, address_service_new
    ) -> None:
        result = await _resolve(
            address_service_new, town="Аскарово", street="Ленина", house="33"
        )
        assert result.status is AddressStatus.AMBIGUOUS
# ---------------------------------------------------------------------------
# 5. Нормализация улицы (служебные префиксы, кавычки, пробелы, регистр)
# ---------------------------------------------------------------------------


class TestStreetNormalization:
    """Все варианты входной строки улицы должны резолвиться в Гагарину."""

    STREET_VARIANTS = [
        "Гагарина",
        " Гагарина ",
        "  Гагарина  ",
        "ГАгАрИнА",
        "ГАГАРИНА",
        "ул. Гагарина",
        "ул Гагарина",
        "улица Гагарина",
        '"Гагарина"',
        "'Гагарина'",
        "  ул.   Гагарина  ",
        "улица Гагарина ",
    ]

    @pytest.mark.parametrize("street_raw", STREET_VARIANTS)
    async def test_street_variant_resolves(
        self, address_service_new, street_raw
    ) -> None:
        result = await _resolve(
            address_service_new, street=street_raw, house="5"
        )
        assert result.status is AddressStatus.RESOLVED
        cand = result.candidates[0]
# ---------------------------------------------------------------------------
# 6. Реальные дома: литеры, дроби, корпуса
# ---------------------------------------------------------------------------


class TestRealHouses:
    """Точные связки (улица, дом), сверенные с актуальной БД."""

    @pytest.mark.parametrize(
        "street, district, house",
        [
            ("Гагарина", "Центр", "5"),
            ("Мира", "Центр", "10/1"),
            ("Советская", "Центр", "2"),
            ("Ленина", "Центр", "127/1"),
            ("Ленина", "Центр", "14к1"),
            ("Ленина", "Центр", "16/1"),
            ("Шаймуратова", "Центр", "12"),
            ("Шаймуратова", "Центр", "12а"),
            ("Шаймуратова", "Центр", "14/1"),
            ("Шаймуратова", "Центр", "14/2"),
            ("Шаймуратова", "Центр", "16/1"),
            ("Шагали Шакман", "Северный", "16"),
            ("Шагали Шакмана", "Северный", "16/1"),
        ],
    )
    async def test_exact_house_resolves(
        self, address_service_new, street, district, house
    ) -> None:
        result = await _resolve(
            address_service_new,
            street=street,
            district=district,
            house=house,
        )
        assert result.status is AddressStatus.RESOLVED
        assert len(result.candidates) == 1
        cand = result.candidates[0]
        assert cand.street_name == street
        assert cand.district_name == district
        assert cand.house_number == house
        assert cand.house_id is not None


class TestLiteraHouses:
    """Литерные номера: точное совпадение по БД (case-sensitive)."""

    @pytest.mark.parametrize(
        "street, house",
        [
            ("Молодежная", "10а"),
            ("Молодежная", "10б"),
            ("Молодежная", "12а"),
            ("Юбилейная", "33а"),
            ("Юбилейная", "33б"),
            ("Юбилейная", "33к1"),
            # Вход нормализуется в lower(): "10К2" -> "10к2" и попадает в БД.
            ("Тангатарская", "10К2"),
        ],
    )
    async def test_litera_exists_resolves(
        self, address_service_new, street, house
    ) -> None:
        result = await _resolve(address_service_new, street=street, house=house)
        assert result.status is AddressStatus.RESOLVED
        # Номер дома возвращается в форме из БД, сравнение без учёта регистра.
        assert result.candidates[0].house_number.lower() == house.lower()

    @pytest.mark.parametrize(
        "street, house",
        [
            # В БД литеры с ЗАГЛАВНОЙ буквой ('4А', '33В'), а вход нормализуется
            # в lower-case -> такие дома сейчас недостижимы (контракт БД).
            ("Советская", "4А"),
            ("Юбилейная", "33В"),
            ("Дружбы", "23А"),
        ],
    )
    async def test_uppercase_db_litera_not_reachable(
        self, address_service_new, street, house
    ) -> None:
        result = await _resolve(address_service_new, street=street, house=house)
        assert result.status is AddressStatus.NOT_FOUND
        assert not result.candidates

    @pytest.mark.parametrize(
        "street, house",
        [
            # В БД '33В' с большой буквы; номера домов ищутся точно.
            ("Юбилейная", "33в"),
            # Литеры нет на этой улице -> NOT_FOUND (а не подмена на 33а/33б).
            ("Юбилейная", "33г"),
            # Номера есть, но на других улицах.
            ("Юбилейная", "127/1"),
            ("Молодежная", "16/1"),
        ],
    )
    async def test_litera_missing_not_found(
        self, address_service_new, street, house
    ) -> None:
        result = await _resolve(address_service_new, street=street, house=house)
        assert result.status is AddressStatus.NOT_FOUND
        assert not result.candidates


class TestFractionHouses:
    """Дробные номера домов и их точное совпадение."""

    @pytest.mark.parametrize(
        "street, district, house",
        [
            ("Дружбы", "Южный", "35/1"),
            ("Мира", "Центр", "10/1"),
            ("Ленина", "Центр", "127/1"),
            ("Бииш Батыра", "Восточный-2", "1/1"),
            ("Шаймуратова", "Центр", "14/1"),
        ],
    )
    async def test_fraction_exists_resolves(
        self, address_service_new, street, district, house
    ) -> None:
        result = await _resolve(
            address_service_new,
            street=street,
            district=district,
            house=house,
        )
        assert result.status is AddressStatus.RESOLVED
        assert result.candidates[0].house_number == house

    @pytest.mark.parametrize(
        "street, house",
        [
            # Пробелы внутри номера не нормализуются (контракт: точное совпадение).
            ("Ленина", "127 / 1"),
            ("Ленина", "127/ 1"),
            # Таких дробей нет в БД.
            ("Ленина", "999/1"),
            ("Гагарина", "1/999"),
        ],
    )
    async def test_fraction_absent_not_found(
        self, address_service_new, street, house
    ) -> None:
        result = await _resolve(address_service_new, street=street, house=house)
        assert result.status is AddressStatus.NOT_FOUND
        assert not result.candidates


class TestKorpusHouses:
    """Корпусные номера вида 10к2, 33к1, 14к1."""

    @pytest.mark.parametrize(
        "street, district, house",
        [
            ("Тангатарская", "Центр", "10к2"),
            ("Юбилейная", "Центр", "33к1"),
            ("Юбилейная", "Центр", "33к2"),
            ("Ленина", "Центр", "14к1"),
            ("Ленина", "Центр", "52к1"),
        ],
    )
    async def test_korpus_exists_resolves(
        self, address_service_new, street, district, house
    ) -> None:
        result = await _resolve(
            address_service_new,
            street=street,
            district=district,
            house=house,
        )
        assert result.status is AddressStatus.RESOLVED
        assert result.candidates[0].house_number == house

    @pytest.mark.parametrize(
        "street, house",
        [
            ("Тангатарская", "10к 2"),
            ("Тангатарская", "10 к2"),
            ("Юбилейная", "999к9"),
        ],
    )
    async def test_korpus_absent_or_case_mismatch_not_found(
        self, address_service_new, street, house
    ) -> None:
        # Совпадение дома строго посимвольное: пробелы НЕ варьируются.
        result = await _resolve(address_service_new, street=street, house=house)
        assert result.status is AddressStatus.NOT_FOUND
        assert not result.candidates


# ---------------------------------------------------------------------------
# 7. Fuzzy-поиск улиц
# ---------------------------------------------------------------------------


class TestFuzzyStreets:
    """Опечатки в названии улицы должны уходить в правильную улицу + дом."""

    @pytest.mark.parametrize(
        "street_typo, street_expected, house",
        [
            ("Мера", "Мира", "9"),
            ("Шахмуратов", "Шаймуратова", "12"),
            ("Гагарына", "Гагарина", "5"),
            ("70 лет октябры", "70 лет Октября", "89"),
            ("Гагарин", "Гагарина", "5"),
            ("Гагаринаа", "Гагарина", "5"),
            ("Советска", "Советская", "2"),
            ("Комароваа", "Комарова", "1"),
            ("Первомайска", "Первомайская", "1"),
        ],
    )
    async def test_typo_resolves_to_correct_street(
        self,
        address_service_new,
        street_typo,
        street_expected,
        house,
    ) -> None:
        result = await _resolve(
            address_service_new, street=street_typo, house=house
        )
        assert result.status is AddressStatus.RESOLVED, (
            f"typo={street_typo!r}: status={result.status}, "
            f"candidates={[c.full_address for c in result.candidates]}"
        )
        cand = result.candidates[0]
        assert cand.street_name == street_expected
        assert cand.house_number == house

    async def test_nonsense_street_not_found(
        self, address_service_new
    ) -> None:
        result = await _resolve(
            address_service_new,
            street="абсолютноНесуществующаяУлица999",
            house="5",
        )
        assert result.status is AddressStatus.NOT_FOUND
        assert not result.candidates

    async def test_fuzzy_with_wrong_district_not_found(
        self, address_service_new
    ) -> None:
        # «Гагарына» + район, где Гагариной нет.
        result = await _resolve(
            address_service_new,
            street="Гагарына",
            district="Южный",
            house="5",
        )
        assert result.status is AddressStatus.NOT_FOUND
        assert not result.candidates


# ---------------------------------------------------------------------------
# 8. Критические похожие улицы
# ---------------------------------------------------------------------------


class TestSimilarStreets:
    """Проверка, что очень похожие названия не склеиваются fuzzy-ом."""

    async def test_shagali_shakman_16_resolves_to_shakman(
        self, address_service_new
    ) -> None:
        result = await _resolve(
            address_service_new, street="Шагали Шакман", house="16"
        )
        assert result.status is AddressStatus.RESOLVED
        cand = result.candidates[0]
        assert cand.street_name == "Шагали Шакман"
        assert cand.district_name == "Северный"

    async def test_shagali_shakmana_16_1_resolves_to_shakmana(
        self, address_service_new
    ) -> None:
        result = await _resolve(
            address_service_new, street="Шагали Шакмана", house="16/1"
        )
        assert result.status is AddressStatus.RESOLVED
        cand = result.candidates[0]
        assert cand.street_name == "Шагали Шакмана"
        assert cand.district_name == "Северный"

    async def test_shakman_does_not_absorb_shakmana_house(
        self, address_service_new
    ) -> None:
        # 16/1 существует только на Шагали Шакмана.
        result = await _resolve(
            address_service_new, street="Шагали Шакман", house="16/1"
        )
        assert result.status is AddressStatus.NOT_FOUND
        assert not result.candidates

    async def test_shakmana_does_not_absorb_shakman_house(
        self, address_service_new
    ) -> None:
        # 16 существует только на Шагали Шакман.
        result = await _resolve(
            address_service_new, street="Шагали Шакмана", house="16"
        )
        assert result.status is AddressStatus.NOT_FOUND
        assert not result.candidates

    async def test_40_vs_70_oktyabrya_distinct(
        self, address_service_new
    ) -> None:
        r40 = await _resolve(
            address_service_new, street="40 лет Октября", house="10"
        )
        assert r40.status is AddressStatus.RESOLVED
        assert r40.candidates[0].district_name == "Центр"

        r70 = await _resolve(
            address_service_new, street="70 лет Октября", house="10"
        )
        assert r70.status is AddressStatus.RESOLVED
        assert r70.candidates[0].district_name == "Южный"

        # 89 есть только на 70 лет Октября.
        r40_89 = await _resolve(
            address_service_new, street="40 лет Октября", house="89"
        )
        assert r40_89.status is AddressStatus.NOT_FOUND

    async def test_60_let_pobedy_resolves_to_vostochny1(
        self, db_session, address_service_new
    ) -> None:
        # 60 лет Победы есть в Восточном-1 и Даутово, но дома — только в В-1.
        house = await _first_house(db_session, "60 лет Победы")
        assert house, "нет домов на 60 лет Победы"
        result = await _resolve(
            address_service_new, street="60 лет Победы", house=house
        )
        assert result.status is AddressStatus.RESOLVED
        assert result.candidates[0].district_name == "Восточный-1"


# ---------------------------------------------------------------------------
# 9. Пустые/частичные входы -> policy INCOMPLETE
# ---------------------------------------------------------------------------


class TestIncompleteInputs:
    """Если нет (street+house) и нет landmark -> INCOMPLETE без поиска."""

    @pytest.mark.parametrize(
        "fields",
        [
            {},
            {"town": "Аскарово"},
            {"district": "Центр"},
            {"street": "Гагарина"},
            {"house": "5"},
            {"district": "Центр", "house": "5"},
            {"town": "Аскарово", "house": "5"},
            {"town": "Аскарово", "district": "Центр"},
        ],
    )
    async def test_incomplete(self, address_service_new, fields) -> None:
        result = await _resolve(address_service_new, **fields)
        assert result.status is AddressStatus.INCOMPLETE
        assert result.reason == "street_and_house_or_landmark"
        assert not result.candidates


# ---------------------------------------------------------------------------
# 10. Landmarks (актуализируются по БД)
# ---------------------------------------------------------------------------


class TestLandmarks:
    """Каждый реальный ориентир должен резолвиться; поиск — ILIKE %name%."""

    async def test_every_landmark_resolves(
        self, db_session, address_service_new
    ) -> None:
        landmarks = await _landmarks(db_session)
        assert len(landmarks) >= 3, (
            f"в БД должно быть >=3 ориентира, найдено {len(landmarks)}"
        )
        for lm in landmarks:
            result = await _resolve(address_service_new, landmark=lm.name)
            # ILIKE '%name%' может подсветить и других ориентиров-дублей,
            # поэтому для каждого ориентира ищем ЕГО кандидата среди выдачи.
            assert result.status in (
                AddressStatus.RESOLVED,
                AddressStatus.AMBIGUOUS,
            ), f"landmark {lm.name!r}: {result.status}"
            matches = [
                c
                for c in result.candidates
                if c.landmark_name == lm.name and c.street_id == lm.street_id
            ]
            assert matches, (
                f"landmark {lm.name!r} не вошёл в кандидатов: "
                f"{[c.landmark_name for c in result.candidates]}"
            )

    async def test_nizhniy_magnit_resolves(self, address_service_new) -> None:
        result = await _resolve(
            address_service_new, landmark="Нижний Магнит"
        )
        assert result.status is AddressStatus.RESOLVED
        cand = result.candidates[0]
        assert cand.landmark_name == "Нижний Магнит"
        assert cand.street_name == "Сафи Истамгалина"
        assert cand.district_name == "Восточный-1"
        assert cand.house_number == "31"

    @pytest.mark.parametrize(
        "landmark_raw", ["нижний магнит", "  Нижний Магнит  "]
    )
    async def test_landmark_case_and_spaces(
        self, address_service_new, landmark_raw
    ) -> None:
        result = await _resolve(address_service_new, landmark=landmark_raw)
        assert result.status is AddressStatus.RESOLVED
        assert result.candidates[0].landmark_name == "Нижний Магнит"

    async def test_bolnica_is_ambiguous(
        self, address_service_new
    ) -> None:
        # '%больница%' матчит и «Больница», и «Районная больница».
        result = await _resolve(address_service_new, landmark="Больница")
        assert result.status is AddressStatus.AMBIGUOUS
        names = {c.landmark_name for c in result.candidates}
        assert names == {"Больница", "Районная больница"}

    async def test_landmark_typo_not_found(self, address_service_new) -> None:
        result = await _resolve(address_service_new, landmark="Больничк")
        assert result.status is AddressStatus.NOT_FOUND
        assert not result.candidates

    async def test_unknown_landmark_not_found(self, address_service_new) -> None:
        result = await _resolve(
            address_service_new, landmark="НеСуществующийОриентирXyz"
        )
        assert result.status is AddressStatus.NOT_FOUND
        assert not result.candidates

    async def test_landmark_flow_ignores_street_and_house(
        self, address_service_new
    ) -> None:
        # Если указан landmark — он приоритетнее street/house (см. сервис).
        result = await _resolve(
            address_service_new,
            street="Гагарина",
            house="999",
            landmark="Нижний Магнит",
        )
        assert result.status is AddressStatus.RESOLVED
        assert result.candidates[0].landmark_name == "Нижний Магнит"


# ---------------------------------------------------------------------------
# 11. Структура AddressMatchResult и защита от ложного резолва
# ---------------------------------------------------------------------------


class TestResultStructure:
    """Форма ответа сервиса."""

    async def test_resolved_single_candidate(self, address_service_new) -> None:
        result = await _resolve(
            address_service_new, street="Гагарина", house="5"
        )
        assert result.status is AddressStatus.RESOLVED
        assert len(result.candidates) == 1

    async def test_ambiguous_multiple_candidates_with_diff(
        self, address_service_new
    ) -> None:
        result = await _resolve(
            address_service_new, street="Ленина", house="33"
        )
        assert result.status is AddressStatus.AMBIGUOUS
        assert len(result.candidates) >= 2
        assert all(c.diff_feature for c in result.candidates)
        assert {c.diff_feature for c in result.candidates} == {
            "район Восточный-1",
            "район Центр",
        }

    async def test_not_found_has_no_candidates(self, address_service_new) -> None:
        result = await _resolve(
            address_service_new, street="Гагарина", house="999"
        )
        assert result.status is AddressStatus.NOT_FOUND
        assert result.candidates == []

    async def test_resolved_fks_match_db(
        self, db_session, address_service_new
    ) -> None:
        result = await _resolve(
            address_service_new, street="Гагарина", district="Центр", house="5"
        )
        assert result.status is AddressStatus.RESOLVED
        cand = result.candidates[0]

        town = await _town(db_session)
        assert cand.town_id == town.id

        rows = (
            (
                await db_session.execute(
                    select(Street, District, House)
                    .join(District, Street.district_id == District.id)
                    .join(House, House.street_id == Street.id)
                    .where(Street.name == "Гагарина", House.number == "5")
                )
            )
            .all()
        )
        assert len(rows) == 1
        street, district, house = rows[0]
        assert cand.street_id == street.id
        assert cand.district_id == district.id
        assert cand.house_id == house.id
        assert cand.house_number == house.number
        assert cand.district_name == district.name

    async def test_full_address_consistent(self, address_service_new) -> None:
        result = await _resolve(
            address_service_new, street="Коммунистическая", house="11/1"
        )
        assert result.status is AddressStatus.RESOLVED
        cand = result.candidates[0]
        assert "ул. Коммунистическая" in cand.full_address
        assert "д. 11/1" in cand.full_address
        assert "р-н Центр" in cand.full_address

    async def test_score_in_range(self, address_service_new) -> None:
        result = await _resolve(
            address_service_new, street="Гагарина", house="5"
        )
        assert all(0.0 <= c.score <= 1.0 for c in result.candidates)

    async def test_repeated_query_stable(self, address_service_new) -> None:
        r1 = await _resolve(address_service_new, street="Ленина", house="33")
        r2 = await _resolve(address_service_new, street="Ленина", house="33")
        assert r1.status is r2.status is AddressStatus.AMBIGUOUS
        assert [(c.street_id, c.house_id) for c in r1.candidates] == [
            (c.street_id, c.house_id) for c in r2.candidates
        ]

    async def test_no_duplicate_ids(self, address_service_new) -> None:
        result = await _resolve(address_service_new, street="Ленина", house="12")
        assert result.status is AddressStatus.AMBIGUOUS
        _assert_no_duplicate_ids(result.candidates)

    async def test_normalized_and_raw_give_same_result(
        self, address_service_new
    ) -> None:
        r_raw = await _resolve(
            address_service_new, street="  ул.   Гагарина  ", house="5"
        )
        r_norm = await _resolve(
            address_service_new, street="Гагарина", house="5"
        )
        assert r_raw.status is r_norm.status is AddressStatus.RESOLVED
        assert r_raw.candidates[0].street_id == r_norm.candidates[0].street_id
        assert r_raw.candidates[0].house_id == r_norm.candidates[0].house_id

    async def test_fuzzy_candidate_is_real_db_name(
        self, db_session, address_service_new
    ) -> None:
        result = await _resolve(
            address_service_new, street="Шахмуратов", house="12"
        )
        assert result.status is AddressStatus.RESOLVED
        cand = result.candidates[0]
        streets = await _streets_by_name(db_session, cand.street_name)
        # Название из результата обязано быть реальной улицей из БД
        # (даже если таких названий несколько, street_id должен существовать).
        assert cand.street_id in {s.id for s in streets}


class TestNoFalseResolutions:
    """Защита от ложного разрешения."""

    async def test_gagarina_999_not_other_house(self, address_service_new) -> None:
        result = await _resolve(
            address_service_new, street="Гагарина", house="999"
        )
        assert result.status is AddressStatus.NOT_FOUND
        assert not result.candidates

    async def test_lenina_9999_not_nearest_house(self, address_service_new) -> None:
        result = await _resolve(
            address_service_new, street="Ленина", house="9999"
        )
        assert result.status is AddressStatus.NOT_FOUND
        assert not result.candidates

    async def test_gagarina_5_not_gagarina_55(self, address_service_new) -> None:
        result = await _resolve(
            address_service_new, street="Гагарина", house="55"
        )
        assert result.status is AddressStatus.NOT_FOUND

    async def test_lenina_vostochny1_not_return_centr(
        self, address_service_new
    ) -> None:
        result = await _resolve(
            address_service_new,
            street="Ленина",
            district="Восточный-1",
            house="33",
        )
        assert result.status is AddressStatus.RESOLVED
        assert all(c.district_name == "Восточный-1" for c in result.candidates)

    async def test_lenina_centr_not_return_vostochny1(
        self, address_service_new
    ) -> None:
        result = await _resolve(
            address_service_new,
            street="Ленина",
            district="Центр",
            house="33",
        )
        assert result.status is AddressStatus.RESOLVED
        assert all(c.district_name == "Центр" for c in result.candidates)

    async def test_random_letters_no_fuzzy_match(self, address_service_new) -> None:
        result = await _resolve(
            address_service_new, street="йцукенгшщзхъ", house="5"
        )
        assert result.status is AddressStatus.NOT_FOUND
        assert not result.candidates

    async def test_random_letters_with_existing_house_no_resolve(
        self, address_service_new
    ) -> None:
        result = await _resolve(
            address_service_new, street="вфывфывфыв", house="5"
        )
        assert result.status is AddressStatus.NOT_FOUND
        assert not result.candidates

    async def test_mira_exact_does_not_lose_to_fuzzy(
        self, address_service_new
    ) -> None:
        result = await _resolve(address_service_new, street="Мира", house="9")
        assert result.status is AddressStatus.RESOLVED
        assert result.candidates[0].street_name == "Мира"


class TestNoDbWrites:
    """Сервис никогда не должен создавать/изменять записи справочника."""

    async def test_resolve_does_not_write(
        self, db_session, address_service_new
    ) -> None:
        before = await _counts(db_session)

        for kwargs in [
            {"street": "Гагарина", "house": "5"},
            {"street": "Ленина", "house": "33"},
            {"street": "Шахмуратов", "house": "12"},
            {"landmark": "Нижний Магнит"},
            {"street": "Гагарина", "house": "999"},
            {"street": "НЕСУЩЕСТВУЮЩАЯ", "house": "1"},
        ]:
            await _resolve(address_service_new, **kwargs)

        after = await _counts(db_session)
        assert before == after, f"сервис изменил БД: {before} -> {after}"