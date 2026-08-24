# app/tools/composition.py
from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.address_repo import AddressRepository
from app.repositories.order_repo import OrderRepository
from app.services.address.address_service import AddressService
from app.services.address.context_resolver import ContextResolver
from app.services.address.house_resolver import HouseResolver
from app.services.address.landmark_resolver import LandmarkResolver
from app.services.address.street_resolver import StreetResolver
from app.services.address.suggestion_service import AddressSuggestionService
from app.services.order_service import OrderService
from app.services.pricing_service import PricingService
from app.services.state_service import StateService
from app.tools.address_tools import SetDestinationTool, SetPickupTool
from app.tools.availability import OrderToolAvailability
from app.tools.draft_tools import SetCommentTool, SetPassengerNameTool
from app.tools.order_tools import (
    CancelOrderTool,
    ConfirmOrderTool,
    CreateOrderTool,
    GetOrderTool,
    ListOrdersTool,
)
from app.tools.registry import ToolRegistry
from app.tools.waypoint_tools import (
    AddWaypointTool,
    RemoveWaypointTool,
    UpdateWaypointTool,
)

from app.core.config import address_config


def build_order_service(session: AsyncSession) -> OrderService:
    """Собирает OrderService со всеми зависимостями."""
    order_repo = OrderRepository(session)
    address_repo = AddressRepository(session)
    context_resolver = ContextResolver(
        address_repo=address_repo, default_town_name=address_config.default_town_name
    )
    street_resolver = StreetResolver(
        address_repo=address_repo,
        fuzzy_threshold=address_config.fuzzy_threshold,
        max_candidate=address_config.max_exact_variants,
    )
    house_resolver = HouseResolver(address_repo=address_repo)
    landmark_resolver = LandmarkResolver(address_repo=address_repo)
    address_suggestion_service = AddressSuggestionService(address_repo=address_repo)
    state_service = StateService()

    # Подставь реальные зависимости для AddressService и PricingService
    address_service = AddressService(
        address_repo=address_repo,
        context_resolver=context_resolver,
        street_resolver=street_resolver,
        house_resolver=house_resolver,
        landmark_resolver=landmark_resolver,
        address_suggestion_service=address_suggestion_service,
    )
    pricing_service = PricingService(address_repo=address_repo)

    return OrderService(
        state_service=state_service,
        address_service=address_service,
        pricing_service=pricing_service,
        order_repo=order_repo,
    )


def build_tool_registry(order_service: OrderService) -> ToolRegistry:
    """Собирает реестр со всеми инструментами."""
    tools = [
        # Жизненный цикл
        CreateOrderTool(order_service),
        ListOrdersTool(order_service),
        GetOrderTool(order_service),
        ConfirmOrderTool(order_service),
        CancelOrderTool(order_service),
        # Адреса
        SetPickupTool(order_service),
        SetDestinationTool(order_service),
        # Черновик
        SetPassengerNameTool(order_service),
        SetCommentTool(order_service),
        # Остановки
        AddWaypointTool(order_service),
        UpdateWaypointTool(order_service),
        RemoveWaypointTool(order_service),
    ]
    return ToolRegistry(tools)


def build_tool_availability(session: AsyncSession) -> OrderToolAvailability:
    """Собирает сервис доступности инструментов."""
    order_repo = OrderRepository(session)
    return OrderToolAvailability(order_repo)


def build_tools(session: AsyncSession) -> tuple[ToolRegistry, OrderToolAvailability]:
    """Точка входа: собирает всё и возвращает реестр + доступность."""
    order_service = build_order_service(session)
    registry = build_tool_registry(order_service)
    availability = build_tool_availability(session)
    return registry, availability
