import asyncio
from typing import Any
from uuid import UUID

from app.core.database import config_settings
from app.core.exceptions import (
    AddressResolveError,
    InvalidStateError,
    OrderNotFoundError,
    PricingError,
    TooManyActiveOrdersError,
)
from app.models.order import Order
from app.models.order_state import ACTIVE_ORDER_STATES, OrderState
from app.repositories.order_repo import OrderRepository
from app.schemas.address import AddressCandidate, AddressInput, AddressStatus
from app.services.address.address_service import AddressService
from app.services.pricing_service import PricingService
from app.services.state_service import StateService

from sqlalchemy.orm.exc import StaleDataError


class OrderService:
    def __init__(
        self,
        state_service: StateService,
        address_service: AddressService,
        pricing_service: PricingService,
        order_repo: OrderRepository,
    ):
        self.state_service = state_service
        self.address_service = address_service
        self.pricing_service = pricing_service
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
        return order

    async def set_pickup(self, order_id: UUID, address_data: AddressInput) -> Order:
        order = await self.order_repo.get_by_id(order_id=order_id)
        if order is None:
            raise OrderNotFoundError(order_id=order_id)

        if order.state != OrderState.DRAFT:
            raise InvalidStateError(
                order_id=order_id,
                current_state=order.state,
                attemted_action="set_pickup",
            )

        address_result = await self.address_service.resolve_address(
            address=address_data
        )

        match address_result.status:
            case AddressStatus.NOT_FOUND:
                raise AddressResolveError(
                    status=AddressStatus.NOT_FOUND,
                    message=address_result.reason,
                    suggestions=address_result.suggestions,
                )

            case AddressStatus.AMBIGUOUS:
                raise AddressResolveError(
                    status=AddressStatus.AMBIGUOUS,
                    message="Найдено несколько вариантов. Выберите один из предложенных",
                    candidates=address_result.candidates,
                )
            case AddressStatus.INCOMPLETE:
                raise AddressResolveError(
                    status=AddressStatus.INCOMPLETE,
                    message=address_result.reason,
                )

            case AddressStatus.RESOLVED:
                candidate = address_result.candidates[0]

        max_retries = 3

        for attempt in range(max_retries):
            try:
                order = await self.order_repo.get_by_id(order_id)

                if order is None:
                    raise OrderNotFoundError(order_id=order_id)

                if order.state != OrderState.DRAFT:
                    raise InvalidStateError(
                        order_id=order_id,
                        current_state=order.state,
                        attemted_action="set_pickup",
                    )

                if self._is_same_address(
                    target=order, candidate=candidate, prefix="pickup"
                ):
                    return order

                self._apply_address_candidate(
                    target=order, candidate=candidate, prefix="pickup"
                )
                order.price = None

                if order.has_both_addresses:
                    price = await self.pricing_service.calculate(order)

                    if price is None:
                        raise PricingError(
                            reason="Не удалось рассчитать стоимость поедзки"
                        )

                    order.price = price

                await self.order_repo.commit()
                return order

            except StaleDataError:
                await self.order_repo.rollback()
                if attempt == max_retries - 1:
                    raise  # TODO или выбросить специализированное исключение

                await asyncio.sleep(0.3)

        raise RuntimeError("Не удалось выполнить операцию из-за конфликтов")

    async def set_destination(
        self, order_id: UUID, address_data: AddressInput
    ) -> Order:
        order = await self.order_repo.get_by_id(order_id=order_id)
        if order is None:
            raise OrderNotFoundError(order_id=order_id)

        if order.state != OrderState.DRAFT:
            raise InvalidStateError(
                order_id=order_id,
                current_state=order.state,
                attemted_action="set_destination",
            )
        address_result = await self.address_service.resolve_address(address_data)

        match address_result.status:
            case AddressStatus.NOT_FOUND:
                raise AddressResolveError(
                    status=AddressStatus.NOT_FOUND,
                    message=address_result.reason,
                    suggestions=address_result.suggestions,
                )

            case AddressStatus.AMBIGUOUS:
                raise AddressResolveError(
                    status=AddressStatus.AMBIGUOUS,
                    message=address_result.reason,
                    candidates=address_result.candidates,
                )
            case AddressStatus.INCOMPLETE:
                raise AddressResolveError(
                    status=AddressStatus.INCOMPLETE,
                    message=address_result.reason,
                )

            case AddressStatus.RESOLVED:
                candidate = address_result.candidates[0]

        max_retries = 3

        for attempt in range(max_retries):
            try:
                order = await self.order_repo.get_by_id(order_id)

                if order is None:
                    raise OrderNotFoundError(order_id=order_id)

                if order.state != OrderState.DRAFT:
                    raise InvalidStateError(
                        order_id=order_id,
                        current_state=order.state,
                        attemted_action="set_destination",
                    )

                if self._is_same_address(
                    target=order, candidate=candidate, prefix="destination"
                ):
                    return order

                self._apply_address_candidate(
                    target=order, candidate=candidate, prefix="destination"
                )
                order.price = None

                if order.has_both_addresses:
                    price = await self.pricing_service.calculate(order)

                    if price is None:
                        raise PricingError(
                            reason="Не удалось рассчитать стоимость поедзки"
                        )

                    order.price = price

                await self.order_repo.commit()
                return order

            except StaleDataError:
                await self.order_repo.rollback()
                if attempt == max_retries - 1:
                    raise  # TODO или выбросить специализированное исключение

                await asyncio.sleep(0.3)

        raise RuntimeError("Не удалось выполнить операцию из-за конфликтов")

    def _is_same_address(
        self, target: Any, candidate: AddressCandidate, prefix: str
    ) -> bool:

        field_map = {
            "town_id": candidate.town_id,
            "district_id": candidate.district_id,
            "street_id": candidate.street_id,
            "house_id": candidate.house_id,
            "landmark_id": candidate.landmark_id,
        }
        for suffix, value in field_map.items():
            if getattr(target, f"{prefix}_{suffix}") != value:
                return False

        return True

    def _apply_address_candidate(
        self, target: Any, candidate: AddressCandidate, prefix: str
    ) -> None:
        """Заполняет поля target с префиксом prefix данными из candidate."""
        field_map = {
            "town": candidate.town_name,
            "town_id": candidate.town_id,
            "district": candidate.district_name,
            "district_id": candidate.district_id,
            "street": candidate.street_name,
            "street_id": candidate.street_id,
            "house": candidate.house_number,
            "house_id": candidate.house_id,
            "landmark": candidate.landmark_name,
            "landmark_id": candidate.landmark_id,
        }
        for suffix, value in field_map.items():
            setattr(target, f"{prefix}_{suffix}", value)


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
