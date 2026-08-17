import re
from app.schemas.address import HouseNumberParts, HouseNumberType


_PATTERN_FRACTION = re.compile(r"^(\d+)/(\d+)$")  # например, 33/1
_PATTERN_CORPUS = re.compile(r"^(\d+)к(\d+)$")  # 33к2
_PATTERN_LETTER = re.compile(r"^(\d+)([а-я])$")  # 33а re.compile(r"^(\d+)([а-я])$")
_PATTERN_PLAIN = re.compile(r"^\d+$")  # 33


def parse_house_number(value: str) -> HouseNumberParts | None:
    if not value:
        return None

    normalized = value.strip().lower()
    if not normalized:
        return None

    match = _PATTERN_FRACTION.match(normalized)
    if match:
        return HouseNumberParts(
            base=match.group(1), type=HouseNumberType.FRACTION, suffix=match.group(2)
        )

    match = _PATTERN_CORPUS.match(normalized)
    if match:
        return HouseNumberParts(
            base=match.group(1), type=HouseNumberType.CORPUS, suffix=match.group(2)
        )

    match = _PATTERN_LETTER.match(normalized)
    if match:
        suffix = match.group(2)
        if suffix != "к":
            return HouseNumberParts(
                base=match.group(1), type=HouseNumberType.LETTER, suffix=match.group(2)
            )

    if _PATTERN_PLAIN.match(normalized):
        return HouseNumberParts(
            base=normalized, type=HouseNumberType.PLAIN, suffix=None
        )

    return None
