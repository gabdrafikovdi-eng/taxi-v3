from app.core.exceptions import InvalidTransitionError
from app.models.order import OrderState
from app.models.order import Order

ALLOWED_TRANSITIONS: dict[OrderState, set[OrderState]] = {
    OrderState.DRAFT: {OrderState.CONFIRMED, OrderState.CANCELLED},
    OrderState.CONFIRMED: {OrderState.COMPLETED, OrderState.CANCELLED},
    OrderState.COMPLETED: set(),
    OrderState.CANCELLED: set(),
}


class StateService:
    def transition(self, order: Order, target_state: OrderState) -> None:
        if target_state not in ALLOWED_TRANSITIONS[order.state]:
            raise InvalidTransitionError(
                from_state=order.state,
                to_state=target_state,
                reason="Переход запрещен матрицей",
            )
        self._check_guards(order=order, target_state=target_state)

        order.state = target_state

    def _check_guards(self, order: Order, target_state: OrderState) -> None:
        if target_state == OrderState.CONFIRMED and not order.can_confirm:
            raise InvalidTransitionError(
                from_state=order.state,
                to_state=target_state,
                reason="Нет обоих адресов и не рассчитана цена поездки(price)",
            )

        if target_state == OrderState.COMPLETED and not order.is_active:
            raise InvalidTransitionError(
                from_state=order.state,
                to_state=target_state,
                reason="Заказ уже не активен",
            )
        if target_state == OrderState.CANCELLED and not order.is_active:
            raise InvalidTransitionError(
                from_state=order.state,
                to_state=target_state,
                reason="Заказ уже не активен",
            )
