"""Структурированное JSON-логирование (stdlib, без внешних зависимостей).

Каждая строка — JSON-объект: ts, level, logger, event, call_id, + произвольные
поля из ``extra={"fields": {...}}``. Correlation ID звонка (call_id) берётся из
``call_id_var`` (contextvar) — задаётся в pipeline звонка.
Секреты в логи не передаются (в fields их не включать).
"""

from __future__ import annotations

import json
import logging
import sys
import time
from contextvars import ContextVar

call_id_var: ContextVar[str] = ContextVar("call_id", default="-")

_FIELDS_ATTR = "fields"


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, object] = {
            "ts": time.strftime(
                "%Y-%m-%dT%H:%M:%S", time.gmtime(record.created)
            )
            + f".{int(record.msecs):03d}Z",
            "level": record.levelname,
            "logger": record.name,
            "event": record.getMessage(),
            "call_id": call_id_var.get(),
        }
        fields = getattr(record, _FIELDS_ATTR, None)
        if isinstance(fields, dict):
            payload.update(fields)
        if record.exc_info:
            payload["exc"] = self.formatException(record.exc_info)
        return json.dumps(payload, ensure_ascii=False, default=str)


def setup_logging(level: str = "INFO") -> None:
    root = logging.getLogger()
    root.handlers.clear()
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JsonFormatter())
    root.addHandler(handler)
    root.setLevel(level.upper())
    # Шумные библиотеки — только предупреждения и выше
    for name in ("aiohttp", "asyncio", "urllib3"):
        logging.getLogger(name).setLevel(logging.WARNING)


def jinfo(event: str, **fields: object) -> None:
    logging.getLogger("telephony").info(event, extra={"fields": fields})


def jwarning(event: str, **fields: object) -> None:
    logging.getLogger("telephony").warning(event, extra={"fields": fields})


def jerror(event: str, **fields: object) -> None:
    logging.getLogger("telephony").error(event, extra={"fields": fields})


def jexception(event: str, **fields: object) -> None:
    logging.getLogger("telephony").exception(event, extra={"fields": fields})
