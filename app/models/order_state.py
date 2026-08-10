from enum import StrEnum


class OrderState(StrEnum):
    DRAFT = "draft"  # Заказ в процессе сбора данных
    CONFIRMED = "confirmed"  # Пользователь подтвердил
    SEARCHING = "searghing"  # Поиск водителя
    ASSIGNED = "assigned"  # Водитель назначен
    IN_PROGRESS = "in_progress"  # В процессе выполнения
    COMPLETED = "completed"  # Заказ завершён успешно
    CANCELLED = "cancelled"  # Заказ отменён

ACTIVE_ORDER_STATES: frozenset[OrderState] = frozenset({
    OrderState.DRAFT,
    OrderState.CONFIRMED,
    OrderState.SEARCHING,
    OrderState.ASSIGNED,
    OrderState.IN_PROGRESS,
})