from uuid import UUID

from sqlalchemy.ext.asyncio.session import AsyncSession
from sqlalchemy import select


from app.models.call_session import CallSession
from app.models.order import Order, OrderState


class OrderRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_id(self, order_id: UUID) -> Order | None:
        query = select(Order).where(Order.id == order_id)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def get_active_call_session(self, call_session_id: UUID) -> Order | None:
        query = (
            select(Order)
            .where(
                Order.call_session_id == call_session_id,
                Order.state.in_((OrderState.DRAFT, OrderState.CONFIRMED)),
            )
            .order_by(Order.created_at.desc())
            .limit(1)
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def add(self, order: Order) -> None:
        self.session.add(order)

    async def save(self, order: Order) -> None:
        self.session.add(order)
