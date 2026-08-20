"""Unit-тесты бизнес-логики OrderService.

Тесты опираются на observable behavior, а не на реализацию строка-в-строку:
проверяются итоговые Order / state / адреса / waypoint / price / исключения /
retry / idempotency / state transitions.

Зависимости (AddressService, PricingService, OrderRepository) замоканы через
unittest.mock. StateService используется реальный (он не является объектом
тестирования), transition() синхронный.

ВАЖНО. Production-код НЕ изменяется. Если тест фиксирует дефект production-кода,
он пишется под фактическое поведение и проблема выносится в финальный отчёт.

==============================================================================
КАК ЗАПУСКАТЬ
==============================================================================
    .venv/bin/python -m pytest tests/test_order_service.py -v
==============================================================================
"""

from __future__ import annotations

from unittest.mock import AsyncMock, Mock
from uuid import UUID, uuid4

import pytest
import pytest_asyncio
from sqlalchemy.orm.exc import StaleDataError

from app.core.exceptions import (
    AddressResolveError,
    InvalidStateError,
    InvalidTransitionError,
    LimitWaypointError,
    OrderNotFoundError,
    PricingError,
    TooManyActiveOrdersError,
    WaypointNotFoundError,
)
from app.core.database import config_settings
from app.models.order import Order, Waypoint
from app.models.order_state import OrderState
from app.schemas.address import (
    AddressCandidate,
    AddressInput,
    AddressMatchResult,
    AddressStatus,
    OrderComment,
    PassengerName,
)
from app.services.order_service import OrderService
from app.services.state_service import StateService

# ---------------------------------------------------------------------------
# Хелперы: данные адресов и Order
# ---------------------------------------------------------------------------


def build_candidate(**overrides) -> AddressCandidate:
    """Стандартный AddressCandidate с возможностью переопределить поля."""
    base = {
        "town_id": 1,
        "town_name": "аскарово",
        "district_id": 2,
        "district_name": "центр",
        "street_id": 3,
        "street_name": "ленина",
        "house_id": 4,
        "house_number": "5",
        "landmark_id": None,
        "landmark_name": None,
        "full_address": "аскарово, центр, ленина, 5",
        "score": 0.95,
    }
    base.update(overrides)
    return AddressCandidate(**base)


def resolved_address(**overrides) -> AddressMatchResult:
    """AddressMatchResult со статусом RESOLVED и одним кандидатом."""
    return AddressMatchResult(
        status=AddressStatus.RESOLVED,
        candidates=[build_candidate(**overrides)],
    )


def error_address(status: AddressStatus, **kw) -> AddressMatchResult:
    """AddressMatchResult с ошибкой разрешения адреса."""
    return AddressMatchResult(status=status, **kw)


def build_draft_order(**overrides) -> Order:
    """Новый DRAFT-заказ без адресов."""
    order = Order(call_session_id=uuid4(), idempotency_key="idem-1")
    order.state = OrderState.DRAFT
    for name, value in overrides.items():
        setattr(order, name, value)
    return order


def build_priced_draft(pickup_street_id: int = 3, destination_street_id: int = 11) -> Order:
    """DRAFT-заказ с обоими адресами и положительной ценой."""
    return build_draft_order(
        pickup_town="аскарово",
        pickup_town_id=1,
        pickup_district="центр",
        pickup_district_id=2,
        pickup_street="ленина",
        pickup_street_id=pickup_street_id,
        pickup_house="5",
        pickup_house_id=4,
        destination_town="аскарово",
        destination_town_id=1,
        destination_district="центр",
        destination_district_id=2,
        destination_street="гагарина",
        destination_street_id=destination_street_id,
        destination_house="10",
        destination_house_id=14,
        price=1000,
    )


def build_draft_with_both_addresses() -> Order:
    """DRAFT-заказ с обоими адресами, но БЕЗ цены (для негативных сценариев)."""
    return build_draft_order(
        pickup_town="аскарово",
        pickup_town_id=1,
        pickup_street="ленина",
        pickup_street_id=3,
        pickup_landmark_id=None,
        destination_town="аскарово",
        destination_town_id=1,
        destination_street="гагарина",
        destination_street_id=11,
        destination_landmark_id=None,
    )


def add_waypoints(order: Order, count: int) -> Order:
    """Добавляет count waypoint'ов c sequence_number 1..count."""
    for index in range(1, count + 1):
        order.waypoints.append(
            Waypoint(
                order_id=order.id,
                sequence_number=index,
                waypoint_town="аскарово",
                waypoint_town_id=1,
                waypoint_street="кирова",
                waypoint_street_id=100 + index,
                waypoint_house=str(index),
                waypoint_house_id=200 + index,
            )
        )
    return order


# ---------------------------------------------------------------------------
# Фикстура сервиса с замокаными зависимостями
# ---------------------------------------------------------------------------


@pytest_asyncio.fixture
def svc() -> OrderService:
    """OrderService с реальным StateService и мокнутыми репозиторием/сервисами."""
    service = OrderService(
        state_service=StateService(),
        address_service=AsyncMock(),
        pricing_service=AsyncMock(),
        order_repo=AsyncMock(),
    )
    return service


# Отключаем реальный asyncio.sleep в retry-циклах, чтобы тесты были быстрыми.


async def _async_noop(*args, **kwargs):
    return None


@pytest.fixture(autouse=True)
def _no_sleep(monkeypatch):
    monkeypatch.setattr("app.services.order_service.asyncio.sleep", _async_noop)
    yield


# ---------------------------------------------------------------------------
# CREATE_ORDER
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_create_order_success_creates_draft_and_commits(svc: OrderService) -> None:
    """create_order: новый Order с call_session_id/idempotency_key, state=DRAFT, commit."""
    new_order = build_draft_order()

    def _persist(order: Order) -> None:
        # В реальном SQLAlchemy flush выставит state по default=DRAFT.
        order.state = OrderState.DRAFT

    svc.order_repo.add.side_effect = _persist
    svc.order_repo.get_active_orders_by_call_session.return_value = []

    result = await svc.create_order(
        call_session_id=new_order.call_session_id, idempotency_key="key-1"
    )

    assert result.call_session_id == new_order.call_session_id
    assert result.idempotency_key == "key-1"
    assert result.state == OrderState.DRAFT
    svc.order_repo.add.assert_called_once()
    svc.order_repo.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_create_order_allows_below_max_active(svc: OrderService) -> None:
    """Активных заказов меньше лимита — создание разрешено."""
    existing = [build_draft_order() for _ in range(config_settings.MAX_ACTIVE_ORDERS - 1)]
    svc.order_repo.get_active_orders_by_call_session.return_value = existing

    result = await svc.create_order(call_session_id=uuid4(), idempotency_key="new-key")

    assert result.idempotency_key == "new-key"
    svc.order_repo.add.assert_called_once()
    svc.order_repo.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_create_order_raises_when_active_orders_equals_max(svc: OrderService) -> None:
    """Равно MAX_ACTIVE_ORDERS активных заказов -> TooManyActiveOrdersError."""
    existing = [build_draft_order() for _ in range(config_settings.MAX_ACTIVE_ORDERS)]
    svc.order_repo.get_active_orders_by_call_session.return_value = existing

    with pytest.raises(TooManyActiveOrdersError):
        await svc.create_order(call_session_id=uuid4(), idempotency_key="new-key")

    svc.order_repo.add.assert_not_called()


@pytest.mark.asyncio
async def test_create_order_raises_when_active_above_max(svc: OrderService) -> None:
    """Активных заказов больше MAX_ACTIVE_ORDERS -> TooManyActiveOrdersError."""
    existing = [build_draft_order() for _ in range(config_settings.MAX_ACTIVE_ORDERS + 1)]
    svc.order_repo.get_active_orders_by_call_session.return_value = existing

    with pytest.raises(TooManyActiveOrdersError):
        await svc.create_order(call_session_id=uuid4(), idempotency_key="new-key")

    svc.order_repo.add.assert_not_called()


@pytest.mark.asyncio
async def test_create_order_idempotent_returns_existing_active_order(
    svc: OrderService,
) -> None:
    """Повторный же idempotency_key с активным заказом возвращает существующий."""
    existing = build_draft_order()
    svc.order_repo.get_active_orders_by_call_session.return_value = [existing]

    result = await svc.create_order(
        call_session_id=existing.call_session_id, idempotency_key=existing.idempotency_key
    )

    assert result is existing
    svc.order_repo.add.assert_not_called()
    svc.order_repo.commit.assert_not_called()


@pytest.mark.asyncio
async def test_create_order_idempotent_ignores_cancelled(svc: OrderService) -> None:
    """CANCELLED заказ с тем же ключом НЕ возвращается как активный."""
    cancelled = build_draft_order(idempotency_key="dup")
    cancelled.state = OrderState.CANCELLED
    svc.order_repo.get_active_orders_by_call_session.return_value = [cancelled]

    result = await svc.create_order(
        call_session_id=cancelled.call_session_id, idempotency_key=cancelled.idempotency_key
    )

    assert result is not cancelled
    assert result.idempotency_key == "dup"
    svc.order_repo.add.assert_called_once()
    svc.order_repo.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_create_order_idempotent_ignores_completed(svc: OrderService) -> None:
    """COMPLETED заказ с тем же idempotency_key НЕ возвращается как активный."""
    completed = build_draft_order(idempotency_key="dup")
    completed.state = OrderState.COMPLETED
    svc.order_repo.get_active_orders_by_call_session.return_value = [completed]

    result = await svc.create_order(
        call_session_id=completed.call_session_id, idempotency_key=completed.idempotency_key
    )

    assert result is not completed
    svc.order_repo.add.assert_called_once()


@pytest.mark.asyncio
async def test_create_order_idempotent_finds_key_among_multiple_active(
    svc: OrderService,
) -> None:
    """Идемпотентность ищется среди нескольких активных заказов."""
    first = build_draft_order(idempotency_key="key-a")
    second = build_draft_order(idempotency_key="key-b")
    svc.order_repo.get_active_orders_by_call_session.return_value = [first, second]

    result = await svc.create_order(
        call_session_id=second.call_session_id, idempotency_key=second.idempotency_key
    )

    assert result is second
    svc.order_repo.add.assert_not_called()
# ---------------------------------------------------------------------------
# SET_PICKUP
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_set_pickup_order_not_found_raises(svc: OrderService) -> None:
    """set_pickup: заказ не найден -> OrderNotFoundError."""
    svc.order_repo.get_by_id.return_value = None

    with pytest.raises(OrderNotFoundError):
        await svc.set_pickup(order_id=uuid4(), address_data=AddressInput(street="ленина", house="5"))


@pytest.mark.asyncio
async def test_set_pickup_invalid_state_raises(svc: OrderService) -> None:
    """set_pickup: заказ не в DRAFT -> InvalidStateError."""
    order = build_draft_order(state=OrderState.CONFIRMED)
    svc.order_repo.get_by_id.return_value = order

    with pytest.raises(InvalidStateError):
        await svc.set_pickup(order_id=order.id, address_data=AddressInput(street="ленина", house="5"))


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "status",
    [AddressStatus.NOT_FOUND, AddressStatus.AMBIGUOUS, AddressStatus.INCOMPLETE],
)
async def test_set_pickup_raises_address_resolve_error(svc: OrderService, status) -> None:
    """set_pickup: не-разрешённый адрес -> AddressResolveError с тем же статусом."""
    order = build_draft_order()
    svc.order_repo.get_by_id.return_value = order
    svc.address_service.resolve_address.return_value = error_address(status, reason="bad")

    with pytest.raises(AddressResolveError) as exc_info:
        await svc.set_pickup(order_id=order.id, address_data=AddressInput(street="5"))

    assert exc_info.value.status == status
    svc.order_repo.commit.assert_not_awaited()


@pytest.mark.asyncio
async def test_set_pickup_applies_full_candidate(svc: OrderService) -> None:
    """set_pickup: RESOLVED полностью заполняет поля pickup и их *_id."""
    order = build_draft_order()
    svc.order_repo.get_by_id.return_value = order
    candidate = build_candidate(
        town_id=10, town_name="уфа",
        district_id=20, district_name="советский",
        street_id=30, street_name="ленина",
        house_id=40, house_number="7к1",
        landmark_id=50, landmark_name="фонтан",
    )
    svc.address_service.resolve_address.return_value = AddressMatchResult(
        status=AddressStatus.RESOLVED, candidates=[candidate]
    )

    result = await svc.set_pickup(order_id=order.id, address_data=AddressInput(street="ленина", house="7к1"))

    assert result.pickup_town == "уфа"
    assert result.pickup_town_id == 10
    assert result.pickup_district == "советский"
    assert result.pickup_district_id == 20
    assert result.pickup_street == "ленина"
    assert result.pickup_street_id == 30
    assert result.pickup_house == "7к1"
    assert result.pickup_house_id == 40
    assert result.pickup_landmark == "фонтан"
    assert result.pickup_landmark_id == 50
    svc.order_repo.commit.assert_awaited_once()
@pytest.mark.asyncio
async def test_set_pickup_same_address_does_not_change_order(svc: OrderService) -> None:
    """set_pickup: повторная установка того же адреса не меняет заказ и не коммитит."""
    order = build_draft_order(
        pickup_town="аскарово", pickup_town_id=1,
        pickup_district="центр", pickup_district_id=2,
        pickup_street="ленина", pickup_street_id=3,
        pickup_house="5", pickup_house_id=4,
        price=1000,
    )
    svc.order_repo.get_by_id.return_value = order
    svc.address_service.resolve_address.return_value = resolved_address()

    result = await svc.set_pickup(order_id=order.id, address_data=AddressInput(street="ленина", house="5"))

    assert result is order
    assert order.price == 1000
    assert order.pickup_street_id == 3
    svc.order_repo.commit.assert_not_awaited()
    svc.pricing_service.calculate.assert_not_awaited()


@pytest.mark.asyncio
async def test_set_pickup_changed_address_resets_price_to_none(svc: OrderService) -> None:
    """set_pickup: изменение адреса сбрасывает price; без destination price=None."""
    order = build_draft_order(pickup_street_id=3, price=1000)
    svc.order_repo.get_by_id.return_value = order
    svc.address_service.resolve_address.return_value = resolved_address(street_id=77)

    result = await svc.set_pickup(order_id=order.id, address_data=AddressInput(street="новая", house="1"))

    assert result.price is None
    svc.pricing_service.calculate.assert_not_awaited()
    svc.order_repo.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_set_pickup_changed_address_recalculates_price(svc: OrderService) -> None:
    """set_pickup: при наличии обоих адресов цена пересчитывается и сохраняется."""
    order = build_priced_draft(pickup_street_id=3, destination_street_id=11)
    order.price = 400
    svc.order_repo.get_by_id.return_value = order
    svc.address_service.resolve_address.return_value = resolved_address(street_id=77, house_id=88)
    svc.pricing_service.calculate.return_value = 1500

    result = await svc.set_pickup(order_id=order.id, address_data=AddressInput(street="новая", house="1"))

    assert result.price == 1500
    svc.pricing_service.calculate.assert_awaited_once()
    svc.order_repo.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_set_pickup_same_candidate_does_not_recalculate_price(svc: OrderService) -> None:
    """set_pickup: одинаковый кандидат не вызывает пересчёт цены."""
    order = build_priced_draft(pickup_street_id=3, destination_street_id=11)
    svc.order_repo.get_by_id.return_value = order
    svc.address_service.resolve_address.return_value = resolved_address(street_id=3, house_id=4)

    result = await svc.set_pickup(order_id=order.id, address_data=AddressInput(street="ленина", house="5"))

    assert result.price == 1000  # цена не трогалась
    svc.pricing_service.calculate.assert_not_awaited()


@pytest.mark.asyncio
async def test_set_pickup_pricing_returns_none_raises_pricing_error(svc: OrderService) -> None:
    """set_pickup: если calculate вернул None -> PricingError, commit не вызван."""
    order = build_priced_draft(pickup_street_id=3)
    svc.order_repo.get_by_id.return_value = order
    svc.address_service.resolve_address.return_value = resolved_address(street_id=77)
    svc.pricing_service.calculate.return_value = None

    with pytest.raises(PricingError):
        await svc.set_pickup(order_id=order.id, address_data=AddressInput(street="новая", house="1"))

    svc.order_repo.commit.assert_not_awaited()


# --- Retry: set_pickup ---


@pytest.mark.asyncio
async def test_set_pickup_retries_after_stale_data(svc: OrderService) -> None:
    """set_pickup: первый commit -> StaleDataError, повтор успешен (Order перечитывается)."""
    svc.order_repo.get_by_id.side_effect = lambda *a, **k: build_draft_order()
    svc.address_service.resolve_address.return_value = resolved_address()
    svc.order_repo.commit.side_effect = [StaleDataError(), None]

    result = await svc.set_pickup(order_id=uuid4(), address_data=AddressInput(street="ленина", house="5"))

    assert result.pickup_street_id == 3  # применён на свежем заказе второй попытки
    assert svc.order_repo.commit.await_count == 2
    svc.order_repo.rollback.assert_awaited_once()


@pytest.mark.asyncio
async def test_set_pickup_exhausts_retries_after_three_stale(svc: OrderService) -> None:
    """set_pickup: три StaleDataError подряд -> ошибка пробрасывается после retry."""
    svc.order_repo.get_by_id.side_effect = lambda *a, **k: build_draft_order()
    svc.address_service.resolve_address.return_value = resolved_address()
    svc.order_repo.commit.side_effect = [StaleDataError(), StaleDataError(), StaleDataError()]

    with pytest.raises(StaleDataError):
        await svc.set_pickup(order_id=uuid4(), address_data=AddressInput(street="ленина", house="5"))

    assert svc.order_repo.rollback.await_count == 3


@pytest.mark.asyncio
async def test_set_pickup_retry_reloads_order(svc: OrderService) -> None:
    """set_pickup: при retry заказ перечитывается из репозитория."""
    original = build_draft_order(street_id=1)
    reloaded = build_draft_order(street_id=2)
    svc.order_repo.get_by_id.side_effect = [original, original, reloaded]
    svc.address_service.resolve_address.return_value = resolved_address()
    svc.order_repo.commit.side_effect = [StaleDataError(), None]

    result = await svc.set_pickup(order_id=original.id, address_data=AddressInput(street="ленина", house="5"))

    assert result is reloaded
    assert svc.order_repo.get_by_id.await_count == 3
# ---------------------------------------------------------------------------
# SET_DESTINATION
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_set_destination_order_not_found_raises(svc: OrderService) -> None:
    """set_destination: заказ не найден -> OrderNotFoundError."""
    svc.order_repo.get_by_id.return_value = None

    with pytest.raises(OrderNotFoundError):
        await svc.set_destination(order_id=uuid4(), address_data=AddressInput(street="гагарина", house="10"))


@pytest.mark.asyncio
async def test_set_destination_invalid_state_raises(svc: OrderService) -> None:
    """set_destination: заказ не в DRAFT -> InvalidStateError."""
    order = build_draft_order(state=OrderState.ASSIGNED)
    svc.order_repo.get_by_id.return_value = order

    with pytest.raises(InvalidStateError):
        await svc.set_destination(order_id=order.id, address_data=AddressInput(street="гагарина", house="10"))


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "status",
    [AddressStatus.NOT_FOUND, AddressStatus.AMBIGUOUS, AddressStatus.INCOMPLETE],
)
async def test_set_destination_raises_address_resolve_error(svc: OrderService, status) -> None:
    """set_destination: не-разрешённый адрес -> AddressResolveError с тем же статусом."""
    order = build_draft_order()
    svc.order_repo.get_by_id.return_value = order
    svc.address_service.resolve_address.return_value = error_address(status, reason="bad")

    with pytest.raises(AddressResolveError) as exc_info:
        await svc.set_destination(order_id=order.id, address_data=AddressInput(street="10"))

    assert exc_info.value.status == status
    svc.order_repo.commit.assert_not_awaited()


@pytest.mark.asyncio
async def test_set_destination_applies_full_candidate(svc: OrderService) -> None:
    """set_destination: RESOLVED полностью заполняет destination и *_id."""
    order = build_draft_order()
    svc.order_repo.get_by_id.return_value = order
    candidate = build_candidate(
        town_id=10, town_name="уфа",
        district_id=20, district_name="советский",
        street_id=30, street_name="гагарина",
        house_id=40, house_number="10",
        landmark_id=None, landmark_name=None,
    )
    svc.address_service.resolve_address.return_value = AddressMatchResult(
        status=AddressStatus.RESOLVED, candidates=[candidate]
    )

    result = await svc.set_destination(order_id=order.id, address_data=AddressInput(street="гагарина", house="10"))

    assert result.destination_town == "уфа"
    assert result.destination_town_id == 10
    assert result.destination_district == "советский"
    assert result.destination_district_id == 20
    assert result.destination_street == "гагарина"
    assert result.destination_street_id == 30
    assert result.destination_house == "10"
    assert result.destination_house_id == 40
    assert result.destination_landmark_id is None
    assert result.destination_landmark is None
    svc.order_repo.commit.assert_awaited_once()
@pytest.mark.asyncio
async def test_set_destination_same_address_does_not_change_order(svc: OrderService) -> None:
    """set_destination: тот же адрес — без изменений заказа и без commit."""
    order = build_draft_order(
        destination_town="аскарово", destination_town_id=1,
        destination_district="центр", destination_district_id=2,
        destination_street="гагарина", destination_street_id=11,
        destination_house="10", destination_house_id=14,
        price=1000,
    )
    svc.order_repo.get_by_id.return_value = order
    svc.address_service.resolve_address.return_value = resolved_address(street_id=11, house_id=14)

    result = await svc.set_destination(order_id=order.id, address_data=AddressInput(street="гагарина", house="10"))

    assert result is order
    assert order.price == 1000
    svc.order_repo.commit.assert_not_awaited()
    svc.pricing_service.calculate.assert_not_awaited()


@pytest.mark.asyncio
async def test_set_destination_changed_address_resets_price_to_none(svc: OrderService) -> None:
    """set_destination: изменение адреса сбрасывает price; без pickup price=None."""
    order = build_draft_order(destination_street_id=11, price=1000)
    svc.order_repo.get_by_id.return_value = order
    svc.address_service.resolve_address.return_value = resolved_address(street_id=98, house_id=97)

    result = await svc.set_destination(order_id=order.id, address_data=AddressInput(street="новая", house="1"))

    assert result.price is None
    svc.pricing_service.calculate.assert_not_awaited()


@pytest.mark.asyncio
async def test_set_destination_changed_address_recalculates_price(svc: OrderService) -> None:
    """set_destination: при наличии обоих адресов цена пересчитывается."""
    order = build_priced_draft(pickup_street_id=3, destination_street_id=11)
    order.price = 400
    svc.order_repo.get_by_id.return_value = order
    svc.address_service.resolve_address.return_value = resolved_address(street_id=98, house_id=97)
    svc.pricing_service.calculate.return_value = 900

    result = await svc.set_destination(order_id=order.id, address_data=AddressInput(street="новая", house="1"))

    assert result.price == 900
    svc.pricing_service.calculate.assert_awaited_once()


# --- Retry: set_destination ---


@pytest.mark.asyncio
async def test_set_destination_retries_after_stale_data(svc: OrderService) -> None:
    """set_destination: StaleDataError -> rollback -> повторный commit успешен."""
    svc.order_repo.get_by_id.side_effect = lambda *a, **k: build_draft_order()
    svc.address_service.resolve_address.return_value = resolved_address()
    svc.order_repo.commit.side_effect = [StaleDataError(), None]

    result = await svc.set_destination(order_id=uuid4(), address_data=AddressInput(street="гагарина", house="10"))

    assert result.destination_street_id == 3  # применён на свежем заказе второй попытки
    assert svc.order_repo.commit.await_count == 2
    svc.order_repo.rollback.assert_awaited_once()


@pytest.mark.asyncio
async def test_set_destination_exhausts_retries(svc: OrderService) -> None:
    """set_destination: три StaleDataError -> ошибка пробрасывается."""
    svc.order_repo.get_by_id.side_effect = lambda *a, **k: build_draft_order()
    svc.address_service.resolve_address.return_value = resolved_address()
    svc.order_repo.commit.side_effect = [StaleDataError(), StaleDataError(), StaleDataError()]

    with pytest.raises(StaleDataError):
        await svc.set_destination(order_id=uuid4(), address_data=AddressInput(street="гагарина", house="10"))

    assert svc.order_repo.rollback.await_count == 3


@pytest.mark.asyncio
async def test_set_destination_retry_reloads_order(svc: OrderService) -> None:
    """set_destination: при retry заказ перечитывается из репозитория."""
    original = build_draft_order()
    reloaded = build_draft_order()
    svc.order_repo.get_by_id.side_effect = [original, original, reloaded]
    svc.address_service.resolve_address.return_value = resolved_address()
    svc.order_repo.commit.side_effect = [StaleDataError(), None]

    result = await svc.set_destination(order_id=original.id, address_data=AddressInput(street="гагарина", house="10"))

    assert result is reloaded
    assert svc.order_repo.get_by_id.await_count == 3
# ---------------------------------------------------------------------------
# ADD_WAYPOINT
# ---------------------------------------------------------------------------

# NOTE production-bug: add_waypoint при превышении лимита бросает TypeError, а не
# LimitWaypointError, из-за запятой в ``raise (LimitWaypointError(...),)``.
# Тесты под фактическое поведение; проблема вынесена в финальный отчёт.


@pytest.mark.asyncio
async def test_add_waypoint_order_not_found_raises(svc: OrderService) -> None:
    """add_waypoint: заказ не найден -> OrderNotFoundError."""
    svc.order_repo.get_by_id.return_value = None

    with pytest.raises(OrderNotFoundError):
        await svc.add_waypoint(order_id=uuid4(), address_data=AddressInput(street="кирова", house="1"))


@pytest.mark.asyncio
async def test_add_waypoint_invalid_state_raises(svc: OrderService) -> None:
    """add_waypoint: заказ не в DRAFT -> InvalidStateError."""
    order = build_draft_order(state=OrderState.CONFIRMED)
    svc.order_repo.get_by_id.return_value = order

    with pytest.raises(InvalidStateError):
        await svc.add_waypoint(order_id=order.id, address_data=AddressInput(street="кирова", house="1"))


@pytest.mark.asyncio
async def test_add_waypoint_assigns_incremental_sequence_and_keeps_existing(
    svc: OrderService,
) -> None:
    """add_waypoint: последовательность sequence_number инкрементная, старые сохранены."""
    order = build_priced_draft()
    add_waypoints(order, 2)  # существующие waypoint 1,2
    svc.order_repo.get_by_id.return_value = order
    svc.address_service.resolve_address.return_value = resolved_address(
        street_id=333, house_id=444, street_name="кирова"
    )

    result = await svc.add_waypoint(order_id=order.id, address_data=AddressInput(street="кирова", house="9"))

    assert len(result.waypoints) == 3
    sequences = [wp.sequence_number for wp in sorted(result.waypoints, key=lambda w: w.sequence_number)]
    assert sequences == [1, 2, 3]
    # Новый waypoint последний с sequence=3.
    new_wp = next(wp for wp in result.waypoints if wp.waypoint_street_id == 333)
    assert new_wp.sequence_number == 3
    svc.order_repo.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_add_waypoint_fills_full_address_and_ids(svc: OrderService) -> None:
    """add_waypoint: адрес и все *_id waypoint заполняются из candidate."""
    order = build_priced_draft()
    svc.order_repo.get_by_id.return_value = order
    candidate = build_candidate(
        town_id=10, town_name="уфа", district_id=20, district_name="советский",
        street_id=30, street_name="кирова", house_id=40, house_number="9",
        landmark_id=50, landmark_name="театр",
    )
    svc.address_service.resolve_address.return_value = AddressMatchResult(
        status=AddressStatus.RESOLVED, candidates=[candidate]
    )

    result = await svc.add_waypoint(order_id=order.id, address_data=AddressInput(street="кирова", house="9"))

    wp = next(w for w in result.waypoints if w.waypoint_town == "уфа")
    assert wp.waypoint_town_id == 10
    assert wp.waypoint_district == "советский"
    assert wp.waypoint_district_id == 20
    assert wp.waypoint_street == "кирова"
    assert wp.waypoint_street_id == 30
    assert wp.waypoint_house == "9"
    assert wp.waypoint_house_id == 40
    assert wp.waypoint_landmark == "театр"
    assert wp.waypoint_landmark_id == 50


@pytest.mark.asyncio
async def test_add_waypoint_resets_price(svc: OrderService) -> None:
    """add_waypoint: сбрасывает price; без обоих адресов пересчёт не вызывается."""
    order = build_draft_order(pickup_street_id=3, price=777)
    svc.order_repo.get_by_id.return_value = order
    svc.address_service.resolve_address.return_value = resolved_address()

    result = await svc.add_waypoint(order_id=order.id, address_data=AddressInput(street="кирова", house="1"))

    assert result.price is None
    svc.pricing_service.calculate.assert_not_awaited()


@pytest.mark.asyncio
async def test_add_waypoint_recalculates_price_when_both_addresses(svc: OrderService) -> None:
    """add_waypoint: при обоих основных адресах цена пересчитывается."""
    order = build_priced_draft()
    svc.order_repo.get_by_id.return_value = order
    svc.address_service.resolve_address.return_value = resolved_address(street_id=333)
    svc.pricing_service.calculate.return_value = 1200

    result = await svc.add_waypoint(order_id=order.id, address_data=AddressInput(street="кирова", house="1"))

    assert result.price == 1200
    svc.pricing_service.calculate.assert_awaited_once()


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "status",
    [AddressStatus.NOT_FOUND, AddressStatus.AMBIGUOUS, AddressStatus.INCOMPLETE],
)
async def test_add_waypoint_raises_address_resolve_error(svc: OrderService, status) -> None:
    """add_waypoint: плохой адрес -> AddressResolveError, waypoint не добавлен."""
    order = build_draft_order()
    svc.order_repo.get_by_id.return_value = order
    svc.address_service.resolve_address.return_value = error_address(status, reason="bad")

    with pytest.raises(AddressResolveError) as exc_info:
        await svc.add_waypoint(order_id=order.id, address_data=AddressInput(street="кирова", house="1"))

    assert exc_info.value.status == status
    assert order.waypoints == []
    svc.order_repo.commit.assert_not_awaited()
@pytest.mark.asyncio
async def test_add_waypoint_over_limit_raises_limit_waypoint_error(svc: OrderService) -> None:
    """add_waypoint: при достижении лимита бросается LimitWaypointError.

    Production-код бросает LimitWaypointError корректно (запятая-кортеж из
    старой версии убрана). Ничего в заказе не меняется, commit не вызывается.
    """
    order = build_priced_draft()
    add_waypoints(order, svc.config_settings.MAX_WAYPOINTS)  # лимит исчерпан
    svc.order_repo.get_by_id.return_value = order
    svc.address_service.resolve_address.return_value = resolved_address()

    with pytest.raises(LimitWaypointError):
        await svc.add_waypoint(order_id=order.id, address_data=AddressInput(street="кирова", house="9"))

    assert len(order.waypoints) == svc.config_settings.MAX_WAYPOINTS
    svc.order_repo.commit.assert_not_awaited()


@pytest.mark.asyncio
async def test_add_waypoint_retries_after_stale_data(svc: OrderService) -> None:
    """add_waypoint: StaleDataError -> rollback -> повтор успешен."""
    svc.order_repo.get_by_id.side_effect = lambda *a, **k: build_priced_draft()
    svc.address_service.resolve_address.return_value = resolved_address(street_id=333)
    svc.pricing_service.calculate.return_value = 100
    svc.order_repo.commit.side_effect = [StaleDataError(), None]

    result = await svc.add_waypoint(order_id=uuid4(), address_data=AddressInput(street="кирова", house="9"))

    assert len(result.waypoints) == 1
    assert svc.order_repo.commit.await_count == 2
    svc.order_repo.rollback.assert_awaited_once()


@pytest.mark.asyncio
async def test_add_waypoint_retry_reloads_order_for_sequence(svc: OrderService) -> None:
    """add_waypoint: retry перечитывает заказ, sequence считается на актуальном Order."""
    original = build_priced_draft()
    add_waypoints(original, 1)
    reloaded = build_priced_draft()
    add_waypoints(reloaded, 2)  # актуальный заказ уже имеет 2 waypoint
    svc.order_repo.get_by_id.side_effect = [original, original, reloaded]
    svc.address_service.resolve_address.return_value = resolved_address(
        street_id=333, street_name="кирова"
    )
    svc.pricing_service.calculate.return_value = 100
    svc.order_repo.commit.side_effect = [StaleDataError(), None]

    result = await svc.add_waypoint(order_id=original.id, address_data=AddressInput(street="кирова", house="9"))

    assert result is reloaded
    assert len(reloaded.waypoints) == 3
    new_wp = next(wp for wp in reloaded.waypoints if wp.waypoint_street_id == 333)
    assert new_wp.sequence_number == 3


@pytest.mark.asyncio
async def test_add_waypoint_exhausts_retries(svc: OrderService) -> None:
    """add_waypoint: три StaleDataError -> ошибка пробрасывается."""
    order = build_priced_draft()
    svc.order_repo.get_by_id.return_value = order
    svc.address_service.resolve_address.return_value = resolved_address()
    svc.order_repo.commit.side_effect = [StaleDataError(), StaleDataError(), StaleDataError()]

    with pytest.raises(StaleDataError):
        await svc.add_waypoint(order_id=order.id, address_data=AddressInput(street="кирова", house="9"))

    assert svc.order_repo.rollback.await_count == 3
# ---------------------------------------------------------------------------
# UPDATE_WAYPOINT
# ---------------------------------------------------------------------------


def _order_with_three_waypoints() -> Order:
    order = build_priced_draft()
    add_waypoints(order, 3)
    return order


@pytest.mark.asyncio
async def test_update_waypoint_order_not_found_raises(svc: OrderService) -> None:
    """update_waypoint: заказ не найден -> OrderNotFoundError."""
    svc.order_repo.get_by_id.return_value = None
    svc.address_service.resolve_address.return_value = resolved_address()

    with pytest.raises(OrderNotFoundError):
        await svc.update_waypoint(
            order_id=uuid4(), sequence_number=1, address_data=AddressInput(street="кирова", house="1")
        )
    svc.order_repo.commit.assert_not_awaited()


@pytest.mark.asyncio
async def test_update_waypoint_invalid_state_raises(svc: OrderService) -> None:
    """update_waypoint: заказ не в DRAFT -> InvalidStateError."""
    order = build_draft_order(state=OrderState.CONFIRMED)
    svc.order_repo.get_by_id.return_value = order
    svc.address_service.resolve_address.return_value = resolved_address()

    with pytest.raises(InvalidStateError):
        await svc.update_waypoint(
            order_id=order.id, sequence_number=1, address_data=AddressInput(street="кирова", house="1")
        )


@pytest.mark.asyncio
@pytest.mark.parametrize("sequence_number", [1, 2, 3])
async def test_update_waypoint_updates_first_middle_last(svc: OrderService, sequence_number: int) -> None:
    """update_waypoint: обновление первого/среднего/последнего waypoint по sequence."""
    order = _order_with_three_waypoints()
    svc.order_repo.get_by_id.return_value = order
    svc.address_service.resolve_address.return_value = resolved_address(
        street_id=999, street_name="кирова", house_id=888, house_number="77"
    )

    result = await svc.update_waypoint(
        order_id=order.id,
        sequence_number=sequence_number,
        address_data=AddressInput(street="кирова", house="77"),
    )

    updated = next(wp for wp in result.waypoints if wp.sequence_number == sequence_number)
    assert updated.waypoint_street == "кирова"
    assert updated.waypoint_street_id == 999
    assert updated.waypoint_house == "77"
    assert updated.waypoint_house_id == 888
    # sequence_number сохраняется
    assert updated.sequence_number == sequence_number
    # остальные не тронуты и сохранены
    assert len(result.waypoints) == 3
    svc.order_repo.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_update_waypoint_nonexistent_sequence_raises(svc: OrderService) -> None:
    """update_waypoint: несуществующий sequence_number -> WaypointNotFoundError."""
    order = _order_with_three_waypoints()
    svc.order_repo.get_by_id.return_value = order
    svc.address_service.resolve_address.return_value = resolved_address()

    with pytest.raises(WaypointNotFoundError):
        await svc.update_waypoint(
            order_id=order.id, sequence_number=99, address_data=AddressInput(street="кирова", house="1")
        )
    svc.order_repo.commit.assert_not_awaited()


@pytest.mark.asyncio
async def test_update_waypoint_replaces_all_address_fields_and_ids(svc: OrderService) -> None:
    """update_waypoint: старые поля/ids полностью заменяются новыми."""
    order = _order_with_three_waypoints()
    svc.order_repo.get_by_id.return_value = order
    candidate = build_candidate(
        town_id=10, town_name="уфа", district_id=20, district_name="советский",
        street_id=30, street_name="кирова", house_id=40, house_number="9",
        landmark_id=50, landmark_name="вокзал",
    )
    svc.address_service.resolve_address.return_value = AddressMatchResult(
        status=AddressStatus.RESOLVED, candidates=[candidate]
    )

    result = await svc.update_waypoint(
        order_id=order.id, sequence_number=1, address_data=AddressInput(street="кирова", house="9")
    )

    updated = next(wp for wp in result.waypoints if wp.sequence_number == 1)
    assert updated.waypoint_town == "уфа"
    assert updated.waypoint_town_id == 10
    assert updated.waypoint_district == "советский"
    assert updated.waypoint_district_id == 20
    assert updated.waypoint_street_id == 30
    assert updated.waypoint_house_id == 40
    assert updated.waypoint_landmark == "вокзал"
    assert updated.waypoint_landmark_id == 50


@pytest.mark.asyncio
async def test_update_waypoint_keeps_other_waypoints(svc: OrderService) -> None:
    """update_waypoint: другие waypoint и их последовательность не меняются."""
    order = _order_with_three_waypoints()
    svc.order_repo.get_by_id.return_value = order
    svc.address_service.resolve_address.return_value = resolved_address(street_id=600, street_name="кирова")

    result = await svc.update_waypoint(
        order_id=order.id, sequence_number=2, address_data=AddressInput(street="кирова", house="1")
    )

    other = [wp for wp in result.waypoints if wp.sequence_number != 2]
    assert other[0].waypoint_street_id == 101  # 1-й старый остался
    assert other[1].waypoint_street_id == 103  # 3-й старый остался
    assert sorted(wp.sequence_number for wp in result.waypoints) == [1, 2, 3]


@pytest.mark.asyncio
async def test_update_waypoint_resets_price(svc: OrderService) -> None:
    """update_waypoint: сбрасывает price при отсутствии обоих адресов."""
    order = build_draft_order(pickup_street_id=3, price=500)
    add_waypoints(order, 1)
    svc.order_repo.get_by_id.return_value = order
    svc.address_service.resolve_address.return_value = resolved_address(street_id=555)

    result = await svc.update_waypoint(
        order_id=order.id, sequence_number=1, address_data=AddressInput(street="кирова", house="1")
    )

    assert result.price is None
    svc.pricing_service.calculate.assert_not_awaited()
@pytest.mark.asyncio
async def test_update_waypoint_recalculates_price(svc: OrderService) -> None:
    """update_waypoint: при обоих адресах цена пересчитывается."""
    order = build_priced_draft()
    add_waypoints(order, 1)
    order.price = 555
    svc.order_repo.get_by_id.return_value = order
    svc.address_service.resolve_address.return_value = resolved_address(street_id=555)
    svc.pricing_service.calculate.return_value = 1300

    result = await svc.update_waypoint(
        order_id=order.id, sequence_number=1, address_data=AddressInput(street="кирова", house="1")
    )

    assert result.price == 1300
    svc.pricing_service.calculate.assert_awaited_once()


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "status",
    [AddressStatus.NOT_FOUND, AddressStatus.AMBIGUOUS, AddressStatus.INCOMPLETE],
)
async def test_update_waypoint_raises_address_resolve_error(svc: OrderService, status) -> None:
    """update_waypoint: плохой адрес -> AddressResolveError, waypoint не менялся."""
    order = _order_with_three_waypoints()
    svc.order_repo.get_by_id.return_value = order
    svc.address_service.resolve_address.return_value = error_address(status, reason="bad")

    with pytest.raises(AddressResolveError) as exc_info:
        await svc.update_waypoint(
            order_id=order.id, sequence_number=1, address_data=AddressInput(street="кирова", house="1")
        )

    assert exc_info.value.status == status
    assert all(wp.waypoint_street_id in (101, 102, 103) for wp in order.waypoints)
    svc.order_repo.commit.assert_not_awaited()


@pytest.mark.asyncio
async def test_update_waypoint_not_blocked_by_max_waypoints(svc: OrderService) -> None:
    """update_waypoint: достижение MAX_WAYPOINTS НЕ запрещает обновление существующего."""
    order = build_priced_draft()
    add_waypoints(order, svc.config_settings.MAX_WAYPOINTS)  # лимит исчерпан
    svc.order_repo.get_by_id.return_value = order
    svc.address_service.resolve_address.return_value = resolved_address(street_id=555, street_name="кирова")

    result = await svc.update_waypoint(
        order_id=order.id,
        sequence_number=svc.config_settings.MAX_WAYPOINTS,
        address_data=AddressInput(street="кирова", house="1"),
    )

    updated = next(wp for wp in result.waypoints if wp.sequence_number == svc.config_settings.MAX_WAYPOINTS)
    assert updated.waypoint_street_id == 555
    svc.order_repo.commit.assert_awaited_once()


# --- Retry: update_waypoint ---


@pytest.mark.asyncio
async def test_update_waypoint_retries_after_stale_data(svc: OrderService) -> None:
    """update_waypoint: StaleDataError -> reload -> повтор успешен."""
    svc.order_repo.get_by_id.side_effect = lambda *a, **k: _order_with_three_waypoints()
    svc.address_service.resolve_address.return_value = resolved_address(street_id=555)
    svc.pricing_service.calculate.return_value = 100
    svc.order_repo.commit.side_effect = [StaleDataError(), None]

    result = await svc.update_waypoint(
        order_id=uuid4(), sequence_number=1, address_data=AddressInput(street="кирова", house="1")
    )

    updated = next(wp for wp in result.waypoints if wp.sequence_number == 1)
    assert updated.waypoint_street_id == 555
    assert svc.order_repo.commit.await_count == 2
    svc.order_repo.rollback.assert_awaited_once()


@pytest.mark.asyncio
async def test_update_waypoint_retry_updates_actual_waypoint(svc: OrderService) -> None:
    """update_waypoint: после retry обновляется waypoint на актуальном Order."""
    original = _order_with_three_waypoints()
    reloaded = _order_with_three_waypoints()
    reloaded.waypoints[1].waypoint_street_id = 42  # актуальные данные отличаются
    svc.order_repo.get_by_id.side_effect = [original, reloaded]
    svc.address_service.resolve_address.return_value = resolved_address(street_id=555)
    svc.order_repo.commit.side_effect = [StaleDataError(), None]

    result = await svc.update_waypoint(
        order_id=original.id, sequence_number=2, address_data=AddressInput(street="кирова", house="1")
    )

    assert result is reloaded
    updated = next(wp for wp in reloaded.waypoints if wp.sequence_number == 2)
    assert updated.waypoint_street_id == 555
    assert svc.order_repo.get_by_id.await_count == 2


@pytest.mark.asyncio
async def test_update_waypoint_exhausts_retries(svc: OrderService) -> None:
    """update_waypoint: три StaleDataError -> ошибка пробрасывается."""
    order = _order_with_three_waypoints()
    svc.order_repo.get_by_id.return_value = order
    svc.address_service.resolve_address.return_value = resolved_address()
    svc.order_repo.commit.side_effect = [StaleDataError(), StaleDataError(), StaleDataError()]

    with pytest.raises(StaleDataError):
        await svc.update_waypoint(
            order_id=order.id, sequence_number=1, address_data=AddressInput(street="кирова", house="1")
        )

    assert svc.order_repo.rollback.await_count == 3
# ---------------------------------------------------------------------------
# REMOVE_WAYPOINT
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_remove_waypoint_order_not_found_raises(svc: OrderService) -> None:
    """remove_waypoint: заказ не найден -> OrderNotFoundError."""
    svc.order_repo.get_by_id.return_value = None

    with pytest.raises(OrderNotFoundError):
        await svc.remove_waypoint(order_id=uuid4(), sequence_number=1)


@pytest.mark.asyncio
async def test_remove_waypoint_invalid_state_raises(svc: OrderService) -> None:
    """remove_waypoint: заказ не в DRAFT -> InvalidStateError."""
    order = _order_with_three_waypoints()
    order.state = OrderState.CONFIRMED
    svc.order_repo.get_by_id.return_value = order

    with pytest.raises(InvalidStateError):
        await svc.remove_waypoint(order_id=order.id, sequence_number=1)


@pytest.mark.asyncio
async def test_remove_waypoint_nonexistent_sequence_raises(svc: OrderService) -> None:
    """remove_waypoint: несуществующий sequence_number -> WaypointNotFoundError."""
    order = _order_with_three_waypoints()
    svc.order_repo.get_by_id.return_value = order

    with pytest.raises(WaypointNotFoundError):
        await svc.remove_waypoint(order_id=order.id, sequence_number=99)

    assert len(order.waypoints) == 3
    svc.order_repo.commit.assert_not_awaited()


@pytest.mark.asyncio
async def test_remove_waypoint_single_removes_only_waypoint(svc: OrderService) -> None:
    """remove_waypoint: удаление единственного waypoint оставляет пустой список."""
    order = build_priced_draft()
    add_waypoints(order, 1)
    svc.order_repo.get_by_id.return_value = order

    result = await svc.remove_waypoint(order_id=order.id, sequence_number=1)

    assert result is order
    assert result.waypoints == []
    svc.order_repo.commit.assert_awaited_once()


@pytest.mark.asyncio
@pytest.mark.parametrize("sequence_number", [1, 2, 3])
async def test_remove_waypoint_first_middle_last_and_renumbers(
    svc: OrderService, sequence_number: int
) -> None:
    """remove_waypoint: удаление первого/среднего/последнего, остальные перенумерованы 1..N."""
    order = _order_with_three_waypoints()
    svc.order_repo.get_by_id.return_value = order

    result = await svc.remove_waypoint(order_id=order.id, sequence_number=sequence_number)

    assert len(result.waypoints) == 2
    sequences = sorted(wp.sequence_number for wp in result.waypoints)
    assert sequences == [1, 2]  # без дыр, непрерывны
    svc.order_repo.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_remove_waypoint_w2_of_w1w2w3_yields_w1w2_w3_renumbered(
    svc: OrderService,
) -> None:
    """remove_waypoint: удаление W2 из W1,W2,W3 даёт W1 (seq1) и старый W3 (seq2)."""
    order = _order_with_three_waypoints()
    svc.order_repo.get_by_id.return_value = order

    result = await svc.remove_waypoint(order_id=order.id, sequence_number=2)

    remaining = sorted(result.waypoints, key=lambda wp: wp.sequence_number)
    assert [wp.sequence_number for wp in remaining] == [1, 2]
    # Старый waypoint #1 (street_id 101) остался с sequence 1.
    assert remaining[0].waypoint_street_id == 101
    # Старый waypoint #3 (street_id 103) теперь имеет sequence 2.
    assert remaining[1].waypoint_street_id == 103
    assert remaining[1].sequence_number == 2
@pytest.mark.asyncio
async def test_remove_waypoint_resets_price(svc: OrderService) -> None:
    """remove_waypoint: сбрасывает price при неполных основных адресах."""
    order = build_draft_order(pickup_street_id=3, price=900)
    add_waypoints(order, 2)
    svc.order_repo.get_by_id.return_value = order

    result = await svc.remove_waypoint(order_id=order.id, sequence_number=1)

    assert result.price is None
    svc.pricing_service.calculate.assert_not_awaited()


@pytest.mark.asyncio
async def test_remove_waypoint_recalculates_price(svc: OrderService) -> None:
    """remove_waypoint: при обоих адресах цена пересчитывается."""
    order = build_priced_draft()
    add_waypoints(order, 2)
    order.price = 555
    svc.order_repo.get_by_id.return_value = order
    svc.pricing_service.calculate.return_value = 700

    result = await svc.remove_waypoint(order_id=order.id, sequence_number=1)

    assert result.price == 700
    svc.pricing_service.calculate.assert_awaited_once()
    assert len(result.waypoints) == 1


# --- Retry: remove_waypoint ---


@pytest.mark.asyncio
async def test_remove_waypoint_retries_after_stale_data(svc: OrderService) -> None:
    """remove_waypoint: StaleDataError -> retry -> повтор успешен."""
    svc.order_repo.get_by_id.side_effect = lambda *a, **k: _order_with_three_waypoints()
    svc.pricing_service.calculate.return_value = 100
    svc.order_repo.commit.side_effect = [StaleDataError(), None]

    result = await svc.remove_waypoint(order_id=uuid4(), sequence_number=1)

    assert len(result.waypoints) == 2
    assert svc.order_repo.commit.await_count == 2
    svc.order_repo.rollback.assert_awaited_once()


@pytest.mark.asyncio
async def test_remove_waypoint_retry_reloads_order_and_renumbers(svc: OrderService) -> None:
    """remove_waypoint: после retry обновление на актуальном Order с перенумерацией."""
    original = _order_with_three_waypoints()
    reloaded = _order_with_three_waypoints()
    svc.order_repo.get_by_id.side_effect = [original, reloaded]
    svc.order_repo.commit.side_effect = [StaleDataError(), None]

    result = await svc.remove_waypoint(order_id=original.id, sequence_number=2)

    assert result is reloaded
    assert sorted(wp.sequence_number for wp in reloaded.waypoints) == [1, 2]


@pytest.mark.asyncio
async def test_remove_waypoint_exhausts_retries(svc: OrderService) -> None:
    """remove_waypoint: три StaleDataError -> ошибка пробрасывается."""
    order = _order_with_three_waypoints()
    svc.order_repo.get_by_id.return_value = order
    svc.order_repo.commit.side_effect = [StaleDataError(), StaleDataError(), StaleDataError()]

    with pytest.raises(StaleDataError):
        await svc.remove_waypoint(order_id=order.id, sequence_number=1)

    assert svc.order_repo.rollback.await_count == 3
# ---------------------------------------------------------------------------
# SET_PASSENGER_NAME
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_set_passenger_name_stores_normalized_value(svc: OrderService) -> None:
    """set_passenger_name: сохраняет нормализованное (PassengerName) имя в order."""
    order = build_draft_order()
    svc.order_repo.get_by_id.return_value = order

    result = await svc.set_passenger_name(
        order_id=order.id, name=PassengerName(first_name="иван иванович")
    )

    assert result is order
    assert order.passenger_name == "Иван Иванович"
    svc.order_repo.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_set_passenger_name_order_not_found_raises(svc: OrderService) -> None:
    """set_passenger_name: заказ не найден -> OrderNotFoundError."""
    svc.order_repo.get_by_id.return_value = None

    with pytest.raises(OrderNotFoundError):
        await svc.set_passenger_name(order_id=uuid4(), name=PassengerName(first_name="Иван"))


@pytest.mark.asyncio
async def test_set_passenger_name_does_not_validate_state_current_behavior(
    svc: OrderService,
) -> None:
    """set_passenger_name теперь НЕ проверяет state — фиксируем фактическое поведение.

    В отличие от set_pickup/set_destination, эта операция допустима и для
    не-DRAFT заказа. Это потенциальная бизнес-ошибка; см. финальный отчёт.
    """
    order = build_draft_order(state=OrderState.CONFIRMED)
    svc.order_repo.get_by_id.return_value = order

    result = await svc.set_passenger_name(order_id=order.id, name=PassengerName(first_name="Петр"))

    assert result is order
    assert order.passenger_name == "Петр"
    svc.order_repo.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_set_passenger_name_retries_after_stale_data(svc: OrderService) -> None:
    """set_passenger_name: StaleDataError -> retry -> повтор успешен."""
    order = build_draft_order()
    svc.order_repo.get_by_id.return_value = order
    svc.order_repo.commit.side_effect = [StaleDataError(), None]

    result = await svc.set_passenger_name(order_id=order.id, name=PassengerName(first_name="Иван"))

    assert result is order
    assert order.passenger_name == "Иван"
    assert svc.order_repo.commit.await_count == 2
    svc.order_repo.rollback.assert_awaited_once()


@pytest.mark.asyncio
async def test_set_passenger_name_retry_reloads_order(svc: OrderService) -> None:
    """set_passenger_name: при retry заказ перечитывается заново (get_by_id на каждой итерации).

    Production-код теперь вызывает ``get_by_id`` внутри retry-цикла,
    поэтому Order загружается на каждой попытке.
    """
    order = build_draft_order()
    svc.order_repo.get_by_id.return_value = order
    svc.order_repo.commit.side_effect = [StaleDataError(), None]

    result = await svc.set_passenger_name(order_id=order.id, name=PassengerName(first_name="Иван"))

    assert result is order
    assert order.passenger_name == "Иван"
    assert svc.order_repo.get_by_id.await_count == 2
    assert svc.order_repo.commit.await_count == 2
    svc.order_repo.rollback.assert_awaited_once()


# ---------------------------------------------------------------------------
# SET_COMMENT
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_set_comment_stores_normalized_value(svc: OrderService) -> None:
    """set_comment: сохраняет нормализованный (OrderComment) комментарий."""
    order = build_draft_order()
    svc.order_repo.get_by_id.return_value = order

    result = await svc.set_comment(
        order_id=order.id, comment=OrderComment(comment="  позвоните   перед подачей  ")
    )

    assert result is order
    assert order.comment == "позвоните перед подачей"
    svc.order_repo.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_set_comment_order_not_found_raises_order_not_found(
    svc: OrderService,
) -> None:
    """set_comment: заказ не найден -> OrderNotFoundError.

    Production-код исправлен: вместо ``self.order_id`` используется параметр
    ``order_id``, поэтому теперь бросается корректное исключение.
    """
    svc.order_repo.get_by_id.return_value = None

    with pytest.raises(OrderNotFoundError):
        await svc.set_comment(order_id=uuid4(), comment=OrderComment(comment="коммент"))


@pytest.mark.asyncio
async def test_set_comment_rejects_non_draft_order(svc: OrderService) -> None:
    """set_comment: заказ не в DRAFT -> InvalidStateError, comment не меняется.

    Production-код теперь проверяет state == DRAFT в set_comment.
    """
    order = build_draft_order(state=OrderState.COMPLETED)
    svc.order_repo.get_by_id.return_value = order

    with pytest.raises(InvalidStateError):
        await svc.set_comment(order_id=order.id, comment=OrderComment(comment="прим"))

    assert order.comment is None
    svc.order_repo.commit.assert_not_awaited()


@pytest.mark.asyncio
async def test_set_comment_retries_after_stale_data(svc: OrderService) -> None:
    """set_comment: StaleDataError -> retry -> повтор успешен."""
    order = build_draft_order()
    svc.order_repo.get_by_id.return_value = order
    svc.order_repo.commit.side_effect = [StaleDataError(), None]

    result = await svc.set_comment(order_id=order.id, comment=OrderComment(comment="прим."))

    assert result is order
    assert order.comment == "прим."
    assert svc.order_repo.commit.await_count == 2
    svc.order_repo.rollback.assert_awaited_once()


@pytest.mark.asyncio
async def test_set_comment_retry_reloads_order(svc: OrderService) -> None:
    """set_comment: при retry Order перечитывается заново."""
    original = build_draft_order()
    reloaded = build_draft_order()
    svc.order_repo.get_by_id.side_effect = [original, original, reloaded]
    svc.order_repo.commit.side_effect = [StaleDataError(), StaleDataError(), None]

    result = await svc.set_comment(order_id=original.id, comment=OrderComment(comment="прим."))

    assert result is reloaded
    assert reloaded.comment == "прим."
    assert svc.order_repo.get_by_id.await_count == 3
# ---------------------------------------------------------------------------
# CONFIRM_ORDER
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_confirm_order_success_draft_to_confirmed(svc: OrderService) -> None:
    """confirm_order: DRAFT с обоими адресами и ценой переходит в CONFIRMED + commit."""
    order = build_priced_draft()
    svc.order_repo.get_by_id.return_value = order

    result = await svc.confirm_order(order_id=order.id)

    assert result is order
    assert order.state == OrderState.CONFIRMED
    svc.order_repo.commit.assert_awaited_once()


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "missing",
    [
        "pickup",
        "destination",
        "both",
    ],
)
async def test_confirm_order_requires_both_addresses(svc: OrderService, missing: str) -> None:
    """confirm_order: отсутствие pickup/destination/обоих -> InvalidTransitionError."""
    order = build_priced_draft()
    if missing in ("pickup", "both"):
        order.pickup_street_id = None
        order.pickup_landmark_id = None
    if missing in ("destination", "both"):
        order.destination_street_id = None
        order.destination_landmark_id = None
    svc.order_repo.get_by_id.return_value = order

    with pytest.raises(InvalidTransitionError):
        await svc.confirm_order(order_id=order.id)

    assert order.state == OrderState.DRAFT
    svc.order_repo.commit.assert_not_awaited()


@pytest.mark.asyncio
async def test_confirm_order_requires_price(svc: OrderService) -> None:
    """confirm_order: отсутствие цены -> InvalidTransitionError."""
    order = build_draft_with_both_addresses()
    order.price = None
    svc.order_repo.get_by_id.return_value = order

    with pytest.raises(InvalidTransitionError):
        await svc.confirm_order(order_id=order.id)


@pytest.mark.asyncio
@pytest.mark.parametrize("price", [0, -100])
async def test_confirm_order_rejects_non_positive_price(svc: OrderService, price: int) -> None:
    """confirm_order: цена <= 0 запрещает подтверждение."""
    order = build_draft_with_both_addresses()
    order.price = price
    svc.order_repo.get_by_id.return_value = order

    with pytest.raises(InvalidTransitionError):
        await svc.confirm_order(order_id=order.id)


@pytest.mark.asyncio
async def test_confirm_order_rejects_non_draft_state(svc: OrderService) -> None:
    """confirm_order: заказ уже не DRAFT (например CONFIRMED) -> InvalidTransitionError."""
    order = build_priced_draft()
    order.state = OrderState.CONFIRMED
    svc.order_repo.get_by_id.return_value = order

    with pytest.raises(InvalidTransitionError):
        await svc.confirm_order(order_id=order.id)


@pytest.mark.asyncio
async def test_confirm_order_invalid_state_raises(svc: OrderService) -> None:
    """confirm_order: некорректная state (SEARCHING) -> InvalidTransitionError."""
    order = build_priced_draft()
    order.state = OrderState.SEARCHING
    svc.order_repo.get_by_id.return_value = order

    with pytest.raises(InvalidTransitionError):
        await svc.confirm_order(order_id=order.id)


# --- Retry: confirm_order ---


@pytest.mark.asyncio
async def test_confirm_order_retries_after_stale_data(svc: OrderService) -> None:
    """confirm_order: StaleDataError -> rollback -> повтор успешен (Order перечитывается)."""
    svc.order_repo.get_by_id.side_effect = lambda *a, **k: build_priced_draft()
    svc.order_repo.commit.side_effect = [StaleDataError(), None]

    result = await svc.confirm_order(order_id=uuid4())

    assert result.state == OrderState.CONFIRMED
    assert svc.order_repo.commit.await_count == 2
    svc.order_repo.rollback.assert_awaited_once()


@pytest.mark.asyncio
async def test_confirm_order_retry_reloads_order(svc: OrderService) -> None:
    """confirm_order: после retry заказ перечитывается, transition на актуальном."""
    original = build_priced_draft()
    reloaded = build_priced_draft()
    svc.order_repo.get_by_id.side_effect = [original, reloaded]
    svc.order_repo.commit.side_effect = [StaleDataError(), None]

    result = await svc.confirm_order(order_id=original.id)

    assert result is reloaded
    assert reloaded.state == OrderState.CONFIRMED
    assert svc.order_repo.get_by_id.await_count == 2


@pytest.mark.asyncio
async def test_confirm_order_exhausts_retries(svc: OrderService) -> None:
    """confirm_order: три StaleDataError -> ошибка пробрасывается."""
    svc.order_repo.get_by_id.side_effect = lambda *a, **k: build_priced_draft()
    svc.order_repo.commit.side_effect = [StaleDataError(), StaleDataError(), StaleDataError()]

    with pytest.raises(StaleDataError):
        await svc.confirm_order(order_id=uuid4())

    assert svc.order_repo.rollback.await_count == 3
# ---------------------------------------------------------------------------
# CANCEL_ORDER
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "state",
    [
        OrderState.DRAFT,
        OrderState.CONFIRMED,
        OrderState.SEARCHING,
        OrderState.ASSIGNED,
        OrderState.IN_PROGRESS,
    ],
)
async def test_cancel_order_allowed_from_active_states(svc: OrderService, state: OrderState) -> None:
    """cancel_order: активное состояние -> CANCELLED, commit выполнен."""
    order = build_priced_draft()
    order.state = state
    svc.order_repo.get_by_id.return_value = order

    result = await svc.cancel_order(order_id=order.id)

    assert result is order
    assert order.state == OrderState.CANCELLED
    svc.order_repo.commit.assert_awaited_once()


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "state",
    [OrderState.COMPLETED, OrderState.CANCELLED],
)
async def test_cancel_order_forbidden_from_terminal_states(
    svc: OrderService, state: OrderState
) -> None:
    """cancel_order: терминальные COMPLETED/CANCELLED -> InvalidTransitionError."""
    order = build_priced_draft()
    order.state = state
    svc.order_repo.get_by_id.return_value = order

    with pytest.raises(InvalidTransitionError):
        await svc.cancel_order(order_id=order.id)

    assert order.state == state
    svc.order_repo.commit.assert_not_awaited()


@pytest.mark.asyncio
async def test_cancel_order_not_found_raises(svc: OrderService) -> None:
    """cancel_order: заказ не найден -> OrderNotFoundError."""
    svc.order_repo.get_by_id.return_value = None

    with pytest.raises(OrderNotFoundError):
        await svc.cancel_order(order_id=uuid4())


# --- Retry: cancel_order ---


@pytest.mark.asyncio
async def test_cancel_order_retries_after_stale_data(svc: OrderService) -> None:
    """cancel_order: StaleDataError -> rollback -> повтор успешен (Order перечитывается)."""
    svc.order_repo.get_by_id.side_effect = lambda *a, **k: build_priced_draft()
    svc.order_repo.commit.side_effect = [StaleDataError(), None]

    result = await svc.cancel_order(order_id=uuid4())

    assert result.state == OrderState.CANCELLED
    assert svc.order_repo.commit.await_count == 2
    svc.order_repo.rollback.assert_awaited_once()


@pytest.mark.asyncio
async def test_cancel_order_retry_reloads_order(svc: OrderService) -> None:
    """cancel_order: после retry заказ перечитывается, переход на актуальном."""
    original = build_priced_draft()
    reloaded = build_priced_draft()
    svc.order_repo.get_by_id.side_effect = [original, reloaded]
    svc.order_repo.commit.side_effect = [StaleDataError(), None]

    result = await svc.cancel_order(order_id=original.id)

    assert result is reloaded
    assert reloaded.state == OrderState.CANCELLED


@pytest.mark.asyncio
async def test_cancel_order_exhausts_retries(svc: OrderService) -> None:
    """cancel_order: три StaleDataError -> ошибка пробрасывается."""
    svc.order_repo.get_by_id.side_effect = lambda *a, **k: build_priced_draft()
    svc.order_repo.commit.side_effect = [StaleDataError(), StaleDataError(), StaleDataError()]

    with pytest.raises(StaleDataError):
        await svc.cancel_order(order_id=uuid4())

    assert svc.order_repo.rollback.await_count == 3
# ---------------------------------------------------------------------------
# STATE TRANSITIONS (через StateService — полная матрица)
# ---------------------------------------------------------------------------
# OrderService публично триггерит только CONFIRMED (confirm) и CANCELLED (cancel).
# Полная матрица (SEARCHING/ASSIGNED/IN_PROGRESS/COMPLETED) проверяется через
# реальный StateService — он является зависимостью OrderService.
# transition() синхронный, поэтому тесты не асинхронные.


ALLOWED_PAIRS = [
    (OrderState.DRAFT, OrderState.CONFIRMED),
    (OrderState.DRAFT, OrderState.CANCELLED),
    (OrderState.CONFIRMED, OrderState.SEARCHING),
    (OrderState.CONFIRMED, OrderState.CANCELLED),
    (OrderState.SEARCHING, OrderState.ASSIGNED),
    (OrderState.SEARCHING, OrderState.CANCELLED),
    (OrderState.ASSIGNED, OrderState.IN_PROGRESS),
    (OrderState.ASSIGNED, OrderState.CANCELLED),
    (OrderState.IN_PROGRESS, OrderState.COMPLETED),
    (OrderState.IN_PROGRESS, OrderState.CANCELLED),
]


@pytest.mark.parametrize(("from_state", "to_state"), ALLOWED_PAIRS)
def test_state_transition_allowed(from_state: OrderState, to_state: OrderState) -> None:
    """StateService.transition: разрешённые переходы применяются."""
    service = StateService()
    order = build_priced_draft()
    order.state = from_state
    service.transition(order, to_state)
    assert order.state == to_state


FORBIDDEN_PAIRS = [
    (OrderState.DRAFT, OrderState.SEARCHING),
    (OrderState.DRAFT, OrderState.ASSIGNED),
    (OrderState.DRAFT, OrderState.ASSIGNED),
    (OrderState.DRAFT, OrderState.IN_PROGRESS),
    (OrderState.DRAFT, OrderState.COMPLETED),
    (OrderState.CONFIRMED, OrderState.ASSIGNED),
    (OrderState.CONFIRMED, OrderState.IN_PROGRESS),
    (OrderState.CONFIRMED, OrderState.COMPLETED),
    (OrderState.CONFIRMED, OrderState.CONFIRMED),
    (OrderState.SEARCHING, OrderState.SEARCHING),
    (OrderState.SEARCHING, OrderState.CONFIRMED),
    (OrderState.SEARCHING, OrderState.IN_PROGRESS),
    (OrderState.ASSIGNED, OrderState.SEARCHING),
    (OrderState.IN_PROGRESS, OrderState.ASSIGNED),
    # Терминальные не дают переходов никуда.
    (OrderState.COMPLETED, OrderState.DRAFT),
    (OrderState.COMPLETED, OrderState.CANCELLED),
    (OrderState.COMPLETED, OrderState.IN_PROGRESS),
    (OrderState.CANCELLED, OrderState.DRAFT),
    (OrderState.CANCELLED, OrderState.CONFIRMED),
    (OrderState.CANCELLED, OrderState.CANCELLED),
]


@pytest.mark.parametrize(("from_state", "to_state"), FORBIDDEN_PAIRS)
def test_state_transition_forbidden(from_state: OrderState, to_state: OrderState) -> None:
    """StateService.transition: запрещённые переходы -> InvalidTransitionError."""
    service = StateService()
    order = build_draft_order()
    order.state = from_state
    with pytest.raises(InvalidTransitionError):
        service.transition(order, to_state)
    assert order.state == from_state  # состояние не изменилось


# ---------------------------------------------------------------------------
# ВСПОМОГАТЕЛЬНАЯ ЛОГИКА OrderService
# ---------------------------------------------------------------------------


def test_is_same_address_compares_ids(svc: OrderService) -> None:
    """_is_same_address: True при совпадении всех *_id, False при отличии."""
    order = build_draft_order(
        pickup_town_id=1,
        pickup_district_id=2,
        pickup_street_id=3,
        pickup_house_id=4,
        pickup_landmark_id=5,
    )
    same = build_candidate(town_id=1, district_id=2, street_id=3, house_id=4, landmark_id=5)
    assert svc._is_same_address(target=order, candidate=same, prefix="pickup") is True

    different = build_candidate(town_id=1, district_id=2, street_id=99, house_id=4, landmark_id=5)
    assert svc._is_same_address(target=order, candidate=different, prefix="pickup") is False


def test_apply_address_candidate_sets_fields(svc: OrderService) -> None:
    """_apply_address_candidate: заполняет target по префиксу из candidate."""
    order = build_draft_order()
    candidate = build_candidate(
        town_id=1, town_name="аскарово",
        district_id=2, district_name="центр",
        street_id=3, street_name="ленина",
        house_id=4, house_number="5",
        landmark_id=6, landmark_name="парк",
    )
    svc._apply_address_candidate(target=order, candidate=candidate, prefix="destination")

    assert order.destination_town == "аскарово"
    assert order.destination_town_id == 1
    assert order.destination_district == "центр"
    assert order.destination_district_id == 2
    assert order.destination_street == "ленина"
    assert order.destination_street_id == 3
    assert order.destination_house == "5"
    assert order.destination_house_id == 4
    assert order.destination_landmark == "парк"
    assert order.destination_landmark_id == 6


@pytest.mark.asyncio
async def test_price_reset_before_recalculation_on_error(svc: OrderService) -> None:
    """set_pickup: price сбрасывается ДО пересчёта; ошибка pricing оставляет price=None."""
    order = build_priced_draft(pickup_street_id=3)
    order.price = 500
    svc.order_repo.get_by_id.return_value = order
    svc.address_service.resolve_address.return_value = resolved_address(street_id=77)
    svc.pricing_service.calculate.side_effect = PricingError(reason="boom")

    with pytest.raises(PricingError):
        await svc.set_pickup(order_id=order.id, address_data=AddressInput(street="новая", house="1"))

    assert order.price is None  # сброшен до вызова calculate
    svc.pricing_service.calculate.assert_awaited_once()
# ---------------------------------------------------------------------------
# Дополнительные негативные ветки retry / not-found
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_confirm_order_not_found_raises(svc: OrderService) -> None:
    """confirm_order: заказ не найден -> OrderNotFoundError."""
    svc.order_repo.get_by_id.return_value = None

    with pytest.raises(OrderNotFoundError):
        await svc.confirm_order(order_id=uuid4())


@pytest.mark.asyncio
async def test_set_passenger_name_exhausts_retries(svc: OrderService) -> None:
    """set_passenger_name: три StaleDataError -> ошибка пробрасывается."""
    order = build_draft_order()
    svc.order_repo.get_by_id.return_value = order
    svc.order_repo.commit.side_effect = [StaleDataError(), StaleDataError(), StaleDataError()]

    with pytest.raises(StaleDataError):
        await svc.set_passenger_name(order_id=order.id, name=PassengerName(first_name="Иван"))

    assert svc.order_repo.rollback.await_count == 3


@pytest.mark.asyncio
async def test_set_comment_exhausts_retries(svc: OrderService) -> None:
    """set_comment: три StaleDataError -> ошибка пробрасывается."""
    order = build_draft_order()
    svc.order_repo.get_by_id.return_value = order
    svc.order_repo.commit.side_effect = [StaleDataError(), StaleDataError(), StaleDataError()]

    with pytest.raises(StaleDataError):
        await svc.set_comment(order_id=order.id, comment=OrderComment(comment="прим."))

    assert svc.order_repo.rollback.await_count == 3