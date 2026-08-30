"""Настройка structlog для speech-service.

Логирование в JSON-формате (для ELK/Loki/строкового вывода в Docker).
Уровень фильтрации берётся из ``settings.LOG_LEVEL``.
"""

from __future__ import annotations

import logging

import structlog

from app.config import settings


def setup_logging() -> None:
    """Настроить structlog на весь процесс. Вызывается один раз при старте."""
    structlog.configure(
        processors=[
            # Сквозной контекст (contextvars), например request_id.
            structlog.contextvars.merge_contextvars,
            # Поле "level": "info" / "warning" / ...
            structlog.processors.add_log_level,
            structlog.processors.StackInfoRenderer(),
            structlog.dev.set_exc_info,
            # Поле "timestamp" в ISO-8601.
            structlog.processors.TimeStamper(fmt="iso"),
            # Машиночитаемый JSON для прод-окружения.
            structlog.processors.JSONRenderer(),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(
            logging.getLevelName(settings.LOG_LEVEL)
        ),
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=False,
    )


def get_logger(name: str) -> structlog.stdlib.BoundLogger:
    """Вернуть bound-логгер structlog для модуля ``name``."""
    return structlog.get_logger(name)