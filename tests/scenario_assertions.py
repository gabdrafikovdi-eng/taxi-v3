"""Предикаты для assertion-строк сценариев.

Каждый сценарий из ``docs/test_case_address.json`` может содержать
человекочитаемое поле ``assertion``. Так как assertion — это свободный
текст, он сопоставляется с реестром предикатов по ключевым словам.

Если assertion не распознан ни одним предикатом — тест получает FAIL
с сообщением ``unhandled assertion`` (молчаливое игнорирование запрещено).
"""

from __future__ import annotations

from app.schemas.address import AddressCandidate, AddressInput, AddressMatchResult, AddressStatus
from app.services.address.house_number_parser import parse_house_number

# Стандартный лимит suggestions (AddressService.suggest_house(limit=3)).
DEFAULT_SUGGESTION_LIMIT = 3


# ---------------------------------------------------------------------------
# Вспомогательные функции
# ---------------------------------------------------------------------------


async def _repeat_resolve(service, scenario) -> AddressMatchResult:
    """Повторный вызов AddressService для проверки детерминизма."""
    return await service.resolve_address(AddressInput(**scenario["input"]))


async def _resolved_street_names(service, scenario) -> set[str]:
    """Канонические имена улиц, в которые резолвится вход (без поиска дома)."""
    address = AddressInput(**scenario["input"])
    normalized = service._normalize_input(address)  # noqa: SLF001
    if not normalized.street:
        return set()

    context = await service.context_resolver.resolve(
        town_name=normalized.town,
        district_name=normalized.district,
    )
    if context is None:
        return set()

    streets = await service.street_resolver.resolve(
        district_ids=context.district_ids,
        name=normalized.street,
    )
    return {match.street.name for match in streets}


def _requested_parts(scenario) -> object | None:
    return parse_house_number(scenario["input"].get("house") or "")


class AssertionPredicate:
    """Один предикат: матчится по ключевым словам и проверяет результат."""

    def __init__(self, run, *keywords: str):
        self._run = run
        self.keywords = [keyword.lower() for keyword in keywords]

    def matches(self, assertion_lower: str) -> bool:
        return any(keyword in assertion_lower for keyword in self.keywords)

    async def __call__(self, scenario, result, service):
        await self._run(scenario, result, service)


# ---------------------------------------------------------------------------
# Реестр предикатов
# ---------------------------------------------------------------------------


async def _pred_null_values(scenario, result, service):
    for suggestion in result.suggestions:
        assert suggestion.house_id is not None
        assert suggestion.house_number is not None


async def _pred_pydantic_schema(scenario, result, service):
    for suggestion in result.suggestions:
        assert isinstance(suggestion, AddressCandidate)
        dumped = suggestion.model_dump()
        assert dumped["house_id"] is not None
        assert dumped["street_id"] is not None


async def _pred_valid_house_ids(scenario, result, service):
    for suggestion in result.suggestions:
        assert isinstance(suggestion.house_id, int)
        assert suggestion.house_id is not None


async def _pred_same_town(scenario, result, service):
    assert len({s.town_id for s in result.suggestions}) <= 1


async def _pred_same_district(scenario, result, service):
    assert len({s.district_id for s in result.suggestions}) <= 1


async def _pred_deterministic(scenario, result, service):
    again = await _repeat_resolve(service, scenario)
    assert again.status is result.status
    assert [s.house_id for s in again.suggestions] == [s.house_id for s in result.suggestions]
    assert [s.house_number for s in again.suggestions] == [s.house_number for s in result.suggestions]


async def _pred_limit_default(scenario, result, service):
    assert len(result.suggestions) <= DEFAULT_SUGGESTION_LIMIT


async def _pred_no_duplicate_ids(scenario, result, service):
    ids = [s.house_id for s in result.suggestions]
    assert len(ids) == len(set(ids))


async def _pred_no_duplicate_numbers(scenario, result, service):
    numbers = [s.house_number for s in result.suggestions]
    assert len(numbers) == len(set(numbers))


async def _pred_no_numeric_proximity(scenario, result, service):
    requested = _requested_parts(scenario)
    if requested is None:
        return
    for suggestion in result.suggestions:
        parts = parse_house_number(suggestion.house_number or "")
        assert parts is not None
        assert parts.base == requested.base, (
            f"suggestion {suggestion.house_number!r} base {parts.base!r} "
            f"!= requested base {requested.base!r}"
        )


async def _pred_structure(scenario, result, service):
    """Все suggestions сохраняют структуру номера (letter/corpus/fraction)."""
    requested = _requested_parts(scenario)
    if requested is None:
        assert result.suggestions == [], (
            "unparseable requested house must not produce suggestions"
        )
        return
    for suggestion in result.suggestions:
        parts = parse_house_number(suggestion.house_number or "")
        assert parts is not None
        assert parts.type is requested.type, (
            f"suggestion {suggestion.house_number!r} type {parts.type.value!r} "
            f"!= requested type {requested.type.value!r}"
        )


async def _pred_exact_no_suggestions(scenario, result, service):
    if result.status in (AddressStatus.RESOLVED, AddressStatus.AMBIGUOUS):
        assert result.suggestions == [], (
            "exact/ambiguous address must return no suggestions"
        )


async def _pred_status_not_changed(scenario, result, service):
    assert result.status is AddressStatus.NOT_FOUND, (
        "suggestions must not change NOT_FOUND to RESOLVED"
    )


async def _pred_real_houses(scenario, result, service):
    for suggestion in result.suggestions:
        assert suggestion.house_id is not None, (
            "suggestion must reference a real house"
        )


async def _pred_exact_not_in_suggestions(scenario, result, service):
    requested = scenario["input"].get("house")
    if not requested:
        return
    expected = requested.strip().lower()
    for suggestion in result.suggestions:
        assert suggestion.house_number.lower() != expected, (
            f"exact house {requested!r} must not appear among suggestions"
        )


async def _pred_street_restricted(scenario, result, service):
    street_ids = {s.street_id for s in result.suggestions}
    assert len(street_ids) <= 1, (
        "suggestions must be restricted to a single resolved street"
    )


async def _pred_district_context(scenario, result, service):
    street_ids = {s.street_id for s in result.suggestions}
    assert len(street_ids) <= 1
    if result.suggestions:
        district_ids = {s.district_id for s in result.suggestions}
        assert len(district_ids) == 1


async def _pred_town_context(scenario, result, service):
    if result.suggestions:
        town_ids = {s.town_id for s in result.suggestions}
        assert len(town_ids) == 1


async def _pred_limit_n(scenario, result, service):
    limit = scenario.get("suggestions_limit") or DEFAULT_SUGGESTION_LIMIT
    assert len(result.suggestions) <= limit


async def _pred_empty_when_no_compatible(scenario, result, service):
    assert result.suggestions == []


async def _pred_not_found_empty_valid(scenario, result, service):
    assert result.status is AddressStatus.NOT_FOUND
    assert result.suggestions == []


async def _pred_normalization_before(scenario, result, service):
    assert result.status is AddressStatus.NOT_FOUND
    resolved = await _resolved_street_names(service, scenario)
    for suggestion in result.suggestions:
        assert suggestion.street_name in resolved


async def _pred_fuzzy_before(scenario, result, service):
    resolved = await _resolved_street_names(service, scenario)
    assert resolved, "street must resolve (not raw) before suggestions"
    for suggestion in result.suggestions:
        assert suggestion.street_name in resolved



async def _pred_ambiguous_no_suggestions(scenario, result, service):
    resolved = await _resolved_street_names(service, scenario)
    if len(resolved) > 1:
        assert result.suggestions == [], (
            "must not generate suggestions from an arbitrary street"
        )


async def _pred_district_disambiguates(scenario, result, service):
    street_ids = {s.street_id for s in result.suggestions}
    assert len(street_ids) <= 1


async def _pred_landmark_no_suggestions(scenario, result, service):
    assert result.suggestions == [], (
        "landmark flow must not generate house suggestions"
    )


async def _pred_verify_interaction(scenario, result, service):
    again = await _repeat_resolve(service, scenario)
    assert again.status is result.status
    assert [c.house_id for c in again.candidates] == [c.house_id for c in result.candidates]


async def _pred_house_resolver_no_null(scenario, result, service):
    for candidate in result.candidates:
        assert candidate.house_id is not None, (
            "HouseResolver must not create candidate with house_id=None"
        )


async def _pred_not_mixed(scenario, result, service):
    if result.suggestions:
        assert result.candidates == [], (
            "suggestions must not be mixed with resolved candidates"
        )


async def _pred_structurally_valid(scenario, result, service):
    assert isinstance(result, AddressMatchResult)
    assert result.status is AddressStatus.NOT_FOUND
    # Pydantic-валидность: модель обязана корректно сериализоваться.
    _ = result.model_dump()


async def _pred_no_null_house_candidate(scenario, result, service):
    for candidate in result.candidates:
        assert candidate.house_id is not None
        assert candidate.house_number


async def _pred_incomplete_prefix(scenario, result, service):
    assert result.status in (AddressStatus.NOT_FOUND, AddressStatus.INCOMPLETE)
    assert result.suggestions == []
    again = await _repeat_resolve(service, scenario)
    assert again.status is result.status


async def _pred_only_existing_variants(scenario, result, service):
    requested = _requested_parts(scenario)
    for suggestion in result.suggestions:
        parts = parse_house_number(suggestion.house_number or "")
        assert parts is not None
        if requested is not None:
            assert parts.type is requested.type


async def _pred_compatible_variants(scenario, result, service):
    requested = _requested_parts(scenario)
    if requested is None:
        return
    for suggestion in result.suggestions:
        parts = parse_house_number(suggestion.house_number or "")
        assert parts is not None
        assert parts.base == requested.base


async def _pred_use_resolved_street_not_raw(scenario, result, service):
    resolved = await _resolved_street_names(service, scenario)
    assert resolved, "street must be resolved to canonical name"
    for suggestion in result.suggestions:
        assert suggestion.street_name in resolved


# ---------------------------------------------------------------------------
# Реестр
# ---------------------------------------------------------------------------

ASSERTION_PREDICATES: list[AssertionPredicate] = [
    AssertionPredicate(_pred_null_values, "must not contain null values"),
    AssertionPredicate(_pred_pydantic_schema, "satisfy the expected pydantic schema"),
    AssertionPredicate(_pred_valid_house_ids, "contain valid house identifiers"),
    AssertionPredicate(_pred_same_town, "same resolved town"),
    AssertionPredicate(_pred_same_district, "same resolved district"),
    AssertionPredicate(
        _pred_deterministic,
        "ordering must be deterministic",
        "twice with identical input must produce identical suggestions",
    ),
    AssertionPredicate(_pred_limit_default, "must not exceed configured default limit"),
    AssertionPredicate(
        _pred_no_duplicate_ids,
        "must not include duplicate house ids",
        "duplicate houses must not occur",
    ),
    AssertionPredicate(
        _pred_no_duplicate_numbers,
        "must not include duplicate house numbers",
    ),
    AssertionPredicate(
        _pred_no_numeric_proximity,
        "must not use generic numeric proximity",
        "unrelated numeric neighbors",
        "numeric distance is small",
    ),
    AssertionPredicate(
        _pred_structure,
        "must preserve corpus structure",
        "must preserve fraction structure",
        "must preserve letter structure",
        "must respect corpus structure",
        "must respect fraction structure",
        "not confused with corpus matching",
        "not confused with fraction matching",
        "not confused with letter matching",
        "preserve the requested house-number structure",
        "must not include 33а, 33б or 33/1 unless house-number matching rules explicitly allow",
        "must not include 33к variants",
    ),
    AssertionPredicate(
        _pred_exact_no_suggestions,
        "exact house must return no suggestions",
        "must be evaluated before suggestions",
        "must not be called for an exact house",
    ),
    AssertionPredicate(
        _pred_status_not_changed,
        "must not change status to resolved",
        "only after exact house lookup fails",
    ),
    AssertionPredicate(
        _pred_real_houses,
        "only real houses with non-null house_id",
    ),
    AssertionPredicate(
        _pred_exact_not_in_suggestions,
        "exact house must not appear among suggestions",
    ),
    AssertionPredicate(
        _pred_street_restricted,
        "restricted to resolved street",
        "belonging to the resolved street",
        "same street_id as the resolved street",
        "on another street must never appear",
        "must be searched on resolved street",
    ),
    AssertionPredicate(
        _pred_district_context,
        "from another district must never appear",
        "must respect district context",
    ),
    AssertionPredicate(
        _pred_town_context,
        "from another town must never appear",
        "must respect town context",
    ),
    AssertionPredicate(
        _pred_limit_n,
        "number of suggestions must be <=",
        "return all matching suggestions when fewer than limit exist",
    ),
    AssertionPredicate(
        _pred_empty_when_no_compatible,
        "when no compatible house exists suggestions must be",
    ),
    AssertionPredicate(
        _pred_not_found_empty_valid,
        "not_found with empty suggestions must remain valid",
    ),
    AssertionPredicate(
        _pred_normalization_before,
        "normalization must happen before suggestion search",
        "case normalization must not break suggestions",
        "street type normalization must not break suggestions",
    ),


    AssertionPredicate(
        _pred_fuzzy_before,
        "fuzzy street resolution must occur before house suggestions",
        "fuzzy street resolution must resolve",
    ),
    AssertionPredicate(
        _pred_ambiguous_no_suggestions,
        "if street is ambiguous, do not generate suggestions from an arbitrary street",
    ),
    AssertionPredicate(
        _pred_district_disambiguates,
        "district disambiguates street before suggestions",
    ),
    AssertionPredicate(
        _pred_landmark_no_suggestions,
        "house suggestions must not be generated without a resolved street context",
        "landmark-to-street resolution before house suggestion generation",
    ),
    AssertionPredicate(
        _pred_verify_interaction,
        "verify interaction between landmark resolution and explicit street/house",
    ),
    AssertionPredicate(
        _pred_house_resolver_no_null,
        "must not create addresscandidate with house_id=none",
    ),
    AssertionPredicate(
        _pred_not_mixed,
        "must not be mixed with resolved candidates",
    ),
    AssertionPredicate(
        _pred_structurally_valid,
        "must remain structurally valid when suggestions are present",
    ),
    AssertionPredicate(
        _pred_no_null_house_candidate,
        "must contain no candidate with unresolved or null house",
    ),
    AssertionPredicate(
        _pred_incomplete_prefix,
        "verify behavior for incomplete corpus house-number prefix",
        "verify behavior for incomplete fraction house-number prefix",
    ),
    AssertionPredicate(
        _pred_only_existing_variants,
        "letter suggestions must use only existing",
        "corpus suggestions must use only existing",
        "generated only if 13а is absent and compatible alternatives exist",
    ),
    AssertionPredicate(
        _pred_compatible_variants,
        "suggestions may contain compatible",
    ),
    AssertionPredicate(
        _pred_use_resolved_street_not_raw,
        "rather than the raw misspelled street",
        "must use the resolved street rather than raw input",
    ),
]


async def run_assertions(scenario: dict, result, service) -> None:
    """Применяет к результату все предикаты, соответствующие assertion сценария."""
    assertion = scenario.get("assertion")
    if not assertion:
        return

    assertion_lower = assertion.lower()
    matched = [pred for pred in ASSERTION_PREDICATES if pred.matches(assertion_lower)]

    assert matched, (
        f"[{scenario['id']}] unhandled assertion: {assertion!r} "
        "(нет предиката в tests/scenario_assertions.py)"
    )

    for pred in matched:
        await pred(scenario, result, service)

