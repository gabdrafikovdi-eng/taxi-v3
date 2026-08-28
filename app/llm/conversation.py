import json
import logging

from uuid import UUID

from app.llm.client import LLMClient
from app.llm.message_mapper import to_llm_message
from app.models.messages import Message, MessageRole, ToolCallRecord
from app.repositories.message_repo import MessageRepository
from app.tools.base import ToolContext
from app.tools.registry import ToolRegistry
from app.tools.availability import OrderToolAvailability


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

    async def handle_message(
        self,
        user_message: str,
        call_session_id: UUID,
    ) -> str:

        await self._save_user_message(
            call_session_id=call_session_id, content=user_message, role=MessageRole.USER
        )

        logger.info("=" * 60)
        logger.info("ПОЛЬЗОВАТЕЛЬ: %s", user_message)

        max_iterations = 10
        for iteration in range(max_iterations):
            messages = await self._message_repo.get_by_call_session(call_session_id)
            messages_llm = to_llm_message(messages)

            available_names = await self._availability.available_names(call_session_id)
            tools = self._registry.openai_tools(available_names)
            logger.info("Доступные инструменты: %s", available_names)

            logger.info("-" * 40)
            logger.info("ИТЕРАЦИЯ %d", iteration + 1)

            response = await self._llm.chat(
                messages_llm, tools=tools if tools else None
            )
            logger.info("RAW RESPONSE: %s", response.model_dump())

            # Если есть текст — финальный ответ
            if response.content:
                logger.info("ФИНАЛЬНЫЙ ОТВЕТ: %s", response.content)
                # assistant_msg: dict[str, Any] = response.model_dump(exclude_none=True)
                sequence_number = await self._message_repo.get_next_sequence_number(
                    call_session_id=call_session_id
                )
                assistant_msg_db = Message(
                    call_session_id=call_session_id,
                    sequence_number=sequence_number,
                    role=MessageRole.ASSISTANT,
                    content=response.content,
                )

                await self._message_repo.add(message=assistant_msg_db)
                await self._message_repo.session.commit()
                return response.content

            # Если есть tool_calls
            if response.tool_calls:
                logger.info("МОДЕЛЬ ВЫЗЫВАЕТ ИНСТРУМЕНТЫ:")

                # Сохраняем ПОЛНЫЙ ответ модели
                sequence_number = await self._message_repo.get_next_sequence_number(
                    call_session_id=call_session_id
                )
                assistant_msg_db = Message(
                    call_session_id=call_session_id,
                    sequence_number=sequence_number,
                    role=MessageRole.ASSISTANT,
                    content=response.content,
                )
                await self._message_repo.add(message=assistant_msg_db)
                await self._message_repo.session.commit()

                # Выполняем каждый tool_call
                for tool_call in response.tool_calls:
                    logger.info("RAW TOOL CALL: %s", tool_call.model_dump())

                    logger.info("  Tool: %s", tool_call.function.name)
                    logger.info("  Args: %s", tool_call.function.arguments)

                    extra_content = getattr(tool_call, "extra_content", None) or {}
                    google_data = extra_content.get("google", {})
                    thought_signature = google_data.get("thought_signature")

                    tool_call_record = ToolCallRecord(
                        message_id=assistant_msg_db.id,
                        tool_call_id=tool_call.id,
                        function_name=tool_call.function.name,
                        arguments=tool_call.function.arguments,
                        thought_signature=thought_signature,
                    )

                    await self._message_repo.add_tool_call(tool_call=tool_call_record)

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
                    sequence_number = await self._message_repo.get_next_sequence_number(
                        call_session_id
                    )
                    tool_message_db = Message(
                        call_session_id=call_session_id,
                        sequence_number=sequence_number,
                        role=MessageRole.TOOL,
                        content=result.model_dump_json(),
                        tool_call_id=tool_call.id,
                    )
                    await self._message_repo.add(tool_message_db)

                    logger.info(
                        "  Result: success=%s, code=%s", result.success, result.code
                    )
                    if result.data:
                        logger.info(
                            "  Data: %s",
                            json.dumps(result.data, ensure_ascii=False, indent=2),
                        )

                await self._message_repo.session.commit()

        logger.warning("Превышено максимальное количество итераций")
        return "Превышено максимальное количество итераций."

    async def _save_user_message(
        self, call_session_id: str, content: str, role: MessageRole
    ) -> None:
        sequence_number = await self._message_repo.get_next_sequence_number(
            call_session_id=call_session_id
        )

        message = Message(
            call_session_id=call_session_id,
            sequence_number=sequence_number,
            role=role,
            content=content,
        )

        await self._message_repo.add(message=message)
        await self._message_repo.session.commit()
