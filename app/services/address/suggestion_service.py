from app.models.address import House
from app.repositories.address_repo import AddressRepository
from app.schemas.address import (
    AddressCandidate,
    HouseNumberParts,
    HouseNumberType,
)
from app.services.address.house_number_parser import parse_house_number


class AddressSuggestionService:
    def __init__(
        self,
        address_repo: AddressRepository,
    ):
        self.address_repo = address_repo

    async def suggest_house(
        self,
        street_id: int,
        house_number: str,
        limit: int = 3,
    ) -> list[AddressCandidate]:
        """
        Ищет похожие номера домов.

        Suggestions никогда не являются автоматически
        разрешённым адресом.

        Например:

            пользователь: Гагарина 2
            БД:          Гагарина 2а

        Результат:

            suggestion = Гагарина 2а

        Но статус основного resolver остаётся NOT_FOUND.
        """

        if limit <= 0:
            return []

        requested = parse_house_number(house_number)

        if requested is None:
            return []

        houses = await self.address_repo.get_houses_by_street_id(
            street_id=street_id,
        )

        suggestions: list[House] = []

        for house in houses:
            candidate = parse_house_number(house.number)

            if candidate is None:
                continue

            if not self._is_compatible(
                requested=requested,
                candidate=candidate,
            ):
                continue

            suggestions.append(house)

        suggestions = self._sort_suggestions(requested=requested, houses=suggestions)

        suggestions = suggestions[:limit]

        return [self._build_candidate(house) for house in suggestions]

    def _is_compatible(
        self,
        requested: HouseNumberParts,
        candidate: HouseNumberParts,
    ) -> bool:
        if requested.base != candidate.base:
            return False

        if requested.type is HouseNumberType.PLAIN:
            return candidate.type is not HouseNumberType.PLAIN

        if requested.type is HouseNumberType.LETTER:
            return candidate.type is HouseNumberType.LETTER

        if requested.type is HouseNumberType.CORPUS:
            return candidate.type is HouseNumberType.CORPUS

        if requested.type is HouseNumberType.FRACTION:
            return candidate.type is HouseNumberType.FRACTION

        return False

    def _build_candidate(
        self,
        house: House,
    ) -> AddressCandidate:
        street = house.street
        district = street.district
        town = district.town

        return AddressCandidate(
            town_id=town.id,
            town_name=town.name,
            district_id=district.id,
            district_name=district.name,
            street_id=street.id,
            street_name=street.name,
            house_id=house.id,
            house_number=house.number,
            landmark_id=None,
            landmark_name=None,
            full_address=(f"ул. {street.name}, д. {house.number}, р-н {district.name}"),
            score=0.0,
        )

    def _sort_suggestions(
        self,
        requested: HouseNumberParts,
        houses: list[House],
    ) -> list[House]:
        if requested.type is HouseNumberType.LETTER:
            return sorted(
                houses,
                key=lambda house: self._letter_sort_key(house),
            )

        if requested.type is HouseNumberType.CORPUS:
            return sorted(
                houses,
                key=lambda house: self._numeric_suffix_sort_key(house),
            )

        if requested.type is HouseNumberType.FRACTION:
            return sorted(
                houses,
                key=lambda house: self._numeric_suffix_sort_key(house),
            )

        if requested.type is HouseNumberType.PLAIN:
            return sorted(
                houses,
                key=self._plain_sort_key,
            )

        return houses

    def _letter_sort_key(
        self,
        house: House,
    ) -> str:
        parts = parse_house_number(house.number)

        if parts is None or parts.suffix is None:
            return ""

        return parts.suffix

    def _numeric_suffix_sort_key(
        self,
        house: House,
    ) -> int:
        parts = parse_house_number(house.number)

        if parts is None or parts.suffix is None:
            return 0

        return int(parts.suffix)

    def _plain_sort_key(
        self,
        house: House,
    ) -> tuple[int, int, str]:
        parts = parse_house_number(house.number)

        if parts is None:
            return (99, 0, house.number)

        type_order = {
            HouseNumberType.LETTER: 1,
            HouseNumberType.CORPUS: 2,
            HouseNumberType.FRACTION: 3,
            HouseNumberType.PLAIN: 4,
        }

        suffix_number = 0

        if parts.suffix and parts.suffix.isdigit():
            suffix_number = int(parts.suffix)

        return (
            type_order.get(parts.type, 99),
            suffix_number,
            house.number,
        )
