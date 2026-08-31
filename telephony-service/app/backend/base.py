"""Интерфейс интеграции с backend (conversation / call sessions)."""

from __future__ import annotations

from typing import Protocol


class BackendError(RuntimeError):
    """Ошибка обращения к backend (недоступен/ошибка контракта)."""


class BackendClient(Protocol):
    """Контекст разговора на стороне backend.

    ``call_session_id`` — идентификатор сессии разговора в backend
    (backend-модель ``CallSession.id``).
    """

    async def start_call(self, external_id: str, caller_phone: str | None) -> str:
        """Создать (или найти по external_id) call session. Вернуть её id."""
        ...

    async def greeting(self, call_session_id: str) -> str | None:
        """Приветствие при ответе. None — приветствия нет."""
        ...

    async def handle_message(self, call_session_id: str, text: str) -> str:
        """Передать распознанный текст пользователя, вернуть ответ (LLM)."""
        ...

    async def end_call(self, call_session_id: str) -> None:
        """Завершить call session в backend."""
        ...
