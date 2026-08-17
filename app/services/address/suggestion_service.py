from app.repositories.address_repo import AddressRepository
from app.schemas.address import AddressCandidate


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

        ВАЖНО:

        suggestions никогда не являются автоматически
        разрешённым адресом.

        Например:

            пользователь: Гагарина 2
            БД:          Гагарина 2а

        результат:

            suggestion = Гагарина 2а

        Но статус основного resolver остаётся NOT_FOUND.
        """

        houses = await self.address_repo.find_house_suggestions(
            street_id=street_id,
            number=house_number,
            limit=limit,
        )

        return [self._build_candidate(house) for house in houses]

    def _build_candidate(
        self,
        house,
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
