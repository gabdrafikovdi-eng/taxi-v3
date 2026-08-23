from typing import Self

from pydantic import BaseModel
from pydantic.config import ConfigDict


class ToolResult(BaseModel):
    model_config = ConfigDict(frozen=True)

    success: bool
    message: str
    code: str | None = None
    data: dict[str, object] | None = None

    @classmethod
    def ok(
        cls,
        message: str,
        *,
        code: str | None = None,
        data: dict[str, object] | None = None,
    ) -> Self:
        return cls(success=True, message=message, code=code, data=data)

    @classmethod
    def fail(
        cls,
        message: str,
        *,
        code: str | None = None,
        data: dict[str, object] | None = None,
    ) -> Self:
        return cls(success=False, message=message, code=code, data=data)
