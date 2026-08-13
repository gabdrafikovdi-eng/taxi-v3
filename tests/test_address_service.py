"""Комплексные интеграционные тесты адресной воронки (AddressService + AddressRepository).

Тесты выполняются на реальной PostgreSQL БД (`taxi-db`), предварительно
наполняемой фикстурой ``seed_askarovo_db`` данными из ``docs/askarovo.yaml``,
тестовыми домами и ориентиром «Районная больница».

Это стресс-тесты реальной работоспособности воронки поиска, а не mock-покрытие:
каждый вызов ``AddressService.resolve_address`` проходит через реальный SQLAlchemy
запрос к БД (town -> district -> street exact/synonym/fuzzy -> house -> landmark).

ПРИМЕЧАНИЕ о полях кандидата:
в схеме ``AddressCandidate`` строка адреса называется ``fulladdress`` (без
подчёркивания), поэтому в ассертах используется ``candidate.fulladdress``.
"""

import pytest

from app.schemas.address import AddressInput, AddressStatus

pytestmark = pytest.mark.asyncio


async def _resolve(service, **fields) -> object:
    """Оборачивает вызов сервиса в AddressInput и возвращает AddressMatchResult."""
    return await service.resolve_address(AddressInput(**fields))


class TestExactStreets:
    """Точное совпадение уникальных улиц."""

    async def test_unique_street_resolved(self, address_service) -> None:
        # 1. Точное совпадение уникальной улицы.
        result = await _resolve(address_service, street="Емельяна Пугачёва")

        assert result.status is AddressStatus.RESOLVED
        assert len(result.candidates) == 1

        cand = result.candidates[0]
        assert cand.district_name == "Восточный-1"
        assert cand.score > 0.0
        assert cand.town_id > 0
        assert cand.district_id > 0
        assert cand.street_id > 0
        assert "Емельяна Пугачёва" in cand.fulladdress
        assert "Восточный-1" in cand.fulladdress


class TestDuplicateStreets:
    """Дубли улиц в разных районах."""

    async def test_duplicate_without_district_is_ambiguous(self, address_service) -> None:
        # 2. Улица-дубликат без района -> AMBIGUOUS с двумя кандидатами и diff_feature.
        result = await _resolve(address_service, street="Ленина")

        assert result.status is AddressStatus.AMBIGUOUS
        assert len(result.candidates) == 2

        districts = {c.district_name for c in result.candidates}
        assert districts == {"Центр", "Северный"}

        # КРИТИЧНО: у кандидатов должен быть заполнен diff_feature.
        diffs = {c.diff_feature for c in result.candidates}
        assert diffs == {"район Центр", "район Северный"}

        for cand in result.candidates:
            assert cand.score > 0.0
            assert cand.town_id > 0

    async def test_duplicate_with_district_resolves(self, address_service) -> None:
        # 3. Улица-дубликат с указанием района -> RESOLVED, Центр отсечён.
        result = await _resolve(address_service, street="Ленина", district="Северный")

        assert result.status is AddressStatus.RESOLVED
        assert len(result.candidates) == 1

        cand = result.candidates[0]
        assert cand.district_name == "Северный"
        assert cand.district_name != "Центр"
        assert "ул. Ленина" in cand.fulladdress
        assert "р-н Северный" in cand.fulladdress
        assert cand.score > 0.0

    async def test_district_with_hyphen_and_digit(self, address_service) -> None:
        # 4. Поиск в районе «Восточный-1» (дефис/цифра) не должен задевать Восточный-2.
        result = await _resolve(
            address_service, street="Шаймуратова", district="Восточный-1"
        )

        assert result.status is AddressStatus.RESOLVED
        assert len(result.candidates) == 1

        cand = result.candidates[0]
        assert cand.district_name == "Восточный-1"
        assert cand.district_name != "Восточный-2"
        assert cand.score > 0.0

    async def test_case_insensitive_and_extra_spaces(self, address_service) -> None:
        # 11. Регистронезависимость и лишние пробелы.
        result = await _resolve(
            address_service, street="   лЕнИнА  ", district="  цЕнТр "
        )

        assert result.status is AddressStatus.RESOLVED
        assert len(result.candidates) == 1

        cand = result.candidates[0]
        assert cand.district_name == "Центр"
        assert "Ленина" in cand.fulladdress
        assert cand.score > 0.0


class TestDefaultTown:
    """Подстановка города по умолчанию."""

    async def test_default_town_used(self, address_service) -> None:
        # 5. default_town_name подставляется при town=None.
        result = await _resolve(address_service, street="Учалинская", town=None)

        assert result.status is AddressStatus.RESOLVED
        assert len(result.candidates) == 1

        cand = result.candidates[0]
        assert cand.district_name == "Центр"
        assert cand.town_id > 0
        assert cand.score > 0.0
        # Учалинская есть только в Центре.
        assert "р-н Центр" in cand.fulladdress


class TestFuzzySearch:
    """Fuzzy-поиск улиц с опечатками."""

    async def test_typo_returns_matching_street(self, address_service) -> None:
        # 6a. «Гагарына» -> «Гагарина».
        result = await _resolve(address_service, street="Гагарына")

        # Из-за высокой неоднозначности допускаем RESOLVED или AMBIGUOUS,
        # но главный кандидат обязан быть «Гагарина» с положительным score.
        assert result.status in (AddressStatus.RESOLVED, AddressStatus.AMBIGUOUS)
        assert result.candidates, "должен быть хотя бы один кандидат"

        top = result.candidates[0]
        assert top.street_name == "Гагарина"
        assert top.score > 0.0

    async def test_typo_returns_shaimuratova(self, address_service) -> None:
        # 6b. «Шахмуратов» -> «Шаймуратова».
        result = await _resolve(address_service, street="Шахмуратов")

        assert result.status in (AddressStatus.RESOLVED, AddressStatus.AMBIGUOUS)
        assert result.candidates, "должен быть хотя бы один кандидат"

        top = result.candidates[0]
        assert top.street_name == "Шаймуратова"
        assert top.score > 0.0



class TestNationalNames:
    """Сложные национальные / двойные / с дефисом названия."""

    @pytest.mark.parametrize("street", ["Шайхзады Бабича", "Ак-Күлгин"])
    async def test_complex_names_resolved(self, address_service, street: str) -> None:
        # 7. Спецсимволы, дефисы, двойные имена обрабатываются корректно.
        result = await _resolve(address_service, street=street)

        assert result.status is AddressStatus.RESOLVED
        assert len(result.candidates) == 1

        cand = result.candidates[0]
        assert cand.street_name == street
        assert cand.score > 0.0
        assert street in cand.fulladdress


class TestLandmarks:
    """Поиск по ориентирам."""

    async def test_landmark_only(self, address_service) -> None:
        # 8. Поиск только по ориентиру «больница».
        result = await _resolve(address_service, landmark="больница")

        assert result.status is AddressStatus.RESOLVED
        assert len(result.candidates) == 1

        cand = result.candidates[0]
        assert "Гагарина" in cand.fulladdress
        assert "д. 5" in cand.fulladdress
        assert cand.district_name == "Центр"
        assert cand.house_id is not None
        assert "Районная больница" in cand.fulladdress
        assert cand.score > 0.0

    async def test_street_plus_landmark_boosts_score(self, address_service) -> None:
        # 9. Улица + ориентир повышают score у кандидата.
        without_landmark = await _resolve(address_service, street="Гагарина")
        with_landmark = await _resolve(
            address_service, street="Гагарина", landmark="больница"
        )

        assert without_landmark.candidates and with_landmark.candidates

        cand_plain = without_landmark.candidates[0]
        cand_boosted = with_landmark.candidates[0]

        # score при совпадении и улицы, и ориентира не должен быть меньше,
        # чем у поиска только по улице.
        assert cand_boosted.score >= cand_plain.score
        assert cand_boosted.score > 0.0
        # Логика бонуса за ориентир: в fulladdress указан landmark.
        assert "Районная больница" in cand_boosted.fulladdress


class TestNotFound:
    """Несуществующие сущности -> NOT_FOUND."""

    async def test_unknown_street_not_found(self, address_service) -> None:
        # 10a. Неизвестная улица.
        result = await _resolve(address_service, street="Невский проспект")

        assert result.status is AddressStatus.NOT_FOUND
        assert result.reason == "street_not_found"
        assert len(result.candidates) == 0

    async def test_unserved_town_not_found(self, address_service) -> None:
        # 10b. Город Уфа не обслуживается.
        result = await _resolve(address_service, town="Уфа", street="Ленина")

        assert result.status is AddressStatus.NOT_FOUND
        assert result.reason == "town_not_found"
        assert len(result.candidates) == 0

    async def test_unknown_district_not_found(self, address_service) -> None:
        # 10c. Несуществующий район.
        result = await _resolve(
            address_service, district="НесуществующийРайон", street="Ленина"
        )

        assert result.status is AddressStatus.NOT_FOUND
        assert result.reason == "district_not_found"
        assert len(result.candidates) == 0

