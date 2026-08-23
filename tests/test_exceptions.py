"""Unit-тесты контрактных кодов ошибок DispatcherError.

Коды (`DispatcherError.code`) уходят из tools в LLM, поэтому каждый код —
это часть контракта и должен быть стабильным и единообразным
(например, ``WAYPOINT_NOT_FOUND``, а не ``not_found_waypoint``).

Как запускать:
    .venv/bin/python -m pytest tests/test_exceptions.py -v
"""

from uuid import uuid4

import pytest

from app.core.exceptions import (
    AddressResolveError,
    AddressValidationError,
    DispatcherError,
    InvalidStateError,
    InvalidTransitionError,
    LimitWaypointError,
    OrderNotFoundError,
    PricingError,
    TooManyActiveOrdersError,
    WaypointNotFoundError,
)
from app.schemas.address import AddressStatus


@pytest.mark.parametrize(
    ("error", "expected_code"),
    [
        pytest.param(
            OrderNotFoundError(order_id="order-1"),
            "ORDER_NOT_FOUND",
            id="order-not-found",
        ),
        pytest.param(
            InvalidStateError(
                order_id="order-1",
                current_state="DRAFT",
                attemted_action="set_pickup",
            ),
            "INVALID_STATE",
            id="invalid-state",
        ),
        pytest.param(
            InvalidTransitionError(from_state="DRAFT", to_state="COMPLETED"),
            "INVALID_TRANSITION",
            id="invalid-transition",
        ),
        pytest.param(
            TooManyActiveOrdersError(max_allowed=1),
            "TOO_MANY_ACTIVE_ORDERS",
            id="too-many-active-orders",
        ),
        pytest.param(
            LimitWaypointError(current_waypoint_count=2, max_waypoint=1),
            "WAYPOINT_LIMIT_EXCEEDED",
            id="waypoint-limit-exceeded",
        ),
        pytest.param(
            WaypointNotFoundError(order_id=uuid4(), sequence_number=5),
            "WAYPOINT_NOT_FOUND",
            id="waypoint-not-found",
        ),
        pytest.param(
            PricingError(reason="нет тарифа"),
            "PRICING_ERROR",
            id="pricing-error",
        ),
        pytest.param(
            AddressValidationError(address_text="ул. Ленина", reason=None),
            "VALIDATION_ERROR",
            id="validation-error",
        ),
    ],
)
def test_error_codes(error: DispatcherError, expected_code: str) -> None:
    """Каждая бизнес-ошибка возвращает стабильный контрактный код."""
    assert error.code == expected_code


@pytest.mark.parametrize(
    ("status", "expected_code"),
    [
        pytest.param(AddressStatus.NOT_FOUND, "ADDRESS_NOT_FOUND", id="not-found"),
        pytest.param(AddressStatus.INCOMPLETE, "ADDRESS_INCOMPLETE", id="incomplete"),
        pytest.param(AddressStatus.AMBIGUOUS, "ADDRESS_AMBIGUOUS", id="ambiguous"),
    ],
)
def test_address_resolve_error_code(
    status: AddressStatus, expected_code: str
) -> None:
    """AddressResolveError не должен путать INCOMPLETE с AMBIGUOUS."""
    assert AddressResolveError(status=status).code == expected_code