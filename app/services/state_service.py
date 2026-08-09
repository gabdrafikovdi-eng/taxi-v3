from app.core.exceptions import InvalidTransitionError
from app.models.order import OrderState
from app.models.order import Order


ALLOWED_TRANSITIONS: dict[OrderState, set[OrderState]] = {
    OrderState.DRAFT: {OrderState.CONFIRMED, OrderState.CANCELLED},
    OrderState.CONFIRMED: {OrderState.SEARCHING, OrderState.CANCELLED},
    OrderState.SEARCHING: {OrderState.ASSIGNED, OrderState.CANCELLED},
    OrderState.ASSIGNED: {OrderState.IN_PROGRESS, OrderState.CANCELLED},
    OrderState.IN_PROGRESS: {OrderState.COMPLETED, OrderState.CANCELLED},
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
        """Проверяет бизнес-правила (guards) для перехода заказа в целевое состояние.

        Args:
            order (Order): Заказ, для которого проверяются правила.
            target_state (OrderState): Целевое состояние заказа.

        Raises:
            InvalidTransitionError: Если у заказа нет обоих адресов и не рассчитана
                цена поездки (price) — при переходе в статус CONFIRMED.
            InvalidTransitionError: Если заказ уже не активен — при переходе
                в статус SEARCHING.
            InvalidTransitionError: Если заказ уже не активен — при переходе
                в статус ASSIGNED.
            InvalidTransitionError: Если заказ уже не активен — при переходе
                в статус IN_PROGRESS.
            InvalidTransitionError: Если заказ уже не активен — при переходе
                в статус COMPLETED.
            InvalidTransitionError: Если заказ уже не активен — при переходе
                в статус CANCELLED.
        """
        match target_state:
            case OrderState.CONFIRMED if not order.can_confirm:
                raise InvalidTransitionError(
                    from_state=order.state,
                    to_state=target_state,
                    reason="Нет обоих адресов и не рассчитана цена поездки(price)",
                )
            case OrderState.SEARCHING if not order.is_active:
                raise InvalidTransitionError(
                    from_state=order.state,
                    to_state=target_state,
                    reason="Заказ уже не активен",
                )
            case OrderState.ASSIGNED if not order.is_active:
                raise InvalidTransitionError(
                    from_state=order.state,
                    to_state=target_state,
                    reason="Заказ уже не активен",
                )

            case OrderState.IN_PROGRESS if not order.is_active:
                raise InvalidTransitionError(
                    from_state=order.state,
                    to_state=target_state,
                    reason="Заказ уже не активен",
                )

            case OrderState.COMPLETED if not order.is_active:
                raise InvalidTransitionError(
                    from_state=order.state,
                    to_state=target_state,
                    reason="Заказ уже не активен",
                )

            case OrderState.CANCELLED if not order.is_active:
                raise InvalidTransitionError(
                    from_state=order.state,
                    to_state=target_state,
                    reason="Заказ уже не активен",
                )