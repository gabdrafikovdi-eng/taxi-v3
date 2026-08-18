"""Проверки результата AddressService по полям сценария.

Каждый сценарий из ``docs/test_case_address.json`` может содержать поля:

    expected_status, expected_candidates, expected_suggestions,
    expected_suggestions_non_empty, expected_resolved_street,
    expected_street, expected_house, expected_suggestion_contains,
    expected_suggestion_excludes, suggestions_limit, suggestions_rule.

Все эти поля проверяются здесь единообразно и динамически (набор полей
определяется самим JSON-сценарием, а не захардкожен).
"""

from __future__ import annotations

from app.schemas.address import AddressMatchResult, AddressStatus
from app.services.address.house_number_parser import parse_house_number

# Статусы, у которых есть "уверенное" разрешение адреса (candidates непустые).
_RESOLVING_STATUSES = {AddressStatus.RESOLVED, AddressStatus.AMBIGUOUS}


def status_allows(expected: str, actual: AddressStatus) -> bool:
    """Проверяет, что фактический статус допустим для ожидаемого.

    Ожидаемый статус может быть комбинированным, например:
        NOT_FOUND_OR_RESOLVED
        AMBIGUOUS_OR_RESOLVED_ACCORDING_TO_DB
        RESOLVED_OR_NOT_FOUND_ACCORDING_TO_DISTRICT_FILTER

    Тест проходит, если фактический статус упомянут среди допустимых.
    """
    if not expected:
        return True

    expected_norm = expected.lower().replace("_", " ").replace("-", " ")
    actual_token = actual.value.lower().replace("_", " ")

    return actual_token in expected_norm


def _house_numbers(result: AddressMatchResult) -> list[str]:
    return [c.house_number for c in result.suggestions]


def check_scenario(scenario: dict, result: AddressMatchResult) -> None:
    """Применяет к результату все поля сценария, присутствующие в JSON."""
    sid = scenario["id"]

    # ------------------------------------------------------------- status
    expected_status = scenario.get("expected_status")
    if expected_status is not None:
        assert status_allows(expected_status, result.status), (
            f"[{sid}] expected_status={expected_status!r}, "
            f"actual={result.status.value!r}"
        )

    # ------------------------------------------------------ candidates
    expected_candidates = scenario.get("expected_candidates")
    if expected_candidates is not None:
        assert list(result.candidates) == expected_candidates, (
            f"[{sid}] expected_candidates={expected_candidates!r}, "
            f"actual={len(result.candidates)} candidates"
        )

    # ----------------------------------------------------- suggestions
    expected_suggestions = scenario.get("expected_suggestions")
    if expected_suggestions is not None:
        assert _house_numbers(result) == expected_suggestions, (
            f"[{sid}] expected_suggestions={expected_suggestions!r}, "
            f"actual={_house_numbers(result)!r}"
        )

    if scenario.get("expected_suggestions_non_empty") is True:
        assert result.suggestions, f"[{sid}] expected non-empty suggestions"

    # ------------------------------------- expected_resolved_street
    expected_resolved_street = scenario.get("expected_resolved_street")
    if expected_resolved_street is not None:
        assert result.status in _RESOLVING_STATUSES and result.candidates, (
            f"[{sid}] expected RESOLVED/AMBIGUOUS with candidates"
        )
        assert result.candidates[0].street_name == expected_resolved_street, (
            f"[{sid}] expected resolved street={expected_resolved_street!r}, "
            f"actual={result.candidates[0].street_name!r}"
        )

    # --------------------------------- expected_street / expected_house
    expected_street = scenario.get("expected_street")
    expected_house = scenario.get("expected_house")
    if expected_street is not None or expected_house is not None:
        # Проверяем, что среди кандидатов есть вариант с ожидаемой улицей/домом.
        # Работает и для RESOLVED (единственный кандидат обязан совпасть),
        # и для AMBIGUOUS (хотя бы один из вариантов совпадает).
        assert result.candidates, f"[{sid}] expected candidate with street/house"
        matches = [
            candidate
            for candidate in result.candidates
            if (expected_street is None or candidate.street_name == expected_street)
            and (expected_house is None or candidate.house_number == expected_house)
        ]
        assert matches, (
            f"[{sid}] expected candidate street={expected_street!r} "
            f"house={expected_house!r}; actual candidates: "
            + ", ".join(
                f"{c.street_name}/{c.house_number}" for c in result.candidates
            )
        )


def check_suggestions_rule(
    sid: str,
    scenario: dict,
    result: AddressMatchResult,
    rule: str,
) -> None:
    """Проверяет rule: все suggestions имеют base и структуру запрошенного дома."""
    requested = parse_house_number(scenario["input"].get("house") or "")
    if requested is None:
        return  # нечего сопоставлять (напр. "14к" — неполный префикс)

    rule_lower = rule.lower()

    for suggestion in result.suggestions:
        parts = parse_house_number(suggestion.house_number or "")
        assert parts is not None, (
            f"[{sid}] unparseable suggestion house {suggestion.house_number!r}"
        )
        # Базовый номер должен совпадать с запрошенным.
        assert parts.base == requested.base, (
            f"[{sid}] suggestion {suggestion.house_number!r} has base {parts.base!r}, "
            f"expected base {requested.base!r} per rule {rule!r}"
        )
        # Структура номера должна совпадать с заявленной в rule.
        expected_type = None
        if "letter" in rule_lower:
            expected_type = "letter"
        elif "corpus" in rule_lower and "к" in rule_lower:
            expected_type = "corpus"
        elif "fraction" in rule_lower or "/" in rule_lower:
            expected_type = "fraction"
        if expected_type is not None:
            assert parts.type.value == expected_type, (
                f"[{sid}] suggestion {suggestion.house_number!r} is {parts.type.value!r}, "
                f"expected {expected_type!r} per rule {rule!r}"
            )

            assert candidate.house_number == expected_house, (
                f"[{sid}] expected house={expected_house!r}, "
                f"actual={candidate.house_number!r}"
            )

    # ----------------------------------- expected_suggestion_contains
    contains = scenario.get("expected_suggestion_contains")
    if contains is not None:
        numbers = set(_house_numbers(result))
        for item in contains:
            assert item in numbers, (
                f"[{sid}] suggestion {item!r} must be present, "
                f"actual={sorted(numbers)!r}"
            )

    # ----------------------------------- expected_suggestion_excludes
    excludes = scenario.get("expected_suggestion_excludes")
    if excludes is not None:
        numbers = set(_house_numbers(result))
        for item in excludes:
            assert item not in numbers, (
                f"[{sid}] suggestion {item!r} must be absent, "
                f"actual={sorted(numbers)!r}"
            )

    # --------------------------------------------------- suggestions_limit
    limit = scenario.get("suggestions_limit")
    if limit is not None:
        assert len(result.suggestions) <= limit, (
            f"[{sid}] suggestions count {len(result.suggestions)} > limit {limit}"
        )

    # --------------------------------------------------- suggestions_rule
    rule = scenario.get("suggestions_rule")
    if rule is not None:
        check_suggestions_rule(sid, scenario, result, rule)
