"""
Скрипт: вариант A (отдельный tool create_order) на реальных сервисах.

Отличие от tests/test_create_order_approaches.py: in-memory хранилище
заменено на реальные сервисы приложения + PostgreSQL.

Используются все пользовательские операции OrderService:
    create_order            -> OrderService.create_order
    set_pickup_address      -> OrderService.set_pickup
    set_destination_address -> OrderService.set_destination
    set_waypoint_address    -> OrderService.add_waypoint        (ADD  )
    update_waypoint_address -> OrderService.update_waypoint     (UPDATE)
    remove_waypoint         -> OrderService.remove_waypoint     (REMOVE)
    set_passenger_name      -> OrderService.set_passenger_name
    set_comment             -> OrderService.set_comment
    confirm_order           -> OrderService.confirm_order
    cancel_order            -> OrderService.cancel_order

Контракт со слоем app:
    * LLM-инструменты валидируются реальными Pydantic-схемами:
        - AddressInput   (app.schemas.address) — для адресных операций;
        - PassengerName  (app.schemas.address) — для имени пассажира;
        - OrderComment   (app.schemas.address) — для комментария;
        - SetPassengerNameInput (app.schemas.order) — tool schema set_passenger_name;
        - SetCommentInput       (app.schemas.order) — tool schema set_comment.
    * Не используются mock/in-memory реализации: только реальные
      AddressRepository / OrderRepository / AddressService / PricingService /
      StateService / OrderService / PostgreSQL.
    * Ошибки приходят из реальных исключений app.core.exceptions и маппятся
      в понятный LLM ответ.
    * Все операции — реальная бизнес-логика OrderService, дублирования
      алгоритмов внутри скрипта нет.
    * remove_waypoint в OrderService ПЕРЕНУМЕРОВЫВАЕТ оставшиеся waypoint
      (sequence_number 1..N в порядке возрастания). Скрипт это не дублирует,
      а лишь показывает фактический результат.

Запуск:
    uv run python scripts/test_order_service_approaches_a.py

Требует: БД PostgreSQL с данными Аскарово и OPENAI_* настройки в .env.

Address suggestions: похожие номера домов (suggestions) считает AddressService,
OrderService прокидывает их в AddressResolveError.suggestions при NOT_FOUND,
а скрипт добавляет их в текст ответа LLM (например, для «70 лет Октября 17к0»
показываются 17к1/17к2/17к3).
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Awaitable, Callable
from uuid import UUID, uuid4

from openai import AsyncOpenAI
from pydantic import BaseModel, Field, ValidationError

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
)
logger = logging.getLogger("order_service_approaches_a")

logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("httpcore").setLevel(logging.WARNING)
logging.getLogger("openai").setLevel(logging.WARNING)

PROJECT_ROOT = Path(__file__).resolve().parent.parent
EXIT_WORDS = {"выход", "exit", "quit", "q", "стоп", "stop"}
MAX_TOOL_CALL_ITERATIONS = 5


def load_env_file(path: Path) -> None:
    """Загружает переменные окружения из .env, если файл существует."""
    if not path.exists():
        return
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        os.environ.setdefault(key.strip(), value.strip())


# .env загружаем ДО импорта app-модулей (app.core.config создаёт Settings).
load_env_file(PROJECT_ROOT / ".env")

# Корень проекта — в sys.path: только он даёт import app / import tests.
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.core.config import address_config  # noqa: E402
from app.core.database import Base, async_session_factory, engine  # noqa: E402
from app.core.exceptions import (  # noqa: E402
    AddressResolveError,
    InvalidStateError,
    InvalidTransitionError,
    LimitWaypointError,
    OrderNotFoundError,
    PricingError,
    TooManyActiveOrdersError,
    WaypointNotFoundError,
)
from app.models.call_session import CallChannel, CallSession  # noqa: E402
from app.models.order_state import OrderState  # noqa: E402
from app.repositories.address_repo import AddressRepository  # noqa: E402
from app.repositories.order_repo import OrderRepository  # noqa: E402
from app.schemas.address import (  # noqa: E402
    AddressInput,
    AddressStatus,
    OrderComment,
    PassengerName,
)
from app.schemas.order import SetCommentInput, SetPassengerNameInput  # noqa: E402
from app.services.address.address_service import AddressService  # noqa: E402
from app.services.address.context_resolver import ContextResolver  # noqa: E402
from app.services.address.house_resolver import HouseResolver  # noqa: E402
from app.services.address.landmark_resolver import LandmarkResolver  # noqa: E402
from app.services.address.street_resolver import StreetResolver  # noqa: E402
from app.services.address.suggestion_service import AddressSuggestionService  # noqa: E402
from app.services.order_service import OrderService  # noqa: E402
from app.services.pricing_service import PricingService  # noqa: E402
from app.services.state_service import StateService  # noqa: E402
from sqlalchemy import text  # noqa: E402
from sqlalchemy.ext.asyncio import AsyncSession  # noqa: E402

# Промпт и базовые схемы (create/confirm/cancel) из эталонного скрипта.
# Для адресных схем используем уже готовую AddressInput из app.schemas.address.
SYSTEM_PROMPT_A = """Ты — диспетчер такси. Помоги пользователю заказать такси.

Ты можешь:
- оформить поездку;
- указать адрес подачи;
- указать адрес назначения;
- добавить / изменить / удалить промежуточную остановку;
- записать имя пассажира и комментарий;
- подтвердить заказ;
- отменить заказ.

Правила:
1. Сначала вызови create_order, чтобы создать заказ
2. Затем заполни адреса через set_pickup_address и set_destination_address
3. Когда оба адреса установлены, спроси подтверждение
4. При подтверждении вызови confirm_order
5. Для нового заказа вызови create_order ещё раз
6. Адрес передавай ЛИБО парой «street»+«house» одновременно, ЛИБО только
   «landmark» (ориентир), но НИКОГДА не оба варианта сразу.
7. НИКОГДА не выдумывай номер дома или ориентир. Если пользователь не назвал
   номер дома или ориентир — переспроси его, не придумывай данные сам.
8. Для НОВОЙ остановки используй set_waypoint_address; для ИЗМЕНЕНИЯ
   существующей — update_waypoint_address(sequence_number=...); для удаления —
   remove_waypoint(sequence_number=...). Никогда не добавляй новую остановку
   вместо изменения существующей.
9. Передавай name через set_passenger_name, комментарий — через set_comment.
### Справочник улиц Аскарово

Используй этот список для нормализации названий улиц.

Если пользовательское название отличается от названия в справочнике
из-за ошибки распознавания речи, опечатки, склонения или небольшого
фонетического искажения, определи наиболее вероятное название из
справочника.

В аргументе `street` всегда передавай каноническое название улицы
из справочника, если можешь уверенно сопоставить его.

Если уверенного сопоставления нет — НЕ выдумывай название и передай
распознанное название как есть.

Справочник:

- Истамгалина
- Бабича
- Шаймуратова
- Гагарина
- Файзрахмана Мустафина
- Ленина
- Мира
- Учалинская
- Молодежная
- Матросова
- Кирова
- Салавата Юлаева
- Тангатарская
- Партизанская
- Колхозная
- Южная
- Горная
- Комсомольская
- Уральская
- Шайхзады Бабича
- Урал Батыра
- Ак-Күлгин
- Шакимана
- Любимая
- Комарова
- 40 лет Победы
- 70 лет Октября
- Идиш
- Дружбы
- Пионерская
- Рауфа Давлетова
- Рихарда Зорге
- Лесная
- Октябрьская
- Диамиграта Абдрахманова
- Весенняя
- Юности
- Николая Гоголя
- Емельяна Пугачёва
- Малика Якшимбетова
- Миптата Хакимова
- Зайнаб Биишевой
- Загира Исмагилова
- Ишмухамета Мырзакаева
- Мустая Карима
- Сафи Истамгалина
- Расуля Кужахметова
- Фаттаха Ибрагимова
- 60 лет Победы
- Сосновая
- Солнечная
- Ишмурзы Хидиатова
- Луговая
- Рамазана Уметбаева
- Фазиля Искандера
- Курчатова
- Сагиры Мишар
- Бииш Батыра
- Тукая
- Целинная
- 50 лет Победы
- Пятая
- Салавата Кадырова
- Нажипа Асанбаева
- Рами Гарипова
- Валиахмета Сулейманова
- Индиры Султанбаевой
- Мисаля Муртасина
- 8 Марта
- 10 лет Победы
- Абзелиловская
- Александра Пушкина
- Гайфуллы Сарбаева
- Георгия Васева
- Караташ
- Кизильская
- Кинзи Арсланова
- Кыркты-Тау
- Михаила Лермонтова
- Мусы Джалиля
- Нургали Фахретдинова
- Сагиды Бердиной
- Салимьяна Гайнуллина
- Саляха Кулибая
- Северная
- Сергея Аксакова
- Сергея Есенина
- Центральная
- Шакира Биккулова
- Школьная"""

# Дополнение к системному промпту варианта A: напоминаем LLM про town/district.
SYSTEM_PROMPT_SERVICE = SYSTEM_PROMPT_A + """

### Дополнительно (реальные сервисы)
- В tools установки адреса доступны поля town и district.
- Если улица есть в нескольких районах (например «Ленина») и район не назван —
  уточни его у пользователя и передай в district.
- town передавать не обязательно: по умолчанию подставляется «Аскарово».

### Промежуточные остановки (waypoint)
- Новая остановка -> set_waypoint_address (OrderService.add_waypoint).
- Изменение существующей -> update_waypoint_address. Обязательно передай
  sequence_number той остановки, которую надо заменить.
  Примеры:
    «измени первую остановку на больницу» -> update_waypoint_address(sequence_number=1)
    «замени остановку номер 2»           -> update_waypoint_address(sequence_number=2)
- Удаление существующей -> remove_waypoint(sequence_number).
  Примеры:
    «удали первую остановку» -> remove_waypoint(sequence_number=1)
    «убери остановку»        -> если остановка одна: remove_waypoint(sequence_number=1)
- Если остановок несколько, а пользователь говорит просто «удали остановку»
  или «измени остановку» — уточни номер (sequence_number), НЕ выбирай сам.
- Полный путь пользователя не задаёт номера stop'ов; их нужно брать из
  последнего значения sequence_number, который вернул OrderService.
  После удаления OrderService ПЕРЕНУМЕРОВЫВАЕТ оставшиеся (1,2,3,...),
  поэтому числа меняются.
- Никогда не используй set_waypoint_address (add) для изменения существующей
  остановки и наоборот.

### Имя пассажира и комментарий
- «Меня зовут Дим», «запиши имя пассажира Иван» -> set_passenger_name(name=«Иван»).
- «Комментарий: подъехать ко второму подъезду», «водителю нужно позвонить»
  -> set_comment(comment=«...»).
- Не изменяй имя/комментарий напрямую в order — только через эти tools.

### Адресные ошибки (AddressService)
- AMBIGUOUS: найдено несколько вариантов — покажи варианты пользователю,
  попроси утончить район (district) и повтори set_*_address.
- NOT_FOUND: покажи причину и, если в ответе есть suggestions, предложи
  похожие варианты; попроси утончить адрес.
- INCOMPLETE: попроси недостающие данные (street+house либо landmark).
"""

# ---------------------------------------------------------------------------
# Схемы адресов для LLM — на основе готовой AddressInput из основного кода.
# AddressInput содержит ровно те поля, которые ожидает OrderService:
# town / district / street / house / landmark.
# ---------------------------------------------------------------------------
class OrderIdInput(BaseModel):
    """order_id для tools варианта A (все операции выполняются по заказу)."""

    order_id: UUID = Field(..., description="ID заказа, полученный из create_order")


class CreateOrderInput(BaseModel):
    """create_order(): аргументов нет."""

    pass


class ConfirmOrderInputA(OrderIdInput):
    """confirm_order(order_id)."""

    pass


class CancelOrderInputA(OrderIdInput):
    """cancel_order(order_id)."""

    pass


class SetPickupAddressInputA(AddressInput, OrderIdInput):
    """set_pickup_address: LLM заполняет AddressInput + order_id."""

    town: str | None = Field(
        default=None, description="Город (необязательно; по умолчанию Аскарово)"
    )
    district: str | None = Field(
        default=None,
        description="Район города (например: Центр, Северный, Южный, Восточный-1, Восточный-2, Даутово)",
    )
    street: str | None = Field(
        default=None,
        description="Улица (каноническое название из справочника). Если указана — нужен house.",
    )
    house: str | None = Field(default=None, description="Номер дома (если указана street).")
    landmark: str | None = Field(
        default=None,
        description="Ориентир вместо пары street+house (например: больница, магазин).",
    )


class SetDestinationAddressInputA(AddressInput, OrderIdInput):
    """set_destination_address: AddressInput + order_id."""

    town: str | None = Field(
        default=None, description="Город (необязательно; по умолчанию Аскарово)"
    )
    district: str | None = Field(
        default=None,
        description="Район города (например: Центр, Северный, Южный, Восточный-1, Восточный-2, Даутово)",
    )
    street: str | None = Field(
        default=None,
        description="Улица (каноническое название из справочника). Если указана — нужен house.",
    )
    house: str | None = Field(default=None, description="Номер дома (если указана street).")
    landmark: str | None = Field(
        default=None,
        description="Ориентир вместо пары street+house (например: больница, магазин).",
    )


class SetWaypointAddressInputA(AddressInput, OrderIdInput):
    """set_waypoint_address: AddressInput + order_id."""

    town: str | None = Field(
        default=None, description="Город (необязательно; по умолчанию Аскарово)"
    )
    district: str | None = Field(
        default=None,
        description="Район города (например: Центр, Северный, Южный, Восточный-1, Восточный-2, Даутово)",
    )
    street: str | None = Field(
        default=None,
        description="Улица (каноническое название из справочника). Если указана — нужен house.",
    )
    house: str | None = Field(default=None, description="Номер дома (если указана street).")
    landmark: str | None = Field(
        default=None,
        description="Ориентир вместо пары street+house (например: больница, магазин).",
    )


class OrderScopedSequence(BaseModel):
    """sequence_number для update/remove waypoint (реальный порядковый номер)."""

    sequence_number: int = Field(
        ...,
        ge=1,
        description="Порядковый номер остановки (sequence_number), как вернул OrderService.",
    )


class UpdateWaypointAddressInputA(AddressInput, OrderIdInput, OrderScopedSequence):
    """update_waypoint_address: заменить существующую остановку (AddressInput + order_id + sequence)."""

    town: str | None = Field(
        default=None, description="Город (необязательно; по умолчанию Аскарово)"
    )
    district: str | None = Field(
        default=None,
        description="Район города (например: Центр, Северный, Южный, Восточный-1, Восточный-2, Даутово)",
    )
    street: str | None = Field(
        default=None,
        description="Улица (каноническое название из справочника). Если указана — нужен house.",
    )
    house: str | None = Field(default=None, description="Номер дома (если указана street).")
    landmark: str | None = Field(
        default=None,
        description="Ориентир вместо пары street+house (например: больница, магазин).",
    )


class RemoveWaypointInputA(OrderIdInput, OrderScopedSequence):
    """remove_waypoint: удалить остановку по sequence_number."""

    pass

# ---------------------------------------------------------------------------
# Схемы tools (вариант A: create_order + адреса с order_id)
# Для set_passenger_name / set_comment используем ГОТОВЫЕ схемы проекта:
#   app.schemas.order.SetPassengerNameInput / SetCommentInput
# (handler конвертирует их в PassengerName/OrderComment перед вызовом OrderService).
# ---------------------------------------------------------------------------
TOOLS_A: list[tuple[str, str, type[BaseModel]]] = [
    (
        "create_order",
        "Создать новый заказ. Вызывай ПЕРВЫМ, перед заполнением адресов.",
        CreateOrderInput,
    ),
    (
        "set_pickup_address",
        "Установить адрес подачи (откуда забрать пассажира) для заказа. "
        "Адрес: либо street+house одновременно, либо ТОЛЬКО landmark. "
        "Не выдумывай номер дома — если его нет, переспроси.",
        SetPickupAddressInputA,
    ),
    (
        "set_destination_address",
        "Установить адрес назначения (куда ехать) для заказа. "
        "Адрес: либо street+house одновременно, либо ТОЛЬКО landmark. "
        "Не выдумывай номер дома — если его нет, переспроси.",
        SetDestinationAddressInputA,
    ),
    (
        "set_waypoint_address",
        "ДОБАВИТЬ новую остановку (промежуточную точку) в конец маршрута. "
        "Используй ТОЛЬКО для новой остановки. Для изменения/удаления "
        "существующей используй update_waypoint_address / remove_waypoint. "
        "Адрес: либо street+house одновременно, либо ТОЛЬКО landmark. "
        "Не выдумывай номер дома — если его нет, переспроси.",
        SetWaypointAddressInputA,
    ),
    (
        "update_waypoint_address",
        "ИЗМЕНИТЬ существующую остановку. Передай sequence_number той "
        "остановки, которую нужно заменить, и новый адрес "
        "(street+house либо landmark). Не добавляй новую остановку.",
        UpdateWaypointAddressInputA,
    ),
    (
        "remove_waypoint",
        "УДАЛИТЬ существующую остановку по sequence_number. "
        "После удаления оставшиеся waypoint перенумеровываются OrderService.",
        RemoveWaypointInputA,
    ),
    (
        "set_passenger_name",
        "Записать имя пассажира для заказа.",
        SetPassengerNameInput,
    ),
    (
        "set_comment",
        "Записать комментарий к заказу для водителя.",
        SetCommentInput,
    ),
    (
        "confirm_order",
        "Подтвердить заказ после того, как оба адреса установлены.",
        ConfirmOrderInputA,
    ),
    (
        "cancel_order",
        "Отменить заказ.",
        CancelOrderInputA,
    ),
]


def _tool_spec(name: str, description: str, model: type[BaseModel]) -> dict:
    """Строит OpenAI tool-spec из Pydantic-модели аргументов."""
    return {
        "type": "function",
        "function": {
            "name": name,
            "description": description,
            "parameters": model.model_json_schema(),
        },
    }


def build_tools_a() -> list[dict]:
    return [_tool_spec(name, desc, model) for name, desc, model in TOOLS_A]


def build_tool_models() -> dict[str, type[BaseModel]]:
    return {name: model for name, _, model in TOOLS_A}

# ---------------------------------------------------------------------------
# Состояние диалога поверх реальной БД
# ---------------------------------------------------------------------------
@dataclass
class ServiceState:
    """Состояние сеанса: реальные зависимости + статистика диалога."""

    session: AsyncSession
    call_session_id: UUID
    order_service: OrderService
    state_service: StateService
    order_repo: OrderRepository

    active_order_id: UUID | None = None
    order_ids: list[UUID] = field(default_factory=list)

    # Статистика для сводки
    history: list[dict] = field(default_factory=list)
    tool_call_counts: dict[str, int] = field(default_factory=dict)
    errors: list[str] = field(default_factory=list)
    total_tokens: int = 0


def record_tool_call(
    state: ServiceState, name: str, arguments: dict, result: dict
) -> None:
    """Логирует вызов tool, ведёт статистику вызовов и ошибок."""
    state.tool_call_counts[name] = state.tool_call_counts.get(name, 0) + 1
    logger.info("🔧 TOOL CALL: %s", name)
    logger.info("   Аргументы: %s", json.dumps(arguments, ensure_ascii=False))
    logger.info("   Результат: %s", json.dumps(result, ensure_ascii=False))
    if result.get("status") == "error":
        state.errors.append(f"{name}: {result.get('message', 'ошибка')}")


ToolHandler = Callable[[BaseModel, ServiceState], Awaitable[dict]]


# ---------------------------------------------------------------------------
# Обработчики: вариант A на реальных сервисах
# ---------------------------------------------------------------------------
async def handle_create_order(_args: CreateOrderInput, state: ServiceState) -> dict:
    """create_order() — создаёт новый DRAFT в БД и возвращает order_id."""
    # idempotency_key в схеме — VARCHAR(64); uuid достаточно уникален и короток.
    idempotency_key = str(uuid4())

    try:
        order = await state.order_service.create_order(
            call_session_id=state.call_session_id,
            idempotency_key=idempotency_key,
        )
    except TooManyActiveOrdersError as exc:
        logger.warning("create_order: достигнут лимит активных заказов: %s", exc)
        return {
            "status": "error",
            "message": f"Достигнут лимит активных заказов: {exc}",
        }
    except Exception as exc:  # noqa: BLE001 - ошибки возвращаем LLM
        logger.warning("create_order error: %s", exc)
        return {
            "status": "error",
            "message": f"Не удалось создать заказ: {exc}",
        }

    state.active_order_id = order.id
    state.order_ids.append(order.id)
    return {
        "status": "success",
        "message": f"Заказ создан. ID: {order.id}",
        "order_id": str(order.id),
    }


def _addr_input_from_args(args: BaseModel) -> AddressInput:
    """Превращает валидированные LLM-аргументы в готовую AddressInput.

    Аргументы tools уже наследуются от AddressInput, поэтому здесь идёт
    просто перенос адресных полей; результат передаётся в OrderService,
    который ожидает именно AddressInput.
    """
    return AddressInput(
        town=getattr(args, "town", None),
        district=getattr(args, "district", None),
        street=getattr(args, "street", None),
        house=getattr(args, "house", None),
        landmark=getattr(args, "landmark", None),
    )

# Причины, которые AddressService кладёт в AddressResolveError.message
# (в текущем OrderService для NOT_FOUND message = address_result.reason).
_NOT_FOUND_REASON_TEXT: dict[str, str] = {
    "town_or_district_not_found": "Не найден город или район.",
    "street_not_found": "Не найдена улица.",
    "house_not_found": "Не найден номер дома.",
    "landmark_not_found": "Не найден ориентир.",
}


def _address_error_result(exc: AddressResolveError) -> dict:
    """Превращает AddressResolveError в читаемый ответ для LLM.

    Работаем с реальными полями исключения:
      * AMBIGUOUS  -> exc.candidates (список вариантов адресов)
      * NOT_FOUND  -> exc.message (машинная причина от AddressService:
                      house_not_found / street_not_found / ...)
                      и exc.suggestions (похожие номера домов, которые
                      OrderService прокинул из AddressMatchResult).
    """
    if exc.status == AddressStatus.AMBIGUOUS:
        variants = [
            f"{i + 1}. {c.full_address}" for i, c in enumerate(exc.candidates or [])
        ]
        return {
            "status": "error",
            "message": "Найдено несколько адресов, уточни район:\n" + "\n".join(variants),
        }
    if exc.status == AddressStatus.NOT_FOUND:
        message = "Адрес не найден."
        reason_text = _NOT_FOUND_REASON_TEXT.get(exc.message or "")
        if reason_text:
            message += f" {reason_text}"

        suggestions = exc.suggestions or []
        if suggestions:
            variants = [
                f"{i + 1}. {c.full_address}" for i, c in enumerate(suggestions)
            ]
            message += (
                " Возможно, подойдёт похожий адрес:\n" + "\n".join(variants)
            )
        else:
            message += " Проверь название улицы / номер дома и попробуй ещё раз."

        return {
            "status": "error",
            "message": message,
        }
    if exc.status == AddressStatus.INCOMPLETE:
        return {
            "status": "error",
            "message": (
                "Для установки адреса нужна пара street+house ЛИБО ТОЛЬКО ориентир "
                "landmark."
            ),
        }
    return {
        "status": "error",
        "message": f"Не удалось разрешить адрес: {exc.status} — {exc}",
    }


async def _set_address(
    state: ServiceState,
    *,
    order_id: UUID,
    address: AddressInput,
    kind: str,
) -> dict:
    """Общий код для set_pickup / set_destination через OrderService."""
    try:
        if kind == "pickup":
            order = await state.order_service.set_pickup(order_id, address)
        else:
            order = await state.order_service.set_destination(order_id, address)
    except OrderNotFoundError:
        return {
            "status": "error",
            "message": "Заказ не найден. Сначала вызови create_order.",
        }
    except InvalidStateError as exc:
        return {
            "status": "error",
            "message": f"Операция недопустима в текущем состоянии заказа: {exc}",
        }
    except AddressResolveError as exc:
        return _address_error_result(exc)
    except PricingError as exc:
        return {
            "status": "error",
            "message": f"Не удалось рассчитать цену поездки: {exc}",
        }
    except Exception as exc:  # noqa: BLE001
        logger.exception("set_%s unresolved error", kind)
        return {
            "status": "error",
            "message": f"Внутренняя ошибка при установке адреса: {exc}",
        }

    label = "подачи" if kind == "pickup" else "назначения"
    addr_parts: list[str] = []
    if kind == "pickup":
        addr_parts.append(order.pickup_street or "-")
        if order.pickup_house:
            addr_parts.append(order.pickup_house)
    else:
        addr_parts.append(order.destination_street or "-")
        if order.destination_house:
            addr_parts.append(order.destination_house)

    message = f"Адрес {label} установлен: {' '.join(addr_parts)}"
    if getattr(order, "price", None) is not None:
        message += f". Стоимость поездки: {order.price} руб."
    elif order.has_both_addresses and not order.is_priced:
        message += ". Цена пока не рассчитана."

    return {"status": "success", "message": message, "order_id": str(order.id)}


async def handle_set_pickup(args: SetPickupAddressInputA, state: ServiceState) -> dict:
    return await _set_address(
        state,
        order_id=args.order_id,
        address=_addr_input_from_args(args),
        kind="pickup",
    )


async def handle_set_destination(
    args: SetDestinationAddressInputA, state: ServiceState
) -> dict:
    return await _set_address(
        state,
        order_id=args.order_id,
        address=_addr_input_from_args(args),
        kind="destination",
    )


async def handle_set_waypoint(
    args: SetWaypointAddressInputA, state: ServiceState
) -> dict:
    """set_waypoint_address() через OrderService.add_waypoint (реальная логика)."""
    address = _addr_input_from_args(args)
    try:
        order = await state.order_service.add_waypoint(args.order_id, address)
    except OrderNotFoundError:
        return {
            "status": "error",
            "message": "Заказ не найден. Сначала вызови create_order.",
        }
    except InvalidStateError as exc:
        return {
            "status": "error",
            "message": f"Операция недопустима в текущем состоянии заказа: {exc}",
        }
    except LimitWaypointError as exc:
        return {
            "status": "error",
            "message": f"Превышен лимит промежуточных остановок: {exc}",
        }
    except AddressResolveError as exc:
        return _address_error_result(exc)
    except PricingError as exc:
        return {
            "status": "error",
            "message": f"Не удалось рассчитать цену поездки: {exc}",
        }
    except Exception as exc:  # noqa: BLE001
        logger.exception("set_waypoint unresolved error")
        return {
            "status": "error",
            "message": f"Внутренняя ошибка при установке остановки: {exc}",
        }

    return _waypoint_summary("Остановка добавлена.", order=order, order_id=order.id)


def _waypoint_parts(order) -> list[str]:
    """Список строк «sequence_number. адрес» для фактических waypoint заказа."""
    waypoints = sorted(order.waypoints, key=lambda wp: wp.sequence_number)
    return [
        f"{wp.sequence_number}. {' '.join(p for p in (wp.waypoint_street, wp.waypoint_house) if p)}"
        for wp in waypoints
    ]


def _waypoint_summary(prefix: str, order, order_id: UUID) -> dict:
    """Формирует success-ответ для add/update/remove waypoint с реальными данными order."""
    parts = _waypoint_parts(order)
    message = prefix
    if parts:
        message += f" Промежуточные точки: {'; '.join(parts)}"
    else:
        message += " Промежуточных остановок больше нет."
    if getattr(order, "price", None) is not None:
        message += f". Стоимость поездки: {order.price} руб."
    elif order.has_both_addresses and not order.is_priced:
        message += ". Цена пока не рассчитана."
    return {"status": "success", "message": message, "order_id": str(order_id)}


async def handle_update_waypoint(
    args: UpdateWaypointAddressInputA, state: ServiceState
) -> dict:
    """update_waypoint_address() через OrderService.update_waypoint (реальная логика)."""
    address = _addr_input_from_args(args)
    try:
        order = await state.order_service.update_waypoint(
            args.order_id, args.sequence_number, address
        )
    except OrderNotFoundError:
        return {"status": "error", "message": "Заказ не найден. Сначала вызови create_order."}
    except InvalidStateError as exc:
        return {
            "status": "error",
            "message": f"Операция недопустима в текущем состоянии заказа: {exc}",
        }
    except WaypointNotFoundError as exc:
        return {
            "status": "error",
            "message": f"Остановка с номером {args.sequence_number} не найдена: {exc}",
        }
    except AddressResolveError as exc:
        return _address_error_result(exc)
    except PricingError as exc:
        return {"status": "error", "message": f"Не удалось рассчитать цену поездки: {exc}"}
    except Exception as exc:  # noqa: BLE001
        logger.exception("update_waypoint unresolved error")
        return {"status": "error", "message": f"Внутренняя ошибка при изменении остановки: {exc}"}

    return _waypoint_summary(
        f"Остановка {args.sequence_number} изменена.", order=order, order_id=order.id
    )


async def handle_remove_waypoint(args: RemoveWaypointInputA, state: ServiceState) -> dict:
    """remove_waypoint() через OrderService.remove_waypoint (реальная логика)."""
    try:
        order = await state.order_service.remove_waypoint(args.order_id, args.sequence_number)
    except OrderNotFoundError:
        return {"status": "error", "message": "Заказ не найден. Сначала вызови create_order."}
    except InvalidStateError as exc:
        return {
            "status": "error",
            "message": f"Операция недопустима в текущем состоянии заказа: {exc}",
        }
    except WaypointNotFoundError as exc:
        return {
            "status": "error",
            "message": f"Остановка с номером {args.sequence_number} не найдена: {exc}",
        }
    except PricingError as exc:
        return {"status": "error", "message": f"Не удалось рассчитать цену поездки: {exc}"}
    except Exception as exc:  # noqa: BLE001
        logger.exception("remove_waypoint unresolved error")
        return {"status": "error", "message": f"Внутренняя ошибка при удалении остановки: {exc}"}

    return _waypoint_summary(
        f"Остановка {args.sequence_number} удалена. Оставшиеся waypoint перенумерованы OrderService.",
        order=order,
        order_id=order.id,
    )


async def handle_set_passenger_name(args: SetPassengerNameInput, state: ServiceState) -> dict:
    """set_passenger_name() через OrderService (реальная логика)."""
    try:
        order = await state.order_service.set_passenger_name(
            args.order_id, PassengerName(first_name=args.name)
        )
    except OrderNotFoundError:
        return {"status": "error", "message": "Заказ не найден. Сначала вызови create_order."}
    except Exception as exc:  # noqa: BLE001
        logger.exception("set_passenger_name unresolved error")
        return {"status": "error", "message": f"Внутренняя ошибка при записи имени: {exc}"}

    return {
        "status": "success",
        "message": f"Имя пассажира установлено: {order.passenger_name}",
        "order_id": str(order.id),
    }


async def handle_set_comment(args: SetCommentInput, state: ServiceState) -> dict:
    """set_comment() через OrderService (реальная логика)."""
    try:
        order = await state.order_service.set_comment(
            args.order_id, OrderComment(comment=args.comment)
        )
    except OrderNotFoundError:
        return {"status": "error", "message": "Заказ не найден. Сначала вызови create_order."}
    except InvalidStateError as exc:
        return {
            "status": "error",
            "message": f"Операция недопустима в текущем состоянии заказа: {exc}",
        }
    except Exception as exc:  # noqa: BLE001
        logger.exception("set_comment unresolved error")
        return {"status": "error", "message": f"Внутренняя ошибка при записи комментария: {exc}"}

    return {
        "status": "success",
        "message": f"Комментарий к заказу установлен: {order.comment}",
        "order_id": str(order.id),
    }


async def _transition_order(
    state: ServiceState, order_id: UUID, target: OrderState
) -> dict:
    """Подтверждение/отмена через реальные OrderService.confirm_order/cancel_order."""
    try:
        if target == OrderState.CONFIRMED:
            order = await state.order_service.confirm_order(order_id)
        else:
            order = await state.order_service.cancel_order(order_id)
    except OrderNotFoundError:
        return {
            "status": "error",
            "message": "Заказ не найден. Сначала вызови create_order.",
        }
    except InvalidTransitionError as exc:
        return {"status": "error", "message": f"Нельзя перевести заказ: {exc}"}
    except Exception as exc:  # noqa: BLE001
        logger.exception("transition error")
        return {"status": "error", "message": f"Ошибка перевода заказа: {exc}"}

    label = "подтверждён" if target == OrderState.CONFIRMED else "отменён"
    price_part = f". Стоимость: {order.price} руб." if order.price else ""
    return {
        "status": "success",
        "message": f"Заказ {order.id} {label}{price_part}",
        "order_id": str(order.id),
    }


async def handle_confirm_order(args: ConfirmOrderInputA, state: ServiceState) -> dict:
    return await _transition_order(state, args.order_id, OrderState.CONFIRMED)


async def handle_cancel_order(args: CancelOrderInputA, state: ServiceState) -> dict:
    return await _transition_order(state, args.order_id, OrderState.CANCELLED)


def build_handlers() -> dict[str, ToolHandler]:
    return {
        "create_order": handle_create_order,
        "set_pickup_address": handle_set_pickup,
        "set_destination_address": handle_set_destination,
        "set_waypoint_address": handle_set_waypoint,
        "update_waypoint_address": handle_update_waypoint,
        "remove_waypoint": handle_remove_waypoint,
        "set_passenger_name": handle_set_passenger_name,
        "set_comment": handle_set_comment,
        "confirm_order": handle_confirm_order,
        "cancel_order": handle_cancel_order,
    }

# ---------------------------------------------------------------------------
# Основной цикл диалога
# ---------------------------------------------------------------------------
async def process_user_message(
    client: AsyncOpenAI,
    model: str,
    state: ServiceState,
    tools: list[dict],
    handlers: dict[str, ToolHandler],
    tool_models: dict[str, type[BaseModel]],
    user_text: str,
) -> None:
    """
    Обрабатывает одно сообщение пользователя:
    1. Добавляет его в историю
    2. Вызывает LLM (до MAX_TOOL_CALL_ITERATIONS раундов tool_calls)
    3. Выполняет обработчики и возвращает результаты в LLM
    4. Выводит финальный ответ диспетчера
    """
    state.history.append({"role": "user", "content": user_text})

    for iteration in range(MAX_TOOL_CALL_ITERATIONS):
        try:
            response = await client.chat.completions.create(
                model=model,
                messages=state.history,
                tools=tools,
                tool_choice="auto",
            )
        except Exception as exc:
            logger.error("Ошибка вызова LLM: %s", exc)
            print(f"\n⚠️  Ошибка вызова LLM: {exc}")
            return

        if response.usage:
            state.total_tokens += response.usage.total_tokens or 0

        message = response.choices[0].message

        # --- LLM хочет вызвать tools ---
        if message.tool_calls:
            # Сохраняем полный ответ ассистента (Gemini требует thought_signature).
            assistant_msg: dict[str, Any] = message.model_dump(exclude_none=True)
            state.history.append(assistant_msg)

            for tool_call in message.tool_calls:
                name = tool_call.function.name
                try:
                    arguments: dict = json.loads(tool_call.function.arguments or "{}")
                except json.JSONDecodeError:
                    logger.warning("Не удалось распарсить аргументы tool %s", name)
                    arguments = {}

                model_cls = tool_models.get(name)
                if model_cls is not None:
                    try:
                        parsed_args: BaseModel = model_cls.model_validate(arguments)
                    except ValidationError as exc:
                        result = {
                            "status": "error",
                            "message": (
                                f"Некорректные аргументы для {name}: "
                                f"{exc.errors(include_url=False)}"
                            ),
                        }
                        record_tool_call(state, name, arguments, result)
                        state.history.append(
                            {
                                "role": "tool",
                                "tool_call_id": tool_call.id,
                                "content": json.dumps(result, ensure_ascii=False),
                            }
                        )
                        continue
                else:
                    parsed_args = arguments

                handler = handlers.get(name)
                if handler is None:
                    result = {
                        "status": "error",
                        "message": f"Неизвестный tool: {name}",
                    }
                else:
                    result = await handler(parsed_args, state)

                record_tool_call(state, name, arguments, result)

                state.history.append(
                    {
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "content": json.dumps(result, ensure_ascii=False),
                    }
                )

            # Продолжаем цикл: снова вызываем LLM с результатами tools
            continue

        # --- Финальный ответ без tool_calls ---
        if message.content:
            print(f"\n🤖 Диспетчер: {message.content}")

        state.history.append({"role": "assistant", "content": message.content or ""})
        return

    logger.warning("Достигнут максимум итераций tool_calls (%d)", MAX_TOOL_CALL_ITERATIONS)
    print(f"\n⚠️  Достигнут максимум итераций tool_calls ({MAX_TOOL_CALL_ITERATIONS})")


async def run_interactive_dialog(
    client: AsyncOpenAI,
    model: str,
    state: ServiceState,
    tools: list[dict],
    handlers: dict[str, ToolHandler],
    tool_models: dict[str, type[BaseModel]],
) -> None:
    """Интерактивный цикл диалога. Завершение по словам «выход»/«exit»/«q»/«стоп»."""
    print("\nВводите сообщения. Для завершения введите «выход».")
    while True:
        try:
            user_text = input("\n🧑 Вы: ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break

        if not user_text:
            continue
        if user_text.lower() in EXIT_WORDS:
            break

        await process_user_message(
            client, model, state, tools, handlers, tool_models, user_text
        )

# ---------------------------------------------------------------------------
# Сводка
# ---------------------------------------------------------------------------
async def print_summary(state: ServiceState) -> None:
    """Выводит итоговую сводку по tool calls и заказам (данные из БД)."""
    print("\n" + "=" * 60)
    print("📊 СВОДКА (Вариант A на реальных сервисах):")
    print("─" * 60)

    total_calls = sum(state.tool_call_counts.values())
    print(f"  Всего tool calls: {total_calls}")
    for name, count in sorted(state.tool_call_counts.items()):
        print(f"  {name}: {count}")

    if state.errors:
        print(f"  Ошибки: {len(state.errors)}")
        for error in state.errors:
            print(f"    ⚠️  {error}")
    else:
        print("  Ошибки: 0")

    print(f"\n  Токенов на диалог: {state.total_tokens}")

    order_ids = getattr(state, "order_ids", [])
    print(f"  Заказов в БД: {len(order_ids)}")
    for order_id in order_ids:
        order = await state.order_repo.get_by_id(order_id)
        if order is None:
            print(f"    {order_id}: <заказ не найден в БД>")
            continue
        pickup = " ".join(
            p for p in (order.pickup_street or "", order.pickup_house or "") if p
        ) or "-"
        destination = " ".join(
            p for p in (order.destination_street or "", order.destination_house or "") if p
        ) or "-"
        print(
            f"    {order.id}: state={order.state.upper()}, "
            f'pickup="{pickup}", dest="{destination}", price={order.price}'
        )

    print("=" * 60)


# ---------------------------------------------------------------------------
# Главная функция
# ---------------------------------------------------------------------------
async def main() -> None:
    """Точка входа: подготовка БД/сервисов, запуск диалога, вывод сводки."""
    api_key = os.getenv("OPENAI_API_KEY", "").strip()
    base_url = os.getenv("OPENAI_BASE_URL", "").strip()
    model = os.getenv("OPENAI_MODEL", "").strip()

    if not api_key or not base_url or not model:
        logger.error(
            "Не заданы настройки LLM. Проверьте OPENAI_API_KEY, "
            "OPENAI_BASE_URL, OPENAI_MODEL в файле .env"
        )
        sys.exit(1)

    # Гарантируем наличие схемы (идемпотентно, как в conftest).
    async with engine.begin() as conn:
        await conn.execute(text("CREATE EXTENSION IF NOT EXISTS pg_trgm"))
        await conn.run_sync(Base.metadata.create_all)

    session = async_session_factory()

    # Создаём call session (Order.call_session_id — обязательный FK).
    call_session = CallSession(channel=CallChannel.CONSOLE)
    session.add(call_session)
    await session.commit()
    await session.refresh(call_session)
    logger.info("Создана CallSession: %s", call_session.id)

    address_repo = AddressRepository(session)
    order_repo = OrderRepository(session)
    address_service = AddressService(
        address_repo=address_repo,
        context_resolver=ContextResolver(
            address_repo=address_repo,
            default_town_name=address_config.default_town_name,
        ),
        street_resolver=StreetResolver(
            address_repo=address_repo,
            fuzzy_threshold=address_config.fuzzy_threshold,
            max_candidate=address_config.max_candidates,
        ),
        house_resolver=HouseResolver(address_repo=address_repo),
        landmark_resolver=LandmarkResolver(address_repo=address_repo),
        address_suggestion_service=AddressSuggestionService(address_repo=address_repo),
    )
    pricing_service = PricingService(address_repo)
    state_service = StateService()
    order_service = OrderService(
        state_service=state_service,
        address_service=address_service,
        pricing_service=pricing_service,
        order_repo=order_repo,
    )

    state = ServiceState(
        session=session,
        call_session_id=call_session.id,
        order_service=order_service,
        state_service=state_service,
        order_repo=order_repo,
    )
    state.history = [{"role": "system", "content": SYSTEM_PROMPT_SERVICE}]

    tools = build_tools_a()
    handlers = build_handlers()
    tool_models = build_tool_models()

    print("\nСкрипт: вариант A на реальных сервисах")
    print("🔧 Доступные tools:")
    for tool in tools:
        print(f"  - {tool['function']['name']}")

    client = AsyncOpenAI(
        api_key=api_key,
        base_url=base_url,
        timeout=60.0,
        max_retries=2,
    )

    try:
        await run_interactive_dialog(
            client=client,
            model=model,
            state=state,
            tools=tools,
            handlers=handlers,
            tool_models=tool_models,
        )
    finally:
        await client.close()
        await session.close()

    await print_summary(state)


if __name__ == "__main__":
    asyncio.run(main())