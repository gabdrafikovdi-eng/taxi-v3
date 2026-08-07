from datetime import datetime
from enum import StrEnum
from uuid import UUID, uuid4

from sqlalchemy import DateTime, Enum, String, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base, TimestampMixin


class CallChannel(StrEnum):
    CONSOLE = "console"
    TELEGRAM = "telegram"
    PHONE = "phone"


class HandledBy(StrEnum):
    BOT = "bot"
    OPERATOR = "operator"


class CallSession(Base, TimestampMixin):
    """Сессия звонка — хранит все данные о текущем диалоге."""

    __tablename__ = "call_sessions"

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    channel: Mapped[CallChannel] = mapped_column(
        Enum(
            CallChannel,
            name="call_channel",
            native_enum=False,
            values_callable=lambda enum: [x.value for x in enum],
        ),
        nullable=False,
    )
    handled_by: Mapped[HandledBy] = mapped_column(
        Enum(
            HandledBy,
            name="handled_by",
            native_enum=False,
            values_callable=lambda enum: [x.value for x in enum],
        ),
        default=HandledBy.BOT,
        nullable=False,
    )
    external_call_id: Mapped[str | None] = mapped_column(
        String(64),
        unique=True,
        nullable=True,
    )
    caller_phone: Mapped[str | None] = mapped_column(String(100), nullable=True)
    caller_name: Mapped[str | None] = mapped_column(String(50), nullable=True)

    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    # Если NULL — звонок активен.
    ended_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    unknown_attempts: Mapped[int] = mapped_column(default=0, nullable=False)

    @property
    def is_active(self) -> bool:
        return self.ended_at is None

    @property
    def is_handled_by_operator(self) -> bool:
        return self.handled_by == HandledBy.OPERATOR
