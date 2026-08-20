from uuid import UUID

from sqlalchemy.ext.asyncio.session import AsyncSession
from sqlalchemy import or_, select
from sqlalchemy.orm import selectinload


from app.models.call_session import CallSession
from app.models.order import Order, Waypoint
from app.models.order_state import ACTIVE_ORDER_STATES, OrderState


class OrderRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_id(self, order_id: UUID) -> Order | None:
        # Зачем: загрузить заказ перед любым изменением.
        # Кто вызывает: OrderService.set_pickup, confirm_order, cancel_order.
        query = (
            select(Order)
            .where(Order.id == order_id)
            .options(selectinload(Order.waypoints))
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def get_active_orders_by_call_session(
        self, call_session_id: UUID
    ) -> list[Order]:
        # Зачем: получить все активные заказы звонка.
        # Фильтр: state IN ACTIVE_ORDER_STATES
        # Сортировка: created_at ASC
        # Кто вызывает: ConversationManager (для промпта),
        #               OrderService (для проверки лимита),
        #               DynamicToolRegistry (для доступности tools).
        query = (
            select(Order)
            .where(
                Order.call_session_id == call_session_id,
                Order.state.in_(ACTIVE_ORDER_STATES),
            )
            .order_by(Order.created_at.asc())
        )
        result = await self.session.execute(query)

        return list(result.scalars())

    async def get_incomplete_draft(self, call_session_id: UUID) -> Order | None:
        # Зачем: найти DRAFT без обоих адресов.
        # Зачем нужен: DynamicToolRegistry скрывает create_order,
        #              пока есть незавершённый DRAFT.
        # Фильтр: state=DRAFT AND (pickup_street_id IS NULL OR destination_street_id IS NULL)
        # Кто вызывает: DynamicToolRegistry.
        query = select(Order).where(
            Order.call_session_id == call_session_id,
            Order.state == OrderState.DRAFT,
            or_(
                Order.pickup_street_id.is_(None), Order.destination_street_id.is_(None)
            ),
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def add(self, order: Order) -> None:
        # Зачем: добавить новый заказ в сессию SQLAlchemy.
        # Не делает commit — commit делает сервис.
        # Кто вызывает: OrderService.create_order.
        self.session.add(order)

    async def delete_waypoint(self, waypoint: Waypoint) -> None:
        await self.session.delete(waypoint)

    async def commit(self) -> None:
        await self.session.commit()

    async def refresh_order(self, order: Order) -> None:
        await self.session.refresh(order)

    async def refresh_with_waypoints(self, order: Order) -> None:
        await self.session.refresh(
            order,
            attribute_names=["waypoints"],
        )

    async def flush(self) -> None:
        await self.session.flush()

    async def rollback(self) -> None:
        await self.session.rollback()
