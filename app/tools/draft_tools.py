# app/tools/draft_tools.py
import logging
from collections.abc import Mapping

from app.schemas.address import OrderComment, PassengerName
from app.services.order_service import OrderService
from app.tools.base import Tool, ToolContext, ToolDefinition, ToolResult
from app.tools.inputs import SetCommentInput, SetPassengerNameInput
from app.tools.serializers import serialize_order

logger = logging.getLogger(__name__)


class SetPassengerNameTool(Tool):
    name = "set_passenger_name"

    def __init__(self, order_service: OrderService) -> None:
        self._service = order_service
        self.definition = ToolDefinition(
            name=self.name,
            description="Сохранить имя пассажира для заказа по его номеру.",
            parameters=SetPassengerNameInput.model_json_schema(),
        )

    async def execute(
        self,
        ctx: ToolContext,
        arguments: Mapping[str, object],
    ) -> ToolResult:
        payload = SetPassengerNameInput.model_validate(arguments)

        order = await self._service.get_order_by_number(
            call_session_id=ctx.call_session_id,
            order_number=payload.order_number,
        )

        # Создаём доменную модель, чтобы прошла нормализация (title case, trim)
        name = PassengerName(first_name=payload.name)

        updated_order = await self._service.set_passenger_name(
            order_id=order.id,
            name=name,
        )

        return ToolResult(
            success=True,
            message="Имя пассажира сохранено.",
            code="PASSENGER_NAME_SET",
            data={"order": serialize_order(updated_order)},
        )


class SetCommentTool(Tool):
    name = "set_comment"

    def __init__(self, order_service: OrderService) -> None:
        self._service = order_service
        self.definition = ToolDefinition(
            name=self.name,
            description="Сохранить комментарий к заказу по его номеру.",
            parameters=SetCommentInput.model_json_schema(),
        )

    async def execute(
        self,
        ctx: ToolContext,
        arguments: Mapping[str, object],
    ) -> ToolResult:
        payload = SetCommentInput.model_validate(arguments)

        order = await self._service.get_order_by_number(
            call_session_id=ctx.call_session_id,
            order_number=payload.order_number,
        )

        # Создаём доменную модель, чтобы прошла нормализация (trim)
        comment = OrderComment(comment=payload.comment)

        updated_order = await self._service.set_comment(
            order_id=order.id,
            comment=comment,
        )

        return ToolResult(
            success=True,
            message="Комментарий сохранён.",
            code="COMMENT_SET",
            data={"order": serialize_order(updated_order)},
        )
