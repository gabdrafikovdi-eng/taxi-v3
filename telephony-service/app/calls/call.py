"""Сущность телефонного звонка (telephony session).

Связывает: Asterisk channel + caller phone + call_id + backend call_session_id
+ медиа-pipeline. Модели backend НЕ изменяются — связка делается через
интеграционный слой (BackendClient).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import TYPE_CHECKING

from app.calls.state import CallStateMachine

if TYPE_CHECKING:  # pragma: no cover
    from app.calls.pipeline import CallPipeline


@dataclass
class Call:
    call_id: str  # correlation ID внутри telephony-service
    channel_id: str  # Asterisk channel id (входящий PJSIP-канал)
    caller_phone: str | None
    external_id: str  # уникальный external_call_id для backend
    backend_call_session_id: str | None = None
    state: CallStateMachine = field(default_factory=CallStateMachine)

    # Asterisk-ресурсы
    external_media_channel_id: str | None = None
    bridge_id: str | None = None
    rtp_port: int | None = None

    pipeline: CallPipeline | None = None
    watchdog_task: object | None = None

    created_at: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc)
    )

    def log_fields(self) -> dict[str, object]:
        return {
            "call_id": self.call_id,
            "channel_id": self.channel_id,
            "backend_call_session_id": self.backend_call_session_id,
            "state": self.state.current.value,
        }
