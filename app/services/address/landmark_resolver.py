from app.repositories.address_repo import AddressRepository
from app.schemas.address import AddressCandidate


class LandmarkResolver:
    def __init__(
        self,
        address_repo: AddressRepository,
    ):
        self.address_repo = address_repo

    async def resolve(
        self,
        district_ids: list[int],
        name: str,
    ) -> list[AddressCandidate]:
        """
        Ищет landmark.

        0 результатов:
            пустой список

        1 результат:
            один AddressCandidate

        2+:
            несколько AddressCandidate

        Решение RESOLVED / AMBIGUOUS принимает
        верхний AddressService.
        """

        landmarks = await self.address_repo.find_landmarks(
            district_ids=district_ids,
            name=name,
        )

        candidates: list[AddressCandidate] = []

        for landmark in landmarks:
            candidate = self._build_candidate(landmark)
            candidates.append(candidate)

        return candidates

    def _build_candidate(
        self,
        landmark,
    ) -> AddressCandidate:
        street = landmark.street
        district = street.district
        town = district.town
        house = landmark.house

        parts = [
            f"ул. {street.name}",
        ]

        if house:
            parts.append(f"д. {house.number}")

        parts.append(f"({landmark.name})")
        parts.append(f"р-н {district.name}")

        return AddressCandidate(
            town_id=town.id,
            town_name=town.name,
            district_id=district.id,
            district_name=district.name,
            street_id=street.id,
            street_name=street.name,
            house_id=house.id if house else None,
            house_number=house.number if house else None,
            landmark_id=landmark.id,
            landmark_name=landmark.name,
            full_address=", ".join(parts),
            score=1.0,
        )
