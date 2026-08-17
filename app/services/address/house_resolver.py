from app.repositories.address_repo import AddressRepository

from app.schemas.address import AddressCandidate, StreetMatch


class HouseResolver:
    def __init__(
        self,
        address_repo: AddressRepository,
    ):
        self.address_repo = address_repo

    async def resolve(
        self,
        streets: list[StreetMatch],
        house_number: str,
    ) -> list[AddressCandidate]:
        """
        Для каждой найденной улицы ищет ТОЧНЫЙ номер дома.

        Важный инвариант:

            если house_number указан,
            AddressCandidate обязан иметь house_id.

        Дом, который не найден, НЕ становится кандидатом.
        """

        candidates: list[AddressCandidate] = []

        for street_match in streets:
            house = await self.address_repo.find_house(
                street_id=street_match.street.id,
                number=house_number,
            )

            if house is None:
                continue

            candidate = self._build_candidate(
                street_match=street_match,
                house=house,
            )

            candidates.append(candidate)

        return candidates

    def _build_candidate(
        self,
        street_match: StreetMatch,
        house,
    ) -> AddressCandidate:
        street = street_match.street
        district = street.district
        town = district.town

        full_address = f"ул. {street.name}, д. {house.number}, р-н {district.name}"

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
            full_address=full_address,
            score=street_match.score,
        )
