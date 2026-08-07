from contextlib import asynccontextmanager
from datetime import datetime

from sqlalchemy import DateTime, func
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase, Mapped, declarative_mixin, mapped_column
from app.core.config import config_settings


engine = create_async_engine(config_settings.DATABASE_URL)

async_session_factory = async_sessionmaker(
    bind=engine, autoflush=False, expire_on_commit=False
)


class Base(DeclarativeBase):
    pass


@declarative_mixin
class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),  # SQLAlchemy сам обновит это поле при любом UPDATE-запросе
    )


@asynccontextmanager
async def get_session():
    """
    Контекстный менеджер для работы с асинхронной сессией SQLAlchemy.

    Автоматически:
    - Создаёт сессию при входе в async with
    - Делает commit при успешном завершении
    - Делает rollback при возникновении исключения
    - Закрывает сессию при выходе из async with
    """
    async with async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


async def get_async_session():
    async with async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise

import app.models.address
import app.models.call_session
import app.models.messages
import app.models.order