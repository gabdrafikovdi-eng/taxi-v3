"""Regression-тесты нормализации входных данных адреса (НОВЫЙ AddressService).

Тестируется ТОЛЬКО нормализация (app.services.address.address_service):

    _normalize_input()   — интеграция: town/district/street/house/landmark
    _normalize_text()    — базовое приведение строки
    _normalize_street()  — срезание префиксов улицы + пунктуация
    _normalize_house()   — корпус / дробь / литера

Это чистые unit-тесты: не требуют БД и резолверов. Сервис создаётся с
заглушечными (None) зависимостями, т.к. методы нормализации их не используют.

ВАЖНО про префиксы улиц: тесты базируются на РЕАЛЬНОМ конфиге
``address_config.street_prefixes`` = ("ул", "улица", "пер", "переулок",
"пр", "проспект") и фактических regex-паттернах сервиса:

    STREET_TYPES_PATTERN  = \\b(переулок|проспект|улица|пер|ул|пр)(?=[.\\s])\\.?\\s*
    PUNCTUATION_PATTERN   = [.,"\\']

Префикс срезается ТОЛЬКО если за ним стоит точка/пробел (lookahead ``(?=[.\\s])``),
поэтому "первомайская" / голый "улица" не теряют корень.

Корпус/дробь/литера в _normalize_house обрабатываются кириллической "к" и
кириллическими литерами [а-я]; произвольные пробелы внутри номера НЕ удаляются.
"""

import pytest

from app.schemas.address import AddressInput, NormalizedAddressInput
from app.services.address.address_service import AddressService


# ---------------------------------------------------------------------------
# Фикстура: сервис без реальных зависимостей (нормализация их не использует)
# ---------------------------------------------------------------------------


@pytest.fixture
def normalization_service() -> AddressService:
    """НОВЫЙ AddressService с заглушечными зависимостями (без БД/резолверов)."""
    return AddressService(
        address_repo=None,
        context_resolver=None,
        street_resolver=None,
        house_resolver=None,
        landmark_resolver=None,
    )


# ---------------------------------------------------------------------------
# 1. _normalize_text()
# ---------------------------------------------------------------------------


class TestNormalizeText:
    @pytest.mark.parametrize(
        ("raw", "expected"),
        [
            # None / пусто
            (None, None),
            ("", None),
            ("   ", None),
            # пробелы
            (" Гагарина ", "гагарина"),
            ("  Гагарина   Северная ", "гагарина северная"),
            ("Ленина   Победы", "ленина победы"),
            # регистр
            ("ГАГАРИНА", "гагарина"),
            ("ГаГаРиНа", "гагарина"),
            # кавычки
            ('"Гагарина"', "гагарина"),
            ("'Гагарина'", "гагарина"),
            ('  "Гагарина"  ', "гагарина"),
            # только кавычки / пустые после снятия кавычек
            ('""', None),
            ("''", None),
            # одиночная кавычка: текущая логика её сохраняет (len < 2)
            ('"', '"'),
            ("'", "'"),
        ],
    )
    def test_normalize_text(
        self, normalization_service: AddressService, raw: str | None, expected
    ) -> None:
        assert normalization_service._normalize_text(raw) == expected


# ---------------------------------------------------------------------------
# 2. _normalize_street()
# ---------------------------------------------------------------------------


class TestNormalizeStreet:
    @pytest.mark.parametrize(
        ("raw", "expected"),
        [
            # None / пусто
            (None, None),
            ("", None),
            ("   ", None),
            # регистр и пробелы
            ("ГАГАРИНА", "гагарина"),
            ("  Гагарина  ", "гагарина"),
            ("Гагарина    Северная", "гагарина северная"),
            # префиксы, реально поддерживаемые address_config.street_prefixes
            ("ул. Гагарина", "гагарина"),
            ("улица Гагарина", "гагарина"),
            ("пер. Ленина", "ленина"),
            ("переулок Ленина", "ленина"),
            ("пр. Ленина", "ленина"),
            ("проспект Ленина", "ленина"),
            # префикс без точки (space после префикса тоже подходит под lookahead)
            ("пр Победы", "победы"),
            # префикс НЕ срезается без разделителя: lookahead (?=[.\\s])
            ("Первомайская", "первомайская"),
            # голый префикс без разделителя сохраняется как есть
            ("улица", "улица"),
            ("пр", "пр"),
            # пунктуация из PUNCTUATION_PATTERN [.,"\\'] удаляется
            ('"Гагарина"', "гагарина"),
            ("ул. Гагарина,", "гагарина"),
        ],
    )
    def test_normalize_street(
        self, normalization_service: AddressService, raw: str | None, expected
    ) -> None:
        assert normalization_service._normalize_street(raw) == expected

# ---------------------------------------------------------------------------
# 3. _normalize_house()
# ---------------------------------------------------------------------------


class TestNormalizeHouse:
    @pytest.mark.parametrize(
        ("raw", "expected"),
        [
            # None / пусто
            (None, None),
            ("", None),
            ("   ", None),
            ('""', None),
            # обычные номера
            ("12", "12"),
            (" 12 ", "12"),
            ('"12"', "12"),
            ("'12'", "12"),
            # регистр
            ("12А", "12а"),
            ("10К2", "10к2"),
            # корпус (кириллическая "к")
            ("10к2", "10к2"),
            ("10к 2", "10к2"),
            ("10 к2", "10к2"),
            ("10 к 2", "10к2"),
            ("10 К 2", "10к2"),
            # дробь
            ("127/1", "127/1"),
            ("127 /1", "127/1"),
            ("127/ 1", "127/1"),
            ("127 / 1", "127/1"),
            # литера
            ("33а", "33а"),
            ("33 а", "33а"),
            ("33 А", "33а"),
            # НЕ-нормализуемые пробелы сохраняются (бизнес-правил нет!)
            ("12 3", "12 3"),
            # латинская "k" не распознаётся как корпус (паттерн — кириллическая "к")
            ("10 k 2", "10 k 2"),
        ],
    )
    def test_normalize_house(
        self, normalization_service: AddressService, raw: str | None, expected
    ) -> None:
        assert normalization_service._normalize_house(raw) == expected

# ---------------------------------------------------------------------------
# 4. _normalize_input() — интеграция
# ---------------------------------------------------------------------------


class TestNormalizeInput:
    @pytest.mark.parametrize(
        ("raw", "expected"),
        [
            # Сценарий 1: пробелы по краям
            (
                {
                    "town": " Москва ",
                    "district": " Восточный ",
                    "street": " ул. Гагарина ",
                    "house": " 10 к 2 ",
                    "landmark": None,
                },
                {
                    "town": "москва",
                    "district": "восточный",
                    "street": "гагарина",
                    "house": "10к2",
                    "landmark": None,
                },
            ),
            # Сценарий 2: uppercase + префикс + дробь
            (
                {
                    "town": "МОСКВА",
                    "district": "ЦЕНТРАЛЬНЫЙ",
                    "street": "УЛИЦА ЛЕНИНА",
                    "house": "127 / 1",
                    "landmark": None,
                },
                {
                    "town": "москва",
                    "district": "центральный",
                    "street": "ленина",
                    "house": "127/1",
                    "landmark": None,
                },
            ),
            # Сценарий 3: только street + house + landmark
            (
                {
                    "town": None,
                    "district": None,
                    "street": " Гагарина ",
                    "house": "33 а",
                    "landmark": " Больница ",
                },
                {
                    "town": None,
                    "district": None,
                    "street": "гагарина",
                    "house": "33а",
                    "landmark": "больница",
                },
            ),
            # Сценарий 4: все поля None
            ({}, {}),
            # Сценарий 5: кавычки + пробелы + регистр одновременно
            (
                {
                    "town": '  "МОСКВА"  ',
                    "district": " 'ВОСТОЧНЫЙ' ",
                    "street": ' УЛ. "ГАГАРИНА" ',
                    "house": ' "10 К 2" ',
                    "landmark": " ' БОЛЬНИЦА № 1 ' ",
                },
                {
                    "town": "москва",
                    "district": "восточный",
                    "street": "гагарина",
                    "house": "10к2",
                    "landmark": "больница № 1",
                },
            ),
        ],
    )
    def test_normalize_input(
        self, normalization_service: AddressService, raw: dict, expected: dict
    ) -> None:
        result = normalization_service._normalize_input(AddressInput(**raw))

        assert isinstance(result, NormalizedAddressInput)
        assert result == NormalizedAddressInput(**expected)

    def test_normalize_input_routes_fields_to_correct_normalizers(
        self, normalization_service: AddressService, monkeypatch
    ) -> None:
        """Проверяет, что каждое поле маршрутизируется на свой нормализатор:

            town -> _normalize_text
            district -> _normalize_text
            street -> _normalize_street
            house -> _normalize_house
            landmark -> _normalize_text

        Заменяем методы на шпионы, которые НЕ вызывают реальную реализацию
        (иначе _normalize_house сам бы дёргал _normalize_text, и список вызовов
        был бы замусорен). Шпионы возвращают маркеры, по которым видно,
        какой метод применился к какому полю.
        """
        calls: dict[str, list] = {
            "_normalize_text": [],
            "_normalize_street": [],
            "_normalize_house": [],
        }

        for name in calls:
            def _spy(value, _name=name):
                calls[_name].append(value)
                return f"{_name}:{value}"

            monkeypatch.setattr(normalization_service, name, _spy)

        result = normalization_service._normalize_input(
            AddressInput(
                town="Москва",
                district="Восточный",
                street="ул. Гагарина",
                house="10 к 2",
                landmark="Больница",
            )
        )

        # town/district/landmark -> _normalize_text (в порядке вызова)
        assert calls["_normalize_text"] == ["Москва", "Восточный", "Больница"]
        # street -> _normalize_street
        assert calls["_normalize_street"] == ["ул. Гагарина"]
        # house -> _normalize_house
        assert calls["_normalize_house"] == ["10 к 2"]

        # Результат собран из маркеров: поле обработано тем методом, что ожидалось.
        assert result == NormalizedAddressInput(
            town="_normalize_text:Москва",
            district="_normalize_text:Восточный",
            street="_normalize_street:ул. Гагарина",
            house="_normalize_house:10 к 2",
            landmark="_normalize_text:Больница",
        )
