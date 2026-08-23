from enum import StrEnum
from typing import Any

from pydantic import BaseModel


class ToolStatus(StrEnum):
    SUCCESS = "success"
    ERROR = "error"
    

class ToolResult(BaseModel):
    status: ToolStatus
    message: str
    code: str | None = None
    data: Any | None = None

