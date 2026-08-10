from datetime import datetime, UTC
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio.session import AsyncSession

from app.models.call_session import CallSession


class CallSessionRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_id(self, call_session_id: UUID) -> CallSession | None:
        # Зачем: загрузить звонок по ID.
        query = select(CallSession).where(CallSession.id == call_session_id)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def add(self, call_session: CallSession) -> None:
        # Зачем: создать новый звонок при входящем вызове.
        self.session.add(call_session)

    async def end_call(self, call_session: CallSession) -> None:
        # Зачем: установить ended_at при завершении звонка.
        call_session.ended_at = datetime.now(UTC)
        self.session.add(call_session)
