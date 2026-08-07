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
