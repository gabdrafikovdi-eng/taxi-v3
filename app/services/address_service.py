import re
from typing import Any

from app.models.address import Street, Town
from app.repositories.address_repo import AddressRepository
from app.core.config import address_config
from app.schemas.address import (
    AddressCandidate,
    AddressInput,
    AddressMatchResult,
    AddressStatus,
    MatchType,
    NormalizedAddressInput,
)


class AddressService:
    def __init__(self, address_repo: AddressRepository):
        self.address_repo = address_repo
        self.address_config = address_config
        self.STREET_TYPES_PATTERN = re.compile(
            r"\b(" + "|".join(self.address_config.street_prefixes) + r")\.?\s*",
            flags=re.IGNORECASE,
        )
        self.PUNCTUATION_PATTERN = re.compile(r'[.,"\']')
        self.DIGITS_PATTERN = re.compile(r"\d+")  # Шаблон для извлечения цифр из строки

    async def resolve_address(self, input_address: AddressInput) -> AddressMatchResult:
        input_data: NormalizedAddressInput = self._normalize_input(input_address)

        town_name = input_data.town or self.address_config.default_town_name

        town = await self.address_repo.get_town_by_name(town_name)

        if town is None:
            return AddressMatchResult(
                status=AddressStatus.NOT_FOUND, reason="town_not_found"
            )

        district_ids: list[int] = []

        if input_data.district:
            district = await self.address_repo.get_district_by_name(
                town.id, input_data.district
            )

            if district is None:
                return AddressMatchResult(
                    status=AddressStatus.NOT_FOUND, reason="district_not_found"
                )
            district_ids = [district.id]

        # Если пользователь передал район — district_ids уже содержит ТОЛЬКО его id,
        # и перезаписывать его списком всех районов нельзя. Иначе берём все районы города.
        if not district_ids:
            district_ids = await self.address_repo.get_district_ids_by_town(town.id)

        if not district_ids:
            return AddressMatchResult(
                status=AddressStatus.NOT_FOUND, reason="no_districts_in_town"
            )

        if input_data.street:
            raw_candidates = await self._search_by_street(
                district_ids=district_ids,
                street_name=input_data.street,
                house_number=input_data.house,
                landmark_name=input_data.landmark,
            )
            if not raw_candidates:
                return AddressMatchResult(
                    status=AddressStatus.NOT_FOUND, reason="street_not_found"
                )

        elif input_data.landmark:
            raw_candidates = await self._search_by_landmark(
                district_ids=district_ids, landmark_name=input_data.landmark
            )
            if not raw_candidates:
                return AddressMatchResult(
                    status=AddressStatus.NOT_FOUND, reason="landmark_not_found"
                )

        else:
            return AddressMatchResult(
                status=AddressStatus.NOT_FOUND, reason="address_and_landmark_not_found"
            )

        return self._process_candidates(candidates=raw_candidates)

    async def _search_by_street(
        self,
        district_ids: list[int],
        street_name: str | None,
        house_number: str | None,
        landmark_name: str | None,
    ) -> list[AddressCandidate]:
        """Поиск улицы: EXACT -> SYNONYM -> FUZZY + Дома и Ориентиры."""
        streets = []
        matched_items: list[tuple[Street, float]] = []

        match_type = MatchType.EXACT
        streets = await self.address_repo.find_streets_exact(
            districts_ids=district_ids, name=street_name
        )
        if streets:
            matched_items = [(s, 1.0) for s in streets]

        if not matched_items:
            match_type = MatchType.SYNONYM
            streets = await self.address_repo.find_streets_by_synonyms(
                districts_ids=district_ids, name=street_name
            )
            if streets:
                matched_items = [(s, 1.0) for s in streets]

        if not matched_items:
            match_type = MatchType.FUZZY
            matched_items = await self.address_repo.find_street_fuzzy(
                district_ids=district_ids,
                name=street_name,
                threshold=self.address_config.fuzzy_threshold,
                limit=self.address_config.max_candidates,
            )

        if not matched_items:
            return []

        candidates: list[AddressCandidate] = []
        user_digits = self.DIGITS_PATTERN.findall(street_name)

        for street, sim_score in matched_items:
            base_score = (
                1.0 if match_type in (MatchType.EXACT, MatchType.SYNONYM) else sim_score
            )

            db_digits = self.DIGITS_PATTERN.findall(street.name)

            if user_digits and db_digits:
                if user_digits != db_digits:
                    base_score -= 0.30
                else:
                    base_score += -0.10

            house = None

            if house_number:
                house = await self.address_repo.find_house(
                    street_id=street.id, number=house_number
                )

                base_score += 0.10 if house else -0.15

            landmark = None

            if landmark_name:
                landmark_matches = await self.address_repo.find_landmark_by_street(
                    street_id=street.id, name=landmark_name
                )
                base_score += 0.10 if landmark_matches else -0.20

            score = min(max(base_score, 0.0), 1.0)

            candidates.append(
                self._build_candidate(
                    street=street, house=house, landmark=landmark, score=score
                )
            )
        return candidates

    async def _search_by_landmark(
        self, district_ids: list[int], landmark_name: str
    ) -> list[AddressCandidate]:
        landmark = await self.address_repo.find_landmarks(
            district_ids=district_ids, name=landmark_name
        )
        candidates: list[AddressCandidate] = []

        for lm in landmark:
            candidates.append(
                self._build_candidate(
                    street=lm.street, house=lm.house, landmark=lm, score=0.9
                )
            )

        return candidates

    def _process_candidates(
        self, candidates: list[AddressCandidate]
    ) -> AddressMatchResult:
        """Сортировка, отсечение хвоста и генерация итогового статуса."""
        if not candidates:
            return AddressMatchResult(
                status=AddressStatus.NOT_FOUND,
                reason="candidate_not_found",
            )

        candidates_with_house = [c for c in candidates if c.house_id is not None]

        if candidates_with_house:
            candidates = candidates_with_house

        sorted_cadidates = sorted(candidates, key=lambda c: c.score, reverse=True)

        valid_candidates = [c for c in sorted_cadidates if c.score >= 0.25]

        if not valid_candidates:
            return AddressMatchResult(
                status=AddressStatus.NOT_FOUND,
                reason="low_confidence",
            )

        if len(valid_candidates) == 1:
            return AddressMatchResult(
                status=AddressStatus.RESOLVED, candidates=[valid_candidates[0]]
            )

        first = valid_candidates[0]
        second = valid_candidates[1]

        if first.score >= 0.80 and (first.score - second.score) >= 0.15:
            return AddressMatchResult(status=AddressStatus.RESOLVED, candidates=[first])

        if (first.score - second.score) >= 0.25:
            return AddressMatchResult(status=AddressStatus.RESOLVED, candidates=[first])

        # 6. В остальных случаях действительно есть неоднозначность
        top_candidates = valid_candidates[:3]
        enriched_candidates = self._enrich_candidates_with_diff(top_candidates)
        return AddressMatchResult(
            status=AddressStatus.AMBIGUOUS, candidates=enriched_candidates
        )

        # # 1. Сортируем по весу (score) от большего к меньшему
        # sorted_candidates = sorted(candidates, key=lambda c: c.score, reverse=True)

        # # 2. Оставляем только топ-3 варианта
        # top_candidates = sorted_candidates[:3]

        # # 3. Если главный кандидат имеет высокий скор и сильно оторвался от второго
        # first = top_candidates[0]
        # if first.score >= 0.8 and (
        #     len(top_candidates) == 1 or (first.score - top_candidates[1].score) >= 0.3
        # ):
        #     return AddressMatchResult(status=AddressStatus.RESOLVED, candidates=[first])

        # # 4. Если есть 2-3 близких кандидата -> обогащаем diff_feature и просим уточнить
        # enriched_candidates = self._enrich_candidates_with_diff(top_candidates)
        # return AddressMatchResult(
        #     status=AddressStatus.AMBIGUOUS, candidates=enriched_candidates
        # )

    def _enrich_candidates_with_diff(
        self, candidates: list[AddressCandidate]
    ) -> list[AddressCandidate]:
        """Вычисляет главные отличия (diff_feature) между спорными кандидатами."""
        if len(candidates) < 2:
            return candidates

        towns = {c.town_name for c in candidates}
        districts = {c.district_name for c in candidates}

        enriched = []
        for c in candidates:
            diff = None
            if len(towns) > 1:
                diff = f"г. {c.town_name}"
            elif len(districts) > 1:
                diff = f"район {c.district_name}"

            # Создаем копию кандидата с обновленным полем diff_feature
            enriched.append(c.model_copy(update={"diff_feature": diff}))

        return enriched

    def _build_candidate(
        self,
        street: Any,
        house: Any | None = None,
        landmark: Any | None = None,
        score: float = 1.0,
    ) -> AddressCandidate:
        """Вспомогательный билдер из ORM-моделей в Pydantic."""
        district = street.district
        town = district.town

        # Формируем читаемую строку
        parts = [f"ул. {street.name}"]
        if house:
            parts.append(f"д. {house.number}")
        if landmark:
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
            landmark_id=landmark.id if landmark else None,
            landmark_name=landmark.name if landmark else None,
            full_address=", ".join(parts),
            score=score,
        )

    def _normalize_input(self, address_raw: AddressInput) -> NormalizedAddressInput:
        return NormalizedAddressInput(
            town=self._normalize_text(address_raw.town),
            district=self._normalize_text(address_raw.district),
            street=self._normalize_street(address_raw.street),
            house=self._normalize_house(address_raw.house),
            landmark=self._normalize_text(address_raw.landmark),
        )

    def _normalize_street(self, value: str | None) -> str | None:
        if value is None:
            return None

        value = value.lower().strip()
        value = self.STREET_TYPES_PATTERN.sub("", value)
        value = self.PUNCTUATION_PATTERN.sub("", value)
        value = " ".join(value.split())

        return value

    def _normalize_house(self, value: str | None) -> str | None:
        value = self._normalize_text(value)

        if value is None:
            return None

        return value.strip("\"'")

    def _normalize_text(self, value: str | None) -> str | None:
        """Приводит строку к каноническому виду: lower, trim, схлопывает пробелы.

        Убирает лишние пробелы по краям и внутри, приводит к нижнему регистру
        (поиск в БД также регистронезависим), снимает обрамляющие кавычки.
        """
        if value is None:
            return None

        val = value.strip().lower()
        # Схлопывает повторяющиеся пробелы/табуляции.
        val = " ".join(val.split())

        if len(val) >= 2 and val[0] == val[-1] and val[0] in "\"'":
            val = val[1:-1].strip()

        return val or None
