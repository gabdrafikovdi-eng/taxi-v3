# app/tools/waypoint_tools.py
import logging
from collections.abc import Mapping

from app.services.order_service import OrderService
from app.tools.base import Tool, ToolContext, ToolDefinition, ToolResult
from app.tools.inputs import AddWaypointInput, RemoveWaypointInput, UpdateWaypointInput
from app.tools.serializers import serialize_order

logger = logging.getLogger(__name__)


class AddWaypointTool(Tool):
    name = "add_waypoint"

    def __init__(self, order_service: OrderService) -> None:
        self._service = order_service
        self.definition = ToolDefinition(
            name=self.name,
            description="Добавить промежуточную остановку к заказу по его номеру.",
            parameters=AddWaypointInput.model_json_schema(),
        )

    async def execute(
        self,
        ctx: ToolContext,
        arguments: Mapping[str, object],
    ) -> ToolResult:
        payload = AddWaypointInput.model_validate(arguments)

        order = await self._service.get_order_by_number(
            call_session_id=ctx.call_session_id,
            order_number=payload.order_number,
        )

        updated_order = await self._service.add_waypoint(
            order_id=order.id,
            address_data=payload.address,
        )

        return ToolResult(
            success=True,
            message="Остановка добавлена.",
            code="WAYPOINT_ADDED",
            data={"order": serialize_order(updated_order)},
        )


class UpdateWaypointTool(Tool):
    name = "update_waypoint"

    def __init__(self, order_service: OrderService) -> None:
        self._service = order_service
        self.definition = ToolDefinition(
            name=self.name,
            description="Изменить адрес промежуточной остановки по её порядковому номеру.",
            parameters=UpdateWaypointInput.model_json_schema(),
        )

    async def execute(
        self,
        ctx: ToolContext,
        arguments: Mapping[str, object],
    ) -> ToolResult:
        payload = UpdateWaypointInput.model_validate(arguments)

        order = await self._service.get_order_by_number(
            call_session_id=ctx.call_session_id,
            order_number=payload.order_number,
        )

        updated_order = await self._service.update_waypoint(
            order_id=order.id,
            sequence_number=payload.sequence_number,
            address_data=payload.address,
        )

        return ToolResult(
            success=True,
            message="Остановка обновлена.",
            code="WAYPOINT_UPDATED",
            data={"order": serialize_order(updated_order)},
        )


class RemoveWaypointTool(Tool):
    name = "remove_waypoint"

    def __init__(self, order_service: OrderService) -> None:
        self._service = order_service
        self.definition = ToolDefinition(
            name=self.name,
            description="Удалить промежуточную остановку по её порядковому номеру.",
            parameters=RemoveWaypointInput.model_json_schema(),
        )

    async def execute(
        self,
        ctx: ToolContext,
        arguments: Mapping[str, object],
    ) -> ToolResult:
        payload = RemoveWaypointInput.model_validate(arguments)

        order = await self._service.get_order_by_number(
            call_session_id=ctx.call_session_id,
            order_number=payload.order_number,
        )

        updated_order = await self._service.remove_waypoint(
            order_id=order.id,
            sequence_number=payload.sequence_number,
        )

        return ToolResult(
            success=True,
            message="Остановка удалена.",
            code="WAYPOINT_REMOVED",
            data={"order": serialize_order(updated_order)},
        )
