import re

from app.core.config import address_config
from app.repositories.address_repo import AddressRepository
from app.schemas.address import (
    AddressCandidate,
    AddressInput,
    AddressMatchResult,
    AddressStatus,
    NormalizedAddressInput,
)
from app.services.address.context_resolver import ContextResolver
from app.services.address.house_resolver import HouseResolver
from app.services.address.landmark_resolver import LandmarkResolver
from app.services.address.street_resolver import StreetResolver
from app.services.address.suggestion_service import AddressSuggestionService


class AddressService:
    def __init__(
        self,
        address_repo: AddressRepository,
        context_resolver: ContextResolver,
        street_resolver: StreetResolver,
        house_resolver: HouseResolver,
        landmark_resolver: LandmarkResolver,
        address_suggestion_service: AddressSuggestionService,
    ):
        self.address_repo = address_repo
        self.context_resolver = context_resolver
        self.street_resolver = street_resolver
        self.house_resolver = house_resolver
        self.landmark_resolver = landmark_resolver
        self.address_suggestion_service = address_suggestion_service

        self.address_config = address_config
        # Префиксы улицы ("улица", "ул", "переулок", "пер", "проспект", "пр")
        # срезаются ТОЛЬКО если за ними стоит точка/пробел (.|пер. Садовая),
        # иначе "первомайская" не должна терять свой корень "пер".
        # Длинные префиксы перебираются раньше коротких ("улица" до "ул").
        _prefixes = sorted(self.address_config.street_prefixes, key=len, reverse=True)
        self.STREET_TYPES_PATTERN = re.compile(
            r"\b(" + "|".join(_prefixes) + r")(?=[.\s])\.?\s*",
            flags=re.IGNORECASE,
        )
        self.PUNCTUATION_PATTERN = re.compile(r'[.,"\']')

    async def resolve_address(
        self,
        address: AddressInput,
    ) -> AddressMatchResult:
        """
        Главный orchestration method.

        Бизнес-правило:

            street + house
            ИЛИ
            landmark

        Только RESOLVED может попасть в OrderService.
        """

        data = self._normalize_input(address)

        # ----------------------------------------
        # 1. LANDMARK FLOW
        # ----------------------------------------

        if data.landmark:
            return await self._resolve_by_landmark(data)

        # ----------------------------------------
        # 2. STREET + HOUSE FLOW
        # ----------------------------------------

        if not data.street or not data.house:
            return AddressMatchResult(
                status=AddressStatus.INCOMPLETE,
                reason="street_and_house_or_landmark",
            )

        return await self._resolve_by_street_and_house(data)

    async def _resolve_by_street_and_house(
        self,
        data: NormalizedAddressInput,
    ) -> AddressMatchResult:
        """
        Алгоритм:

        Context
          ↓
        Street
          ↓
        House
          ↓
        finalize
        """

        context = await self.context_resolver.resolve(
            town_name=data.town,
            district_name=data.district,
        )

        if context is None:
            return AddressMatchResult(
                status=AddressStatus.NOT_FOUND,
                reason="town_or_district_not_found",
            )

        streets = await self.street_resolver.resolve(
            district_ids=context.district_ids,
            name=data.street,
        )

        if not streets:
            return AddressMatchResult(
                status=AddressStatus.NOT_FOUND,
                reason="street_not_found",
            )

        candidates = await self.house_resolver.resolve(
            streets=streets,
            house_number=data.house,
        )

        if candidates:
            return self._finalize_candidates(
                candidates=candidates,
                not_found_reason="house_not_found",
            )
        if len(streets) != 1:
            return self._finalize_candidates(
                candidates=candidates, not_found_reason="house_not_found"
            )

        street_id = streets[0].street.id

        suggestions = await self.address_suggestion_service.suggest_house(
            street_id=street_id, house_number=data.house, limit=3
        )

        return AddressMatchResult(
            status=AddressStatus.NOT_FOUND,
            reason="house_not_found",
            suggestions=suggestions,
        )

    async def _resolve_by_landmark(
        self,
        data: NormalizedAddressInput,
    ) -> AddressMatchResult:
        """
        Алгоритм:

        Context
          ↓
        Landmark
          ↓
        finalize
        """

        context = await self.context_resolver.resolve(
            town_name=data.town,
            district_name=data.district,
        )

        if context is None:
            return AddressMatchResult(
                status=AddressStatus.NOT_FOUND,
                reason="town_or_district_not_found",
            )

        candidates = await self.landmark_resolver.resolve(
            district_ids=context.district_ids,
            name=data.landmark,
        )

        return self._finalize_candidates(
            candidates=candidates,
            not_found_reason="landmark_not_found",
        )

    def _finalize_candidates(
        self,
        candidates: list[AddressCandidate],
        not_found_reason: str,
    ) -> AddressMatchResult:
        """
        Финальное бизнес-решение.

        0 кандидатов:
            NOT_FOUND

        1 кандидат:
            RESOLVED

        2+ кандидатов:
            AMBIGUOUS
        """

        if not candidates:
            return AddressMatchResult(
                status=AddressStatus.NOT_FOUND,
                reason=not_found_reason,
            )

        if len(candidates) == 1:
            return AddressMatchResult(
                status=AddressStatus.RESOLVED,
                candidates=candidates,
            )

        candidates = sorted(
            candidates,
            key=lambda candidate: candidate.score,
            reverse=True,
        )

        candidates = candidates[:3]

        candidates = self._enrich_candidates_with_diff(candidates)

        return AddressMatchResult(
            status=AddressStatus.AMBIGUOUS,
            candidates=candidates,
        )

    def _enrich_candidates_with_diff(
        self,
        candidates: list[AddressCandidate],
    ):
        """
        Добавляет информацию, чем отличаются
        неоднозначные кандидаты.

        Например:

            район Восточный
            район Центральный
        """

        if len(candidates) < 2:
            return candidates

        towns = {candidate.town_name for candidate in candidates}

        districts = {candidate.district_name for candidate in candidates}

        enriched = []

        for candidate in candidates:
            diff_feature = None

            if len(towns) > 1:
                diff_feature = f"г. {candidate.town_name}"

            elif len(districts) > 1:
                diff_feature = f"район {candidate.district_name}"

            enriched.append(candidate.model_copy(update={"diff_feature": diff_feature}))

        return enriched

    def _normalize_input(
        self,
        address: AddressInput,
    ):
        """
        Нормализация входа.

        Здесь можно перенести твои текущие методы
        _normalize_text / _normalize_street / _normalize_house.
        """

        from app.schemas.address import NormalizedAddressInput

        return NormalizedAddressInput(
            town=self._normalize_text(address.town),
            district=self._normalize_text(address.district),
            street=self._normalize_street(address.street),
            house=self._normalize_house(address.house),
            landmark=self._normalize_text(address.landmark),
        )

    def _normalize_street(
        self,
        value: str | None,
    ) -> str | None:
        if value is None:
            return None

        value = value.lower().strip()

        # Срезаем префиксы типа улицы ("ул.", "улица", "пер.", "пр.", ...),
        # знаки препинания и схлопываем пробелы (реализация перенесена из
        # старого app/services/address_service.py).
        value = self.STREET_TYPES_PATTERN.sub("", value)
        value = self.PUNCTUATION_PATTERN.sub("", value)
        value = " ".join(value.split())

        return value or None

    def _normalize_house(
        self,
        value: str | None,
    ) -> str | None:
        value = self._normalize_text(value)

        if value is None:
            return None

        # return value.strip("\"'")

        # корпус
        value = re.sub(r"\s*к\s*", "к", value)
        # дробь
        value = re.sub(r"\s*/\s*", "/", value)
        # литера
        value = re.sub(r"(\d)\s+([а-я])$", r"\1\2", value)

        return value

    def _normalize_text(
        self,
        value: str | None,
    ) -> str | None:
        if value is None:
            return None

        value = value.strip().lower()
        value = " ".join(value.split())

        if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
            value = value[1:-1].strip()

        return value or None
