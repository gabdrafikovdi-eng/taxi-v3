import pytest
from app.services.address.house_number_parser import (
    parse_house_number,
    HouseNumberParts,
    HouseNumberType,
)


class TestHouseNumberParser:
    """Тесты для разбора номера дома."""

    @pytest.mark.parametrize(
        "input_str, expected_base, expected_type, expected_suffix",
        [
            # PLAIN
            ("33", "33", HouseNumberType.PLAIN, None),
            ("1", "1", HouseNumberType.PLAIN, None),
            ("999", "999", HouseNumberType.PLAIN, None),
            # LETTER
            ("33а", "33", HouseNumberType.LETTER, "а"),
            ("33б", "33", HouseNumberType.LETTER, "б"),
            ("10в", "10", HouseNumberType.LETTER, "в"),
            ("4а", "4", HouseNumberType.LETTER, "а"),
            # CORPUS
            ("33к1", "33", HouseNumberType.CORPUS, "1"),
            ("33к2", "33", HouseNumberType.CORPUS, "2"),
            ("14к1", "14", HouseNumberType.CORPUS, "1"),
            ("52к1", "52", HouseNumberType.CORPUS, "1"),
            # FRACTION
            ("33/1", "33", HouseNumberType.FRACTION, "1"),
            ("127/1", "127", HouseNumberType.FRACTION, "1"),
            ("10/1", "10", HouseNumberType.FRACTION, "1"),
            ("14/2", "14", HouseNumberType.FRACTION, "2"),
        ],
    )
    def test_valid_parsing(self, input_str, expected_base, expected_type, expected_suffix):
        result = parse_house_number(input_str)
        assert result is not None
        assert result.base == expected_base
        assert result.type == expected_type
        assert result.suffix == expected_suffix

    @pytest.mark.parametrize(
        "invalid_input",
        [
            "",          # пустая строка
            None,        # None
            "abc",       # буквы без цифр
            "к2",        # корпус без цифр перед "к"
            "/1",        # дробь без числителя
            "33/",       # дробь без знаменателя
            "33к",       # корпус без цифр после "к"
            "33аа",      # две буквы
            "33к12к",    # невалидный корпус
            "33/1/",     # лишний слеш
            "33-1",      # дефис – не поддерживается
        ],
    )
    def test_invalid_parsing(self, invalid_input):
        result = parse_house_number(invalid_input)
        assert result is None

    def test_case_insensitive(self):
        # Функция приводит к нижнему регистру, так что "33А" должно стать "33а"
        result = parse_house_number("33А")
        assert result is not None
        assert result.type == HouseNumberType.LETTER
        assert result.suffix == "а"

    def test_whitespace_handling(self):
        result = parse_house_number("  33/1  ")
        assert result is not None
        assert result.base == "33"
        assert result.type == HouseNumberType.FRACTION
        assert result.suffix == "1"