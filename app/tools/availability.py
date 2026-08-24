# app/tools/availability.py
from uuid import UUID

from app.repositories.order_repo import OrderRepository


class OrderToolAvailability:
    """Определяет, какие инструменты доступны для текущего звонка."""

    def __init__(self, order_repo: OrderRepository) -> None:
        self._repo = order_repo

    async def available_names(self, call_session_id: UUID) -> set[str]:
        """Возвращает множество имён доступных инструментов."""
        names: set[str] = {"list_orders", "get_order"}

        incomplete_draft = await self._repo.get_incomplete_draft(call_session_id)
        active_orders = await self._repo.get_active_orders_by_call_session(
            call_session_id
        )

        # Если нет незавершённого DRAFT — можно создать новый заказ
        if incomplete_draft is None:
            names.add("create_order")
        else:
            # Если есть незавершённый DRAFT — можно заполнять адреса и поля
            names.update(
                {
                    "set_pickup",
                    "set_destination",
                    "set_passenger_name",
                    "set_comment",
                    "add_waypoint",
                    "update_waypoint",
                    "remove_waypoint",
                }
            )

        # Если есть заказ, который можно подтвердить
        if any(order.can_confirm for order in active_orders):
            names.add("confirm_order")

        # Если есть активный заказ — можно отменить
        if any(order.is_active for order in active_orders):
            names.add("cancel_order")

        return names
