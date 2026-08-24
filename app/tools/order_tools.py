# app/tools/order_tools.py
import logging
from collections.abc import Mapping
from uuid import uuid4

from app.services.order_service import OrderService
from app.tools.base import Tool, ToolContext, ToolDefinition, ToolResult
from app.tools.inputs import CreateOrderInput, OrderNumberInput
from app.tools.serializers import serialize_order

logger = logging.getLogger(__name__)


class CreateOrderTool(Tool):
    name = "create_order"

    def __init__(self, order_service: OrderService) -> None:
        self._service = order_service
        self.definition = ToolDefinition(
            name=self.name,
            description="Создать новый черновой заказ. Вызывать, когда пользователь хочет заказать такси.",
            parameters=CreateOrderInput.model_json_schema(),
        )

    async def execute(
        self,
        ctx: ToolContext,
        arguments: Mapping[str, object],
    ) -> ToolResult:

        idempotency_key = ctx.tool_call_id or str(uuid4())

        order = await self._service.create_order(
            call_session_id=ctx.call_session_id,
            idempotency_key=idempotency_key,
        )

        return ToolResult(
            success=True,
            message="Заказ создан.",
            code="ORDER_CREATED",
            data={"order": serialize_order(order)},
        )


class ListOrdersTool(Tool):
    name = "list_orders"

    def __init__(self, order_service: OrderService) -> None:
        self._service = order_service
        self.definition = ToolDefinition(
            name=self.name,
            description="Получить список активных заказов в текущем звонке.",
            parameters={},
        )

    async def execute(
        self,
        ctx: ToolContext,
        arguments: Mapping[str, object],
    ) -> ToolResult:
        orders = await self._service.list_active_orders(ctx.call_session_id)

        return ToolResult(
            success=True,
            message=f"Найдено заказов: {len(orders)}",
            code="ORDERS_LIST",
            data={"orders": [serialize_order(o) for o in orders]},
        )


class GetOrderTool(Tool):
    name = "get_order"

    def __init__(self, order_service: OrderService) -> None:
        self._service = order_service
        self.definition = ToolDefinition(
            name=self.name,
            description="Получить информацию о заказе по его номеру.",
            parameters=OrderNumberInput.model_json_schema(),
        )

    async def execute(
        self,
        ctx: ToolContext,
        arguments: Mapping[str, object],
    ) -> ToolResult:
        payload = OrderNumberInput.model_validate(arguments)

        order = await self._service.get_order_by_number(
            call_session_id=ctx.call_session_id,
            order_number=payload.order_number,
        )

        return ToolResult(
            success=True,
            message="Информация о заказе.",
            code="ORDER_STATE",
            data={"order": serialize_order(order)},
        )


class ConfirmOrderTool(Tool):
    name = "confirm_order"

    def __init__(self, order_service: OrderService) -> None:
        self._service = order_service
        self.definition = ToolDefinition(
            name=self.name,
            description="Подтвердить заказ по его номеру. Заказ должен иметь оба адреса и рассчитанную цену.",
            parameters=OrderNumberInput.model_json_schema(),
        )

    async def execute(
        self,
        ctx: ToolContext,
        arguments: Mapping[str, object],
    ) -> ToolResult:
        payload = OrderNumberInput.model_validate(arguments)

        order = await self._service.get_order_by_number(
            call_session_id=ctx.call_session_id,
            order_number=payload.order_number,
        )

        confirmed_order = await self._service.confirm_order(order.id)

        return ToolResult(
            success=True,
            message="Заказ подтверждён.",
            code="ORDER_CONFIRMED",
            data={"order": serialize_order(confirmed_order)},
        )


class CancelOrderTool(Tool):
    name = "cancel_order"

    def __init__(self, order_service: OrderService) -> None:
        self._service = order_service
        self.definition = ToolDefinition(
            name=self.name,
            description="Отменить заказ по его номеру.",
            parameters=OrderNumberInput.model_json_schema(),
        )

    async def execute(
        self,
        ctx: ToolContext,
        arguments: Mapping[str, object],
    ) -> ToolResult:
        payload = OrderNumberInput.model_validate(arguments)

        order = await self._service.get_order_by_number(
            call_session_id=ctx.call_session_id,
            order_number=payload.order_number,
        )

        cancelled_order = await self._service.cancel_order(order.id)

        return ToolResult(
            success=True,
            message="Заказ отменён.",
            code="ORDER_CANCELLED",
            data={"order": serialize_order(cancelled_order)},
        )
