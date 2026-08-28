from enum import StrEnum
from uuid import UUID, uuid4

from sqlalchemy import (
    Enum,
    ForeignKey,
    String,
    Text,
    UniqueConstraint,
    Uuid,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base, TimestampMixin


class MessageRole(StrEnum):
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"
    TOOL = "tool"


class Message(Base, TimestampMixin):
    __tablename__ = "messages"

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    call_session_id: Mapped[UUID] = mapped_column(
        ForeignKey("call_sessions.id", ondelete="CASCADE"), nullable=False, index=True
    )
    sequence_number: Mapped[int] = mapped_column(nullable=False)
    role: Mapped[MessageRole] = mapped_column(
        Enum(
            MessageRole,
            native_enum=False,
            name="message_role",
            values_callable=lambda enum: [x.value for x in enum],
        ),
        nullable=False,
    )
    content: Mapped[str | None] = mapped_column(Text, nullable=True)
    tool_call_id: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )
    name: Mapped[str | None] = mapped_column(String(50), nullable=True)
    tools_calls: Mapped[list["ToolCallRecord"]] = relationship(
        back_populates="message",
        cascade="all, delete-orphan",
    )

    __table_args__ = (
        UniqueConstraint(
            "call_session_id", "sequence_number", name="uq_messages_session_sequence"
        ),
    )


class ToolCallRecord(Base, TimestampMixin):
    __tablename__ = "tool_call_records"

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    message_id: Mapped[UUID] = mapped_column(
        ForeignKey("messages.id", ondelete="CASCADE"), nullable=False, index=True
    )
    tool_call_id: Mapped[str] = mapped_column(String(100), nullable=False)
    function_name: Mapped[str] = mapped_column(String(100), nullable=False)
    arguments: Mapped[str] = mapped_column(Text, nullable=False)
    message: Mapped["Message"] = relationship(
        back_populates="tools_calls",
    )
    thought_signature: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    reasoning_content: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    response_id: Mapped[str | None] = mapped_column(
        String(200),
        nullable=True,
    )
