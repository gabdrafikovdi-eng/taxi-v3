# app/core/logging.py
import logging
import structlog
from app.core.config import config_settings


def setup_logging() -> None:
    """
    Настройка structlog для всего приложения.
    Вызывается один раз при старте.
    """
    structlog.configure(
        # === PROCESSORS ===
        # Это цепочка обработчиков, через которые проходит каждое log-сообщение.
        # Каждый processor делает что-то одно и передаёт результат следующему.
        processors=[
            # 1. merge_contextvars
            # Сливает контекстные переменные (ContextVar) в event_dict.
            # Это позволяет использовать contextvars для сквозного контекста
            # (например, request_id в FastAPI middleware).
            structlog.contextvars.merge_contextvars,
            # 2. add_log_level
            # Добавляет поле "level" в event_dict.
            # Было: {"event": "order_created"}
            # Стало: {"event": "order_created", "level": "info"}
            structlog.processors.add_log_level,
            # 3. StackInfoRenderer
            # Если в логе есть stack_info=True, рендерит стек вызовов.
            # Полезно для отладки: видно, откуда вызван лог.
            structlog.processors.StackInfoRenderer(),
            # 4. set_exc_info
            # Если было исключение (logger.exception()), добавляет traceback.
            # dev.set_exc_info — для читаемого вывода в консоли.
            structlog.dev.set_exc_info,
            # 5. TimeStamper
            # Добавляет временную метку в формате ISO 8601.
            # Было: {"event": "order_created", "level": "info"}
            # Стало: {"event": "order_created", "level": "info", "timestamp": "2024-01-15T10:30:01.123456Z"}
            structlog.processors.TimeStamper(fmt="iso"),
            # 6. Финальный рендерер (зависит от окружения)
            # DEBUG → ConsoleRenderer (цветной, читаемый)
            # PROD → JSONRenderer (JSON для ELK/Loki)
            structlog.dev.ConsoleRenderer()
            if config_settings.DEBUG
            else structlog.processors.JSONRenderer(),
        ],
        # === WRAPPER CLASS ===
        # Определяет, какой уровень логирования использовать.
        # make_filtering_bound_logger создаёт логгер, который фильтрует
        # сообщения ниже указанного уровня.
        #
        # Пример: LOG_LEVEL=WARNING
        # logger.info("...") → не запишется
        # logger.warning("...") → запишется
        wrapper_class=structlog.make_filtering_bound_logger(
            logging.getLevelName(config_settings.LOG_LEVEL)
        ),
        # === CONTEXT CLASS ===
        # Какой класс использовать для хранения контекста.
        # dict — самый простой и быстрый вариант.
        # Можно использовать collections.OrderedDict, если важен порядок полей.
        context_class=dict,
        # === LOGGER FACTORY ===
        # Какая фабрика создаёт логгеры.
        # PrintLoggerFactory — пишет в stdout (для консоли).
        # Для прода можно использовать LoggerFactory(logging.getLogger),
        # чтобы интегрировать со стандартным logging.
        logger_factory=structlog.PrintLoggerFactory(),
        # === CACHE ===
        # Кэшировать логгер при первом использовании.
        # False — создаём новый логгер каждый раз (безопасно для async).
        # True — быстрее, но может быть проблемы с contextvars в async.
        cache_logger_on_first_use=False,
    )


def get_logger(name: str) -> structlog.stdlib.BoundLogger:
    """
    Получить логгер для модуля.

    Использование:
        from app.core.logging import get_logger
        logger = get_logger(__name__)

        logger.info("order_created", order_id="abc123")
    """
    return structlog.get_logger(name)
