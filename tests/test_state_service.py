"""Тесты сервиса переходов состояний заказа (StateService).

Уровень: unit/service. Внешних зависимостей нет — сервис работает
с SQLAlchemy-моделью Order как с обычным объектом.
"""

import pytest

from app.core.exceptions import InvalidTransitionError
from app.models.order import Order, OrderState
from app.services.state_service import StateService


@pytest.fixture
def service() -> StateService:
    return StateService()


@pytest.fixture
def order_with_one_address() -> Order:
    """Заказ в DRAFT только с одним адресом."""
    order = Order(state=OrderState.DRAFT)
    order.pickup_street_id = 1
    return order


class TestSuccessfulTransitions:
    """Разрешённые матрицей переходы с выполненными guard'ами."""

    def test_transition_draft_to_confirmed_updates_state(
        self, service: StateService, confirmable_order: Order
    ) -> None:
        service.transition(confirmable_order, OrderState.CONFIRMED)

        assert confirmable_order.state is OrderState.CONFIRMED

    def test_transition_draft_to_cancelled_updates_state(
        self, service: StateService, draft_order: Order
    ) -> None:
        service.transition(draft_order, OrderState.CANCELLED)

        assert draft_order.state is OrderState.CANCELLED

    def test_transition_confirmed_to_completed_updates_state(
        self, service: StateService, confirmed_order: Order
    ) -> None:
        service.transition(confirmed_order, OrderState.COMPLETED)

        assert confirmed_order.state is OrderState.COMPLETED

    def test_transition_confirmed_to_cancelled_updates_state(
        self, service: StateService, confirmed_order: Order
    ) -> None:
        service.transition(confirmed_order, OrderState.CANCELLED)

        assert confirmed_order.state is OrderState.CANCELLED


class TestForbiddenByTransitionMatrix:
    """Переходы, не входящие в матрицу разрешённых переходов."""

    @pytest.mark.parametrize(
        ("from_state", "to_state"),
        [
            (OrderState.DRAFT, OrderState.COMPLETED),
            (OrderState.CONFIRMED, OrderState.DRAFT),
            (OrderState.COMPLETED, OrderState.DRAFT),
            (OrderState.COMPLETED, OrderState.CONFIRMED),
            (OrderState.COMPLETED, OrderState.COMPLETED),
            (OrderState.COMPLETED, OrderState.CANCELLED),
            (OrderState.CANCELLED, OrderState.DRAFT),
            (OrderState.CANCELLED, OrderState.CONFIRMED),
            (OrderState.CANCELLED, OrderState.COMPLETED),
            (OrderState.CANCELLED, OrderState.CANCELLED),
        ],
    )
    def test_transition_forbidden_by_matrix_raises_invalid_transition(
        self,
        service: StateService,
        from_state: OrderState,
        to_state: OrderState,
    ) -> None:
        order = Order(state=from_state)

        with pytest.raises(InvalidTransitionError) as exc_info:
            service.transition(order, to_state)

        assert exc_info.value.code == "INVALID_TRANSITION"
        assert exc_info.value.from_state == from_state
        assert exc_info.value.to_state == to_state
        assert order.state is from_state

    def test_transition_on_terminal_states_always_raises(
        self, service: StateService, completed_order: Order, cancelled_order: Order
    ) -> None:
        """COMPLETED и CANCELLED — терминальные состояния: любой переход невозможен."""
        for order in (completed_order, cancelled_order):
            with pytest.raises(InvalidTransitionError):
                service.transition(order, OrderState.CANCELLED)
            with pytest.raises(InvalidTransitionError):
                service.transition(order, OrderState.COMPLETED)


class TestGuardsForConfirmation:
    """Guard подтверждения: оба адреса и рассчитанная цена."""

    def test_transition_draft_to_confirmed_without_addresses_raises(
        self, service: StateService, draft_order: Order
    ) -> None:
        with pytest.raises(InvalidTransitionError) as exc_info:
            service.transition(draft_order, OrderState.CONFIRMED)

        assert exc_info.value.reason == (
            "Нет обоих адресов и не рассчитана цена поездки(price)"
        )
        assert draft_order.state is OrderState.DRAFT

    def test_transition_draft_to_confirmed_with_partial_addresses_raises(
        self, service: StateService, order_with_one_address: Order
    ) -> None:
        with pytest.raises(InvalidTransitionError):
            service.transition(order_with_one_address, OrderState.CONFIRMED)

        assert order_with_one_address.state is OrderState.DRAFT

    def test_transition_draft_to_confirmed_without_price_raises(
        self, service: StateService
    ) -> None:
        order = Order(state=OrderState.DRAFT)
        order.pickup_street_id = 1
        order.destination_street_id = 2

        with pytest.raises(InvalidTransitionError):
            service.transition(order, OrderState.CONFIRMED)

        assert order.state is OrderState.DRAFT

    def test_transition_draft_to_confirmed_with_zero_price_raises(
        self, service: StateService
    ) -> None:
        """Цена 0 не считается рассчитанной (is_priced требует price > 0)."""
        order = Order(state=OrderState.DRAFT)
        order.pickup_street_id = 1
        order.destination_street_id = 2
        order.price = 0

        with pytest.raises(InvalidTransitionError):
            service.transition(order, OrderState.CONFIRMED)

        assert order.state is OrderState.DRAFT


class TestSideEffects:
    """Побочные эффекты: состояние меняется только при успешном переходе."""

    def test_transition_error_does_not_change_order_state(
        self, service: StateService, draft_order: Order
    ) -> None:
        service.transition(draft_order, OrderState.CANCELLED)
        assert draft_order.state is OrderState.CANCELLED

        # Повторный переход из терминального состояния запрещён,
        # и состояние не должно измениться.
        with pytest.raises(InvalidTransitionError):
            service.transition(draft_order, OrderState.CONFIRMED)

        assert draft_order.state is OrderState.CANCELLED

    def test_successful_transition_is_the_only_state_mutation(
        self, service: StateService, confirmable_order: Order
    ) -> None:
        before = confirmable_order.state

        service.transition(confirmable_order, OrderState.CONFIRMED)

        assert before is OrderState.DRAFT
        assert confirmable_order.state is OrderState.CONFIRMED
        # Другие поля не должны затрагиваться переходом.
        assert confirmable_order.price == 500
        assert confirmable_order.pickup_street_id == 1
        assert confirmable_order.destination_street_id == 2