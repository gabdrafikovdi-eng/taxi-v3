# app/main.py
import asyncio
import logging
from uuid import uuid4

from app.core.database import async_session_factory
from app.models.call_session import CallSession, CallChannel, HandledBy
from app.repositories.call_session_repo import CallSessionRepository
from app.llm.client import LLMClient
from app.llm.conversation import ConversationManager
from app.tools.composition import build_tools

# Включаем логирование
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
)
logger = logging.getLogger(__name__)


async def create_call_session(session) -> uuid4:
    """Создаёт call_session."""
    call_session = CallSession(
        channel=CallChannel.CONSOLE,
        handled_by=HandledBy.BOT,
        external_call_id=str(uuid4()),
        caller_phone="79000000000",
    )
    call_repo = CallSessionRepository(session)
    await call_repo.add(call_session=call_session)
    await call_repo.session.commit()
    return call_session.id


async def main() -> None:
    async with async_session_factory() as session:
        call_session_id = await create_call_session(session)
        logger.info("call_session_id: %s", call_session_id)

        registry, availability = build_tools(session)
        llm_client = LLMClient()
        conversation = ConversationManager(llm_client, registry, availability)

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
