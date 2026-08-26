# app/llm/conversation.py
import json
import logging
from typing import Any
from uuid import UUID

from app.llm.client import LLMClient
from app.repositories.message_repo import MessageRepository
from app.tools.base import ToolContext
from app.tools.registry import ToolRegistry
from app.tools.availability import OrderToolAvailability
from app.llm.system_promt import SYSTEM_PROMPT

logger = logging.getLogger(__name__)


class ConversationManager:
    def __init__(
        self,
        llm_client: LLMClient,
        tool_registry: ToolRegistry,
        tool_availability: OrderToolAvailability,
        message_repo: MessageRepository,
    ) -> None:
        self._llm = llm_client
        self._registry = tool_registry
        self._availability = tool_availability
        self._message_repo = message_repo
        # self._messages: list[dict] = [
        #     {"role": "system", "content": SYSTEM_PROMPT},
        # ]

    async def handle_message(
        self,
        user_message: str,
        call_session_id: UUID,
    ) -> str:
        self._messages.append({"role": "user", "content": user_message})

        logger.info("=" * 60)
        logger.info("ПОЛЬЗОВАТЕЛЬ: %s", user_message)

        max_iterations = 10
        for iteration in range(max_iterations):
            available_names = await self._availability.available_names(call_session_id)
            tools = self._registry.openai_tools(available_names)
            logger.info("Доступные инструменты: %s", available_names)

            logger.info("-" * 40)
            logger.info("ИТЕРАЦИЯ %d", iteration + 1)

            response = await self._llm.chat(
                self._messages, tools=tools if tools else None
            )

            # Если есть текст — финальный ответ
            if response.content:
                logger.info("ФИНАЛЬНЫЙ ОТВЕТ: %s", response.content)
                assistant_msg: dict[str, Any] = response.model_dump(exclude_none=True)
                self._messages.append(assistant_msg)
                return response.content

            # Если есть tool_calls
            if response.tool_calls:
                logger.info("МОДЕЛЬ ВЫЗЫВАЕТ ИНСТРУМЕНТЫ:")

                # Сохраняем ПОЛНЫЙ ответ модели
                assistant_msg = response.model_dump(exclude_none=True)
                self._messages.append(assistant_msg)

                # Выполняем каждый tool_call
                for tool_call in response.tool_calls:
                    logger.info("  Tool: %s", tool_call.function.name)
                    logger.info("  Args: %s", tool_call.function.arguments)

                    ctx = ToolContext(
                        call_session_id=call_session_id,
                        tool_call_id=tool_call.id,
                    )

                    try:
                        args = json.loads(tool_call.function.arguments)
                    except json.JSONDecodeError:
                        args = {}

                    result = await self._registry.execute(
                        name=tool_call.function.name,
                        ctx=ctx,
                        arguments=args,
                    )

                    logger.info(
                        "  Result: success=%s, code=%s", result.success, result.code
                    )
                    if result.data:
                        logger.info(
                            "  Data: %s",
                            json.dumps(result.data, ensure_ascii=False, indent=2),
                        )

                    self._messages.append(
                        {
                            "role": "tool",
                            "tool_call_id": tool_call.id,
                            "content": result.model_dump_json(),
                        }
                    )

        logger.warning("Превышено максимальное количество итераций")
        return "Превышено максимальное количество итераций."

    def reset(self) -> None:
        self._messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
        ]
