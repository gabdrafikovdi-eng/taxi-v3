from uuid import UUID

from app.core.database import config_settings
from app.core.exceptions import (
    InvalidStateError,
    OrderNotFoundError,
    TooManyActiveOrdersError,
)
from app.models.order import Order
from app.models.order_state import ACTIVE_ORDER_STATES, OrderState
from app.repositories.order_repo import OrderRepository
from app.schemas.address import AddressInput, AddressStatus
from app.services.address_service import AddressService
from app.services.state_service import StateService


class OrderService:
    def __init__(
        self,
        state_service: StateService,
        address_service: AddressService,
        calculate_service,
        order_repo: OrderRepository,
    ):
        self.state_service = state_service
        self.address_service = address_service
        self.calculate_service = calculate_service
        self.order_repo = order_repo

    async def create_order(self, call_session_id: UUID, idempotency_key: str) -> Order:
        orders: list[Order] = await self.order_repo.get_active_orders_by_call_session(
            call_session_id
        )
        if len(orders) >= config_settings.MAX_ACTIVE_ORDERS:
            raise TooManyActiveOrdersError(
                max_allowed=config_settings.MAX_ACTIVE_ORDERS
            )
        for order in orders:
            if (
                order.idempotency_key == idempotency_key
                and order.state in ACTIVE_ORDER_STATES
            ):
                return order

        order = Order(call_session_id=call_session_id, idempotency_key=idempotency_key)
        await self.order_repo.add(order)
        await self.order_repo.commit()

    async def set_pickup(self, order_id: UUID, address_data: AddressInput) -> Order:
        order = await self.order_repo.get_by_id(order_id=order_id)
        if order is None:
            raise OrderNotFoundError(order_id=order_id)

        if order.state != OrderState.DRAFT:
            raise InvalidStateError(order_id=order_id)
        address_result = await self.address_service.resolve_address(address_data)

        if address_result.status == AddressStatus.NOT_FOUND:
            raise 
        


"""class OrderService:

    Конструктор принимает:
        state_service: StateService
        order_repo: OrderRepository
        address_service: AddressService
        pricing_service: PricingService

    set_pickup(session, order_id, address_data) → Order
        Зачем: установить адрес подачи.
        Шаги:
            1. Загрузить заказ через order_repo.get_by_id
               → если None, бросить OrderNotFoundError
            2. Проверить state == DRAFT
               → если не DRAFT, бросить InvalidStateError
            3. Валидировать адрес через address_service
               → если невалиден, бросить AddressValidationError
            4. Сохранить pickup_street_id, pickup_street
            5. Сбросить price = None
            6. Если оба адреса есть → пересчитать цену через pricing_service
            7. session.commit()
        Кто вызывает: handle_set_pickup_address (tool)

    set_destination(session, order_id, address_data) → Order
        Зачем: установить адрес назначения.
        Аналогично set_pickup, но для destination.

    add_waypoint(session, order_id, address_data) → Order
        Зачем: добавить промежуточную остановку.
        Шаги:
            1. Загрузить заказ
            2. Проверить state == DRAFT
            3. Проверить len(waypoints) < MAX_WAYPOINTS
            4. Валидировать адрес
            5. Создать OrderWaypoint с sequence_number = len(waypoints) + 1
            6. Сбросить price, пересчитать если оба адреса
            7. session.commit()

    update_waypoint(session, order_id, index, address_data) → Order
        Зачем: изменить промежуточную остановку по индексу.

    remove_waypoint(session, order_id, index) → Order
        Зачем: удалить промежуточную остановку по индексу.
        После удаления пересчитать sequence_number оставшихся.

    set_passenger_name(session, order_id, name) → Order
        Зачем: установить имя пассажира.

    set_comment(session, order_id, comment) → Order
        Зачем: установить комментарий к заказу.

    confirm_order(session, order_id) → Order
        Зачем: подтвердить заказ.
        Шаги:
            1. Загрузить заказ
            2. state_service.transition(order, CONFIRMED)
               → StateService проверяет матрицу и guards
            3. session.commit()
        Кто вызывает: handle_confirm_order (tool)

    cancel_order(session, order_id) → Order
        Зачем: отменить заказ.
        Шаги:
            1. Загрузить заказ
            2. state_service.transition(order, CANCELLED)
            3. session.commit()
        Кто вызывает: handle_cancel_order (tool)"""
