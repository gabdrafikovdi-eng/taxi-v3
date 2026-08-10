from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.messages import Message


class MessageRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_call_session(self, call_session_id: UUID) -> list[Message]:
        # Зачем: получить все сообщения звонка для построения промпта.
        # Сортировка: sequence_number ASC
        query = (
            select(Message)
            .where(Message.call_session_id == call_session_id)
            .order_by(Message.sequence_number.asc())
        )
        result = await self.session.execute(query)
        return list(result.scalars())

    async def add(self, message: Message) -> None:
        # Зачем: сохранить сообщение пользователя или ответ LLM.
        self.session.add(message)

    async def get_next_sequence_number(self, call_session_id: UUID) -> int:
        # Зачем: каждый сообщение имеет порядковый номер.
        # SELECT MAX(sequence_number) + 1
        query = select(func.max(Message.sequence_number)).where(
            Message.call_session_id == call_session_id
        )
        result = await self.session.execute(query)
        max_sequence = result.scalar_one()
        return 1 if max_sequence is None else max_sequence + 1
