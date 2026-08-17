from app.repositories.address_repo import AddressRepository
from app.schemas.address import MatchType, StreetMatch


class StreetResolver:
    def __init__(
        self,
        address_repo: AddressRepository,
        fuzzy_threshold: float,
        max_candidate: int,
    ):
        self.address_repo = address_repo
        self.fuzzy_threshold = fuzzy_threshold
        self.max_candidate = max_candidate

    async def resolve(self, district_ids: list[int], name: str) -> list[StreetMatch]:
        exact_matches = await self._find_exact(
            district_ids=district_ids, name=name
        )

        if exact_matches:
            return exact_matches

        synonym_matches = await self._find_synonyms(
            district_ids=district_ids, name=name
        )

        if synonym_matches:
            return synonym_matches

        return await self._find_fuzzy(
            district_ids=district_ids, name=name
        )

    async def _find_exact(
        self, district_ids: list[int], name: str
    ) -> list[StreetMatch]:
        streets = await self.address_repo.find_streets_exact(
            districts_ids=district_ids, name=name
        )

        return [
            StreetMatch(street=street, score=1.0, match_type=MatchType.EXACT)
            for street in streets
        ]

    async def _find_synonyms(
        self, district_ids: list[int], name: str
    ) -> list[StreetMatch]:
        streets = await self.address_repo.find_streets_by_synonyms(
            districts_ids=district_ids, name=name
        )
        return [
            StreetMatch(street=street, score=1.0, match_type=MatchType.SYNONYM)
            for street in streets
        ]

    async def _find_fuzzy(
        self, district_ids: list[int], name: str
    ) -> list[StreetMatch]:
        matches = await self.address_repo.find_street_fuzzy(
            district_ids=district_ids,
            name=name,
            threshold=self.fuzzy_threshold,
            limit=self.max_candidate,
        )
        return [
            StreetMatch(street=street, score=score, match_type=MatchType.FUZZY)
            for street, score in matches
        ]
