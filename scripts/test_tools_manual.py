# scripts/test_tools_manual.py
import asyncio
from uuid import uuid4

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import async_session_factory
from app.models.call_session import CallSession, CallChannel, HandledBy
from app.repositories.call_session_repo import CallSessionRepository
from app.tools.base import ToolContext
from app.tools.composition import build_tools


async def create_call_session(session: AsyncSession) -> uuid4:
    """Создаёт call_session и возвращает его ID."""
    # Подставь реальный способ создания call_session
    # Например, через CallSessionRepository
    call_session = CallSession(
        channel=CallChannel.CONSOLE,
        handled_by=HandledBy.BOT,
        external_call_id=str(uuid4()),
        caller_phone="79000000000",
    )
    call_repo = CallSessionRepository(session)

    await call_repo.add(call_session=call_session)
    await call_repo.session.commit()
    await call_repo.session.flush()
    return call_session.id


async def print_result(result) -> None:
    """Печатает результат инструмента."""
    print(f"success: {result.success}")
    print(f"message: {result.message}")
    print(f"code:    {result.code}")
    if result.data:
        print(f"data:    {result.data}")
    print("-" * 40)


async def main() -> None:
    async with async_session_factory() as session:
        # 1. Создаём или получаем call_session
        call_session_id = await create_call_session(session)
        print(f"call_session_id: {call_session_id}\n")

        # 2. Собираем инструменты
        registry, availability = build_tools(session)

        # 3. Контекст для вызовов
        ctx = ToolContext(
            call_session_id=call_session_id,
            tool_call_id=None,
        )

        # 4. Проверяем доступность
        available = await availability.available_names(call_session_id)
        print(f"Доступные инструменты: {available}\n")

        # 5. Создаём заказ
        result = await registry.execute("create_order", ctx, {})
        await print_result(result)

        # 6. Смотрим список заказов
        result = await registry.execute("list_orders", ctx, {})
        await print_result(result)

        # 7. Устанавливаем адрес подачи
        result = await registry.execute(
            "set_pickup",
            ctx,
            {
                "order_number": 1,
                "address": {"street": "Ленина", "house": "10"},
            },
        )
        await print_result(result)

        # 8. Устанавливаем адрес назначения
        result = await registry.execute(
            "set_destination",
            ctx,
            {
                "order_number": 1,
                "address": {"street": "Гагарина", "house": "5"},
            },
        )
        await print_result(result)

        # 9. Подтверждаем заказ
        result = await registry.execute(
            "confirm_order",
            ctx,
            {"order_number": 1},
        )
        await print_result(result)


if __name__ == "__main__":
    asyncio.run(main())
