"""Mock-реализация backend для разработки и ручного теста pipeline.

Позволяет проверить полный круг GSM → Asterisk → STT → TTS → GSM без
доступного backend API. Ответы детерминированные, хранятся в памяти.
"""

from __future__ import annotations

from uuid import uuid4

from app.logging import jinfo


class MockBackendClient:
    def __init__(self, fail_rate: float = 0.0) -> None:
        self._calls: dict[str, list[str]] = {}
        self._by_external: dict[str, str] = {}
        self._ended: set[str] = set()

    async def start_call(self, external_id: str, caller_phone: str | None) -> str:
        # Идемпотентность как у backend: тот же external_id → та же сессия
        existing = self._by_external.get(external_id)
        if existing is not None:
            return existing
        call_id = str(uuid4())
        self._calls[call_id] = []
        self._by_external[external_id] = call_id
        jinfo("mock_backend_call_started", call_session_id=call_id, phone=caller_phone)
        return call_id

    async def greeting(self, call_session_id: str) -> str | None:
        return "Здравствуйте! Служба такси. Чем могу помочь?"

    async def handle_message(self, call_session_id: str, text: str) -> str:
        if call_session_id not in self._calls:
            raise KeyError(call_session_id)
        self._calls[call_session_id].append(text)
        lowered = text.lower()
        if "оператор" in lowered or "оператора" in lowered:
            return "Соединяю вас с оператором, оставайтесь на линии."
        if not text.strip():
            return "Извините, я вас не расслышал."
        return f"Принято: {text}. Что-нибудь ещё?"

    async def end_call(self, call_session_id: str) -> None:
        self._ended.add(call_session_id)
        jinfo("mock_backend_call_ended", call_session_id=call_session_id)

    @property
    def calls(self) -> dict[str, list[str]]:
        return self._calls
