from uuid import UUID

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from app.models.call_session import CallSession
from app.models.messages import Message, ToolCallRecord


class MessageRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_call_session(self, call_session_id: UUID) -> list[Message]:
        # Зачем: получить все сообщения звонка для построения промпта.
        # Сортировка: sequence_number ASC
        query = (
            select(Message)
            .where(Message.call_session_id == call_session_id)
            .options(selectinload(Message.tools_calls))
            .order_by(Message.sequence_number.asc())
        )
        result = await self.session.execute(query)
        return list(result.scalars())

    async def add(self, message: Message) -> None:
        # Зачем: сохранить сообщение пользователя или ответ LLM.
        self.session.add(message)

    async def get_next_sequence_number(self, call_session_id: UUID) -> int:
        """
        Атомарно инкрементирует счетчик сообщений для сессии.
        UPDATE ... RETURNING гарантирует отсутствие race condition.
        """
        stmt = (
            update(CallSession)
            .where(CallSession.id == call_session_id)
            .values(last_message_sequence=CallSession.last_message_sequence + 1)
            .returning(CallSession.last_message_sequence)
        )

        result = await self.session.execute(stmt)
        return result.scalar_one()

    async def add_tool_call(self, tool_call: ToolCallRecord) -> None:
        self.session.add(tool_call)
