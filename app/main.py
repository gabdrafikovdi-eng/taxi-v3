# app/main.py
import asyncio
import logging
from uuid import uuid4

from app.core.database import async_session_factory
from app.llm.system_prompt import SYSTEM_PROMPT
from app.models.call_session import CallSession, CallChannel, HandledBy
from app.models.messages import Message, MessageRole
from app.repositories.call_session_repo import CallSessionRepository
from app.llm.client import LLMClient
from app.llm.conversation import ConversationManager
from app.repositories.message_repo import MessageRepository
from app.services.call_service import CallSessionService
from app.tools.composition import build_tools


# Включаем логирование
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
)
logger = logging.getLogger(__name__)


async def main() -> None:
    async with async_session_factory() as session:
        # call_session_id = await create_call_session(session)
        # logger.info("call_session_id: %s", call_session_id)
        call_repo = CallSessionRepository(session)
        call_service = CallSessionService(call_repo)

        call = await call_service.start_call(
            external_id=str(uuid4()),
            caller_phone="79920770402",
            channel=CallChannel.CONSOLE,
            handled_by=HandledBy.BOT,
        )
        call_session_id = call.id
        logger.info("call_session_id: %s", call_session_id)

        message_repo = MessageRepository(session)

        sequence_number = await message_repo.get_next_sequence_number(
            call_session_id=call_session_id
        )
        system_promt_message = Message(
            call_session_id=call_session_id,
            sequence_number=sequence_number,
            role=MessageRole.SYSTEM,
            content=SYSTEM_PROMPT,
        )
        await message_repo.add(system_promt_message)
        await message_repo.session.commit()

        registry, availability = build_tools(session)
        llm_client = LLMClient()

        conversation = ConversationManager(
            llm_client, registry, availability, message_repo
        )

        print("\n\n Введите сообщение (или 'quit', 'q', 'выход' для выхода):")
        while True:
            try:
                user_input = input("\n\n>  ")
            except EOFError, KeyboardInterrupt:
                break

            if user_input.strip().lower() in {"quit", "q", "exit", "выход"}:
                break

            if not user_input.strip():
                continue

            try:
                response = await conversation.handle_message(
                    user_input, call_session_id
                )
                print(f"\nБот: {response}")
            except Exception as e:
                logger.exception("Ошибка в диалоге")
                print(f"\nОшибка: {e}")


if __name__ == "__main__":
    asyncio.run(main())
