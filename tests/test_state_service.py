import pytest

from app.core.exceptions import InvalidTransitionError
from app.models.order import Order, OrderState
from app.services.state_service import StateService


def make_order(
    *,
    state: OrderState = OrderState.DRAFT,
    pickup_street_id: int | None = 1,
    destination_street_id: int | None = 2,
    price: int | None = 100,
) -> Order:
    """Создаёт заказ с заданными параметрами без обращения к БД."""
    order = Order(
        call_session_id=1,
        pickup_street_id=pickup_street_id,
        destination_street_id=destination_street_id,
        price=price,
    )
    order.state = state
    return order


class TestStateServiceTransitions:
    """Тесты матрицы переходов."""

    def test_draft_to_confirmed(self):
        order = make_order()
        StateService().transition(order, OrderState.CONFIRMED)
        assert order.state == OrderState.CONFIRMED

    def test_draft_to_cancelled(self):
        order = make_order()
        StateService().transition(order, OrderState.CANCELLED)
        assert order.state == OrderState.CANCELLED

    def test_confirmed_to_completed(self):
        order = make_order(state=OrderState.CONFIRMED)
        StateService().transition(order, OrderState.COMPLETED)
        assert order.state == OrderState.COMPLETED

    def test_confirmed_to_cancelled(self):
        order = make_order(state=OrderState.CONFIRMED)
        StateService().transition(order, OrderState.CANCELLED)
        assert order.state == OrderState.CANCELLED

    @pytest.mark.parametrize(
        ("from_state", "to_state"),
        [
            (OrderState.DRAFT, OrderState.COMPLETED),
            (OrderState.CONFIRMED, OrderState.DRAFT),
            (OrderState.COMPLETED, OrderState.DRAFT),
            (OrderState.COMPLETED, OrderState.CONFIRMED),
            (OrderState.COMPLETED, OrderState.CANCELLED),
            (OrderState.CANCELLED, OrderState.DRAFT),
            (OrderState.CANCELLED, OrderState.CONFIRMED),
            (OrderState.CANCELLED, OrderState.COMPLETED),
        ],
    )
    def test_forbidden_transitions_raise(self, from_state, to_state):
        order = make_order(state=from_state)
        with pytest.raises(InvalidTransitionError) as exc_info:
            StateService().transition(order, to_state)

        assert exc_info.value.from_state == from_state
        assert exc_info.value.to_state == to_state
        assert order.state == from_state  # состояние не изменилось


class TestStateServiceGuards:
    """Тесты guard-условий."""

    def test_confirm_requires_both_addresses(self):
        order = make_order(pickup_street_id=None)
        with pytest.raises(InvalidTransitionError) as exc_info:
            StateService().transition(order, OrderState.CONFIRMED)

        assert "адресов" in exc_info.value.reason
        assert order.state == OrderState.DRAFT

    def test_confirm_requires_price(self):
        order = make_order(price=None)
        with pytest.raises(InvalidTransitionError) as exc_info:
            StateService().transition(order, OrderState.CONFIRMED)

        assert "price" in exc_info.value.reason
        assert order.state == OrderState.DRAFT

    def test_confirm_requires_positive_price(self):
        order = make_order(price=0)
        with pytest.raises(InvalidTransitionError):
            StateService().transition(order, OrderState.CONFIRMED)
