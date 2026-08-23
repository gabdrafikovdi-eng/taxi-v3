import asyncio
from typing import Any
from uuid import UUID

from app.core.database import config_settings
from app.core.exceptions import (
    AddressResolveError,
    CallSessionNotFoundError,
    InvalidStateError,
    LimitWaypointError,
    OrderNotFoundError,
    PricingError,
    TooManyActiveOrdersError,
    WaypointNotFoundError,
)
from app.models.order import Order, Waypoint
from app.models.order_state import ACTIVE_ORDER_STATES, OrderState
from app.repositories.order_repo import OrderRepository
from app.schemas.address import (
    AddressCandidate,
    AddressInput,
    AddressStatus,
    OrderComment,
    PassengerName,
)
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
        self.config_settings = config_settings
        self.max_retries = 3

    async def create_order(self, call_session_id: UUID, idempotency_key: str) -> Order:
        next_number = await self.order_repo.get_next_order_number(
            call_session_id=call_session_id
        )
        if next_number is None:
            raise CallSessionNotFoundError(call_session_id)

        orders = await self.order_repo.get_active_orders_by_call_session(
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

        order = Order(
            call_session_id=call_session_id,
            idempotency_key=idempotency_key,
            order_number=next_number,
        )
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

        for attempt in range(self.max_retries):
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
                if attempt == self.max_retries - 1:
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

        for attempt in range(self.max_retries):
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
                if attempt == self.max_retries - 1:
                    raise  # TODO или выбросить специализированное исключение

                await asyncio.sleep(0.3)

        raise RuntimeError("Не удалось выполнить операцию из-за конфликтов")

    async def add_waypoint(self, order_id: UUID, address_data: AddressInput) -> Order:
        """add_waypoint(session, order_id, address_data) → Order
        Зачем: добавить промежуточную остановку.
        Шаги:
            1. Загрузить заказ
            2. Проверить state == DRAFT
            3. Проверить len(waypoints) < MAX_WAYPOINTS
            4. Валидировать адрес
            5. Создать OrderWaypoint с sequence_number = len(waypoints) + 1
            6. Сбросить price, пересчитать если оба адреса
            7. session.commit()"""

        order = await self.order_repo.get_by_id(order_id=order_id)

        if order is None:
            raise OrderNotFoundError(order_id=order_id)

        if order.state != OrderState.DRAFT:
            raise InvalidStateError(
                order_id=order_id,
                current_state=order.state,
                attemted_action="add_waypoint",
            )

        if len(order.waypoints) >= self.config_settings.MAX_WAYPOINTS:
            raise LimitWaypointError(
                current_waypoint_count=len(order.waypoints),
                max_waypoint=self.config_settings.MAX_WAYPOINTS,
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

        for attempt in range(self.max_retries):
            try:
                order = await self.order_repo.get_by_id(order_id)

                if order is None:
                    raise OrderNotFoundError(order_id=order_id)

                if order.state != OrderState.DRAFT:
                    raise InvalidStateError(
                        order_id=order_id,
                        current_state=order.state,
                        attemted_action="add_waypoint",
                    )

                if len(order.waypoints) >= self.config_settings.MAX_WAYPOINTS:
                    raise LimitWaypointError(
                        current_waypoint_count=len(order.waypoints),
                        max_waypoint=self.config_settings.MAX_WAYPOINTS,
                    )

                sequence = len(order.waypoints) + 1
                waypoint = Waypoint(
                    sequence_number=sequence,
                    waypoint_town=candidate.town_name,
                    waypoint_town_id=candidate.town_id,
                    waypoint_district=candidate.district_name,
                    waypoint_district_id=candidate.district_id,
                    waypoint_street=candidate.street_name,
                    waypoint_street_id=candidate.street_id,
                    waypoint_house=candidate.house_number,
                    waypoint_house_id=candidate.house_id,
                    waypoint_landmark=candidate.landmark_name,
                    waypoint_landmark_id=candidate.landmark_id,
                )
                order.waypoints.append(waypoint)

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
                if attempt == self.max_retries - 1:
                    raise  # TODO или выбросить специализированное исключение

                await asyncio.sleep(0.3)

        raise RuntimeError("Не удалось выполнить операцию из-за конфликтов")

    async def update_waypoint(
        self, order_id: UUID, sequence_number: int, address_data: AddressInput
    ) -> Order:
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

        for attempt in range(self.max_retries):
            try:
                order = await self.order_repo.get_by_id(order_id)

                if order is None:
                    raise OrderNotFoundError(order_id=order_id)

                if order.state != OrderState.DRAFT:
                    raise InvalidStateError(
                        order_id=order_id,
                        current_state=order.state,
                        attemted_action="update_waypoint",
                    )

                waypoint = next(
                    (
                        waypoint
                        for waypoint in order.waypoints
                        if waypoint.sequence_number == sequence_number
                    ),
                    None,
                )
                if waypoint is None:
                    raise WaypointNotFoundError(
                        order_id=order_id,
                        sequence_number=sequence_number,
                    )

                self._apply_address_candidate(
                    target=waypoint,
                    candidate=candidate,
                    prefix="waypoint",
                )

                order.price = None

                if order.has_both_addresses:
                    price = await self.pricing_service.calculate(order)

                    if price is None:
                        raise PricingError(
                            reason="Не удалось рассчитать стоимость поездки"
                        )

                    order.price = price

                await self.order_repo.commit()
                return order

            except StaleDataError:
                await self.order_repo.rollback()
                if attempt == self.max_retries - 1:
                    raise  # TODO или выбросить специализированное исключение

                await asyncio.sleep(0.3)

        raise RuntimeError("Не удалось выполнить операцию из-за конфликтов")

    async def remove_waypoint(
        self,
        order_id: UUID,
        sequence_number: int,
    ) -> Order:

        for attempt in range(self.max_retries):
            try:
                order = await self.order_repo.get_by_id(order_id)

                if order is None:
                    raise OrderNotFoundError(order_id=order_id)

                if order.state != OrderState.DRAFT:
                    raise InvalidStateError(
                        order_id=order_id,
                        current_state=order.state,
                        attemted_action="remove_waypoint",
                    )

                waypoint = next(
                    (
                        waypoint
                        for waypoint in order.waypoints
                        if waypoint.sequence_number == sequence_number
                    ),
                    None,
                )

                if waypoint is None:
                    raise WaypointNotFoundError(
                        order_id=order_id,
                        sequence_number=sequence_number,
                    )

                order.waypoints.remove(waypoint)
                # await self.order_repo.delete_waypoint(waypoint)
                # await self.order_repo.flush()
                # await self.order_repo.refresh_with_waypoints(order)

                for sequence, waypoint in enumerate(
                    sorted(
                        order.waypoints,
                        key=lambda waypoint: waypoint.sequence_number,
                    ),
                    start=1,
                ):
                    waypoint.sequence_number = sequence

                order.price = None

                if order.has_both_addresses:
                    price = await self.pricing_service.calculate(order)

                    if price is None:
                        raise PricingError(
                            reason="Не удалось рассчитать стоимость поездки"
                        )

                    order.price = price

                await self.order_repo.commit()
                return order

            except StaleDataError:
                await self.order_repo.rollback()

                if attempt == self.max_retries - 1:
                    raise

                await asyncio.sleep(0.3)

        raise RuntimeError("Не удалось выполнить операцию из-за конфликтов")

    async def set_passenger_name(
        self,
        order_id: UUID,
        name: PassengerName,
    ) -> Order:

        for attempt in range(self.max_retries):
            try:
                order = await self.order_repo.get_by_id(order_id=order_id)

                if order is None:
                    raise OrderNotFoundError(order_id=order_id)

                order.passenger_name = name.first_name
                await self.order_repo.commit()
                return order

            except StaleDataError:
                await self.order_repo.rollback()
                if attempt == self.max_retries - 1:
                    raise  # TODO или выбросить специализированное исключение

                await asyncio.sleep(0.3)

        raise RuntimeError("Не удалось выполнить операцию из-за конфликтов")

    async def set_comment(self, order_id: UUID, comment: OrderComment) -> Order:

        for attempt in range(self.max_retries):
            try:
                order = await self.order_repo.get_by_id(order_id=order_id)

                if order is None:
                    raise OrderNotFoundError(order_id=order_id)

                if order.state != OrderState.DRAFT:
                    raise InvalidStateError(
                        order_id=order_id,
                        current_state=order.state,
                        attemted_action="set_comment",
                    )
                order.comment = comment.comment
                await self.order_repo.commit()
                return order

            except StaleDataError:
                await self.order_repo.rollback()
                if attempt == self.max_retries - 1:
                    raise  # TODO или выбросить специализированное исключение

                await asyncio.sleep(0.3)

        raise RuntimeError("Не удалось выполнить операцию из-за конфликтов")

    async def confirm_order(self, order_id: UUID) -> Order:
        for attempt in range(self.max_retries):
            try:
                order = await self.order_repo.get_by_id(order_id=order_id)

                if order is None:
                    raise OrderNotFoundError(order_id=order_id)

                self.state_service.transition(
                    order=order, target_state=OrderState.CONFIRMED
                )
                await self.order_repo.commit()
                return order

            except StaleDataError:
                await self.order_repo.rollback()
                if attempt == self.max_retries - 1:
                    raise  # TODO или выбросить специализированное исключение

                await asyncio.sleep(0.3)

        raise RuntimeError("Не удалось выполнить операцию из-за конфликтов")

    async def cancel_order(self, order_id: UUID) -> Order:
        for attempt in range(self.max_retries):
            try:
                order = await self.order_repo.get_by_id(order_id=order_id)

                if order is None:
                    raise OrderNotFoundError(order_id=order_id)

                self.state_service.transition(
                    order=order, target_state=OrderState.CANCELLED
                )
                await self.order_repo.commit()
                return order

            except StaleDataError:
                await self.order_repo.rollback()
                if attempt == self.max_retries - 1:
                    raise  # TODO или выбросить специализированное исключение

                await asyncio.sleep(0.3)

        raise RuntimeError("Не удалось выполнить операцию из-за конфликтов")

    async def get_order_by_number(
        self, call_session_id: UUID, order_number: int
    ) -> Order:
        order = await self.order_repo.get_by_order_number(
            call_session_id=call_session_id, order_number=order_number
        )

        if order is None:
            raise OrderNotFoundError(order_id=f"order_number = {order_number}")

        return order

    async def list_active_orders(self, call_session_id: UUID) -> list[Order]:
        return await self.order_repo.get_active_orders_by_call_session(call_session_id)

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
