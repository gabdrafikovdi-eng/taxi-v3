# app/tools/errors.py
import logging

from pydantic import ValidationError

from app.core.exceptions import AddressResolveError, DispatcherError
from app.tools.base import ToolResult

logger = logging.getLogger(__name__)


def error_to_tool_result(exc: Exception) -> ToolResult:
    if isinstance(exc, AddressResolveError):
        data: dict[str, object] | None = None

        if exc.candidates:
            data = {
                "candidates": [c.model_dump(mode="json") for c in exc.candidates],
            }
        elif exc.suggestions:
            data = {
                "suggestions": [s.model_dump(mode="json") for s in exc.suggestions],
            }

        return ToolResult(
            success=False,
            message=exc.message,
            code=exc.code,
            data=data,
        )

    if isinstance(exc, ValidationError):
        return ToolResult(
            success=False,
            message="Ошибка валидации входных данных.",
            code="VALIDATION_ERROR",
            data={"errors": exc.errors()},
        )

    if isinstance(exc, DispatcherError):
        return ToolResult(
            success=False,
            message=exc.message,
            code=exc.code,
        )

    logger.exception("Unexpected error in tool", exc_info=exc)
    return ToolResult(
        success=False,
        message="Внутренняя ошибка при выполнении действия.",
        code="INTERNAL_ERROR",
    )