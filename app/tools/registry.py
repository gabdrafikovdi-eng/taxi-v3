
import logging
from collections.abc import Mapping
from uuid import UUID

from app.tools.base import Tool, ToolContext, ToolDefinition, ToolResult
from app.tools.errors import error_to_tool_result

logger = logging.getLogger(__name__)


class ToolRegistry:
    """Реестр инструментов. Хранит, отдаёт описания, выполняет."""

    def __init__(self, tools: list[Tool]) -> None:
        self._tools = {tool.name: tool for tool in tools}

    def definitions(self, available_names: set[str]) -> list[ToolDefinition]:
        """Возвращает описания доступных инструментов для модели."""
        return [
            tool.definition
            for tool in self._tools.values()
            if tool.name in available_names
        ]

    def openai_tools(self, available_names: set[str]) -> list[dict[str, object]]:
        """Возвращает описания в формате OpenAI function calling."""
        return [
            {
                "type": "function",
                "function": {
                    "name": definition.name,
                    "description": definition.description,
                    "parameters": definition.parameters,
                },
            }
            for definition in self.definitions(available_names)
        ]

    async def execute(
        self,
        name: str,
        ctx: ToolContext,
        arguments: Mapping[str, object],
    ) -> ToolResult:
        """Выполняет инструмент по имени."""
        tool = self._tools.get(name)

        if tool is None:
            return ToolResult(
                success=False,
                message=f"Неизвестный инструмент: {name}",
                code="UNKNOWN_TOOL",
            )

        try:
            return await tool.execute(ctx, arguments)
        except Exception as exc:
            logger.exception("Tool execution failed: %s", name)
            return error_to_tool_result(exc)
