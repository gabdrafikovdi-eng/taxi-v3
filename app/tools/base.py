from abc import ABC, abstractmethod
from typing import Any, ClassVar
from collections.abc import Mapping
from uuid import UUID

from pydantic import BaseModel
from pydantic.config import ConfigDict


class ToolContext(BaseModel):
    model_config = ConfigDict(frozen=True)

    call_session_id: UUID
    tool_call_id: str | None = None


class ToolResult(BaseModel):
    model_config = ConfigDict(frozen=True)

    success: bool
    message: str
    code: str | None = None
    data: dict[str, object] | None = None


class ToolDefinition(BaseModel):
    model_config = ConfigDict(frozen=True)

    name: str
    description: str
    parameters: dict[str, object]


class Tool(ABC):
    name: ClassVar[str]
    definition: ToolDefinition

    @abstractmethod
    async def execute(
        self, context: ToolContext, arguments: Mapping[str, object]
    ) -> ToolResult:
        raise NotImplementedError
