"""Интеграция с backend (существующий сервис, НЕ изменяется).

Контракт — Protocol ``BackendClient``; реализация выбирается настройкой
``BACKEND_MODE`` (mock | http). Подробности и BLOCKER — в README.
"""

from __future__ import annotations

from app.backend.base import BackendClient, BackendError
from app.backend.http_client import HTTPBackendClient
from app.backend.mock import MockBackendClient
from app.config import Settings

__all__ = [
    "BackendClient",
    "BackendError",
    "HTTPBackendClient",
    "MockBackendClient",
    "build_backend",
]


def build_backend(settings: Settings) -> BackendClient:
    mode = settings.BACKEND_MODE.lower()
    if mode == "mock":
        return MockBackendClient()
    if mode == "http":
        return HTTPBackendClient(
            base_url=settings.BACKEND_URL, timeout=settings.BACKEND_TIMEOUT_SEC
        )
    raise ValueError(f"Unsupported BACKEND_MODE: {settings.BACKEND_MODE!r} (mock|http)")
