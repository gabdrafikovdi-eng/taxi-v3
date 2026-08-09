from uuid import UUID

from sqlalchemy.ext.asyncio.session import AsyncSession

from app.models.order import Order


class OrderRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_id(self, order_id: UUID) -> Order | None:
        queru = select()
