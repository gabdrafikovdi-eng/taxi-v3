class DispatcherError(Exception):
    def __init__(self, message: str, *, code: str | None = None):
        self.message = message
        self.code = code
        super().__init__(message)


class InvalidTransitionError(DispatcherError):
    """Переход между состояниями заказа запрещён."""

    def __init__(
        self,
        from_state: str,
        to_state: str,
        reason: str | None = None,
    ) -> None:
        self.from_state = from_state
        self.to_state = to_state
        self.reason = reason

        message = f"Переход {from_state} → {to_state} запрещён"
        if reason is not None:
            message += f": {reason}"

        super().__init__(message, code="INVALID_TRANSITION")


class OrderNotFoundError(DispatcherError):
    def __init__(self, order_id: str):
        self.order_id = order_id
        message = f"Заказ не найден по order_id: {order_id}"
        super().__init__(message, code="ORDER_NOT_FOUND")


class TooManyActiveOrdersError(DispatcherError):
    def __init__(self, max_allowed):
        self.max_allowed = max_allowed
        message = "Лимит активных заказов исчерпан"
        if max_allowed:
            message += f"Максимальное допустимо {max_allowed}"
        super().__init__(message, code="TOO_MANY_ACTIVE_ORDERS")


class AddressValidationError(DispatcherError):
    def __init__(self, address_text, reason):
        self.address_text = address_text
        self.reason = reason
        message = f"Адрес: {address_text}, не прошел валидацию."
        if reason is not None:
            message += f" Причина: {reason}"

        super().__init__(message, code="ADDRESS_VALIDATION")


class InvalidStateError(DispatcherError):
    def __init__(self, order_id, current_state, attemted_action):
        self.order_id = order_id
        self.current_state = current_state
        self.attemted_action = attemted_action
        message = (
            f"Операция недопустима в текущем состоянии заказа. "
            f"order_id - {order_id}, current_state - {current_state}, attemted_action - {attemted_action}"
        )

        super().__init__(message, code="INVALID_STATE")


class PricingError(DispatcherError):
    def __init__(self, reason):
        self.reason = reason
        message = "Ошибка расчёта цены."
        if reason is not None:
            message += f" reason - {reason}"
        super().__init__(message, code="PRICING_ERROR")
