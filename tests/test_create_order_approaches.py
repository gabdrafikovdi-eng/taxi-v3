"""
Скрипт для сравнения двух подходов к созданию заказа в LLM-диспетчере такси.

Вариант A: отдельный tool create_order
    LLM сама решает, когда создать заказ. Все остальные tools требуют order_id.

Вариант B: автоматическое создание + start_new_order
    Backend создаёт DRAFT при первом вызове set_pickup/set_destination.
    start_new_order нужен только для второго и последующих заказов.

Запуск:
    uv run python -m tests.test_create_order_approaches

Настройки LLM берутся из переменных окружения:
    OPENAI_API_KEY, OPENAI_BASE_URL, OPENAI_MODEL (см. .env)
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

from pydantic import BaseModel, ConfigDict, Field, ValidationError, model_validator

from openai import AsyncOpenAI

# ---------------------------------------------------------------------------
# Настройки логирования
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
)
logger = logging.getLogger("create_order_approaches")

# Отключаем шумные HTTP-логи от openai/httpx, чтобы не засорять вывод
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("httpcore").setLevel(logging.WARNING)
logging.getLogger("openai").setLevel(logging.WARNING)

# Максимум итераций tool_calls за один ход пользователя (защита от зацикливания)
MAX_TOOL_CALL_ITERATIONS = 5

# Корень проекта (родитель tests/)
PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Слова для выхода из диалога
EXIT_WORDS = {"выход", "exit", "quit", "q", "стоп", "stop"}


# ---------------------------------------------------------------------------
# Работа с .env (без pydantic-settings, только stdlib)
# ---------------------------------------------------------------------------
def load_env_file(path: Path) -> None:
    """Загружает переменные окружения из .env файла, если он существует."""
    if not path.exists():
        return

    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        # Пропускаем пустые строки, комментарии и строки без '=' (например,
        # случайный текст в начале .env)
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        key = key.strip()
        value = value.strip()
        os.environ.setdefault(key, value)


# ---------------------------------------------------------------------------
# InMemoryState — хранение состояния без БД
# ---------------------------------------------------------------------------
@dataclass
class InMemoryOrder:
    """Заказ в памяти (аналог модели Order без БД)."""

    id: UUID
    pickup: str | None = None
    destination: str | None = None
    waypoint: str | None = None
    price: int | None = None
    state: str = "draft"  # draft / confirmed / cancelled

    def __str__(self) -> str:
        """Краткое представление заказа для сводки."""
        return (
            f"{self.id}: {self.state.upper()}, "
            f'pickup="{self.pickup or "-"}", dest="{self.destination or "-"}"'
            f'waypoint="{self.waypoint or "-"}"'
        )


@dataclass
class InMemoryState:
    """Состояние диалога: заказы, история сообщений, статистика."""

    orders: list[InMemoryOrder] = field(default_factory=list)
    history: list[dict] = field(default_factory=list)
    active_order_id: UUID | None = None

    # Статистика для сводки
    tool_call_counts: dict[str, int] = field(default_factory=dict)
    errors: list[str] = field(default_factory=list)
    total_tokens: int = 0


def get_order_by_id(state: InMemoryState, order_id: UUID) -> InMemoryOrder | None:
    """Возвращает заказ по id или None."""
    for order in state.orders:
        if order.id == order_id:
            return order
    return None


def get_active_order(state: InMemoryState) -> InMemoryOrder | None:
    """Возвращает активный заказ (на который указывает active_order_id)."""
    if state.active_order_id is None:
        return None
    return get_order_by_id(state, state.active_order_id)


def record_tool_call(
    state: InMemoryState, name: str, arguments: dict, result: dict
) -> None:
    """Логирует вызов tool, ведёт статистику вызовов и ошибок."""
    state.tool_call_counts[name] = state.tool_call_counts.get(name, 0) + 1

    logger.info("🔧 TOOL CALL: %s", name)
    logger.info("   Аргументы: %s", json.dumps(arguments, ensure_ascii=False))
    logger.info("   Результат: %s", json.dumps(result, ensure_ascii=False))

    if result.get("status") == "error":
        state.errors.append(f"{name}: {result.get('message', 'ошибка')}")


# Тип обработчика tool: (валидированная Pydantic-модель аргументов, state) -> dict
ToolHandler = Callable[[BaseModel, InMemoryState], Awaitable[dict]]


# ---------------------------------------------------------------------------
# Pydantic-схемы аргументов tools
#   LLM при вызове функции заполняет JSON, который проходит валидацию через
#   соответствующую Pydantic-модель. JSON-схема для tools генерируется из этих
#   же моделей (model_json_schema()), так что контракт единый.
# ---------------------------------------------------------------------------
class AddressFields(BaseModel):
    """
    Общие поля адреса для tools установки адресов.

    Business-правила (проверяются автоматически при создании модели через
    @model_validator, т.е. в момент AddressInput(**arguments) от LLM):
      * street и house указываются ТОЛЬКО вместе;
      * должен быть задан либо набор street+house, либо ориентир landmark.
    Нарушение правил выбрасывает ValidationError, который перехватывается в
    process_user_message и возвращается LLM как результат инструмента с ошибкой.
    """

    model_config = ConfigDict(str_strip_whitespace=True)

    street: str | None = Field(
        default=None,
        description=(
            "Улица. Если указана — обязательно нужно указать и house. "
            "ЛИБО используй только landmark."
        ),
    )
    house: str | None = Field(
        default=None,
        description="Номер дома. Обязателен, если указана street.",
    )
    landmark: str | None = Field(
        default=None,
        description=(
            "Ориентир (напр. «больница», «магазин»). Указывай ТОЛЬКО landmark "
            "ВМЕСТО пары street+house, не вместе с ними."
        ),
    )

    @model_validator(mode="after")
    def check_address(self) -> "AddressFields":
        # Если указана улица или дом, то должны быть указаны оба
        if (self.street is not None) != (self.house is not None):
            raise ValueError(
                "Если указывается улица или дом, необходимо указать оба поля: "
                "street и house"
            )
        # Если ни улица, ни дом, ни ориентир не указаны — адрес пустой
        if self.street is None and self.house is None and self.landmark is None:
            raise ValueError(
                "Необходимо указать либо улицу и номер дома (street+house), "
                "либо ориентир (landmark)"
            )
        return self


class OrderIdField(BaseModel):
    """Поле order_id для tools варианта A."""

    order_id: UUID = Field(..., description="ID заказа, полученный из create_order")


# --- Вариант A: все tools требуют order_id ---
class CreateOrderInput(BaseModel):
    """create_order(): аргументов нет."""

    pass


class SetPickupAddressInputA(AddressFields, OrderIdField):
    """set_pickup_address(order_id, street, house?, landmark?)."""

    pass


class SetDestinationAddressInputA(AddressFields, OrderIdField):
    """set_destination_address(order_id, street, house?, landmark?)."""

    pass


class SetWaypointAddressInputA(AddressFields, OrderIdField):
    """set_waypoint_address(order_id, street, house?, landmark?)."""

    pass


class ConfirmOrderInputA(OrderIdField):
    """confirm_order(order_id)."""

    pass


class CancelOrderInputA(OrderIdField):
    """cancel_order(order_id)."""

    pass


# --- Вариант B: без order_id (автоматическое создание DRAFT) ---
class SetPickupAddressInputB(AddressFields):
    """set_pickup_address(street, house?, landmark?)."""

    pass


class SetDestinationAddressInputB(AddressFields):
    """set_destination_address(street, house?, landmark?)."""

    pass


class ConfirmOrderInputB(BaseModel):
    """confirm_order(): аргументов нет."""

    pass


class CancelOrderInputB(BaseModel):
    """cancel_order(): аргументов нет."""

    pass


class StartNewOrderInputB(BaseModel):
    """start_new_order(): аргументов нет."""

    pass


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


# ---------------------------------------------------------------------------
# Вариант A: Отдельный tool create_order
# ---------------------------------------------------------------------------
async def handle_create_order_a(_args: CreateOrderInput, state: InMemoryState) -> dict:
    """create_order() — создаёт новый DRAFT и возвращает order_id."""
    order = InMemoryOrder(id=uuid4(), state="draft")
    state.orders.append(order)
    state.active_order_id = order.id
    return {
        "status": "success",
        "message": f"Заказ создан. ID: {order.id}",
        "order_id": str(order.id),
    }


async def handle_set_pickup_a(args: SetPickupAddressInputA, state: InMemoryState) -> dict:
    """set_pickup_address(order_id, street, house?, landmark?)."""
    order = _resolve_order_a(args, state)
    if order is None:
        return {
            "status": "error",
            "message": "Сначала создайте заказ — вызовите create_order",
        }

    order.pickup = _format_address(args)
    return {
        "status": "success",
        "message": f"Адрес подачи установлен: {order.pickup}",
        "order_id": str(order.id),
    }


async def handle_set_destination_a(
    args: SetDestinationAddressInputA, state: InMemoryState
) -> dict:
    """set_destination_address(order_id, street, house?, landmark?)."""
    order = _resolve_order_a(args, state)
    if order is None:
        return {
            "status": "error",
            "message": "Сначала создайте заказ — вызовите create_order",
        }

    order.destination = _format_address(args)
    return {
        "status": "success",
        "message": f"Адрес назначения установлен: {order.destination}",
        "order_id": str(order.id),
    }


async def handle_set_waypoint(args: SetWaypointAddressInputA, state: InMemoryState) -> dict:
    """set_waypoint_address(order_id, street, house?, landmark?)."""
    order = _resolve_order_a(args, state)
    if order is None:
        return {
            "status": "error",
            "message": "Сначала создайте заказ — вызовите create_order",
        }
    order.waypoint = _format_address(args)
    return {
        "status": "success",
        "message": f"Адрес назначения установлен: {order.waypoint}",
        "order_id": str(order.id),
    }


async def handle_confirm_order_a(args: ConfirmOrderInputA, state: InMemoryState) -> dict:
    """confirm_order(order_id) — подтверждает заказ."""
    order = _resolve_order_a(args, state)
    if order is None:
        return {
            "status": "error",
            "message": "Сначала создайте заказ — вызовите create_order",
        }
    if order.pickup is None or order.destination is None:
        return {
            "status": "error",
            "message": "Нельзя подтвердить заказ: не указаны адрес подачи и/или назначения",
        }

    order.state = "confirmed"
    # Простая оценка стоимости (заглушка, без реальной БД)
    order.price = 200
    return {
        "status": "success",
        "message": f"Заказ {order.id} подтверждён. Стоимость: {order.price} руб.",
        "order_id": str(order.id),
    }


async def handle_cancel_order_a(args: CancelOrderInputA, state: InMemoryState) -> dict:
    """cancel_order(order_id) — отменяет заказ."""
    order = _resolve_order_a(args, state)
    if order is None:
        return {
            "status": "error",
            "message": "Сначала создайте заказ — вызовите create_order",
        }

    order.state = "cancelled"
    return {
        "status": "success",
        "message": f"Заказ {order.id} отменён",
        "order_id": str(order.id),
    }


def _resolve_order_a(args: OrderIdField, state: InMemoryState) -> InMemoryOrder | None:
    """Достаёт заказ по order_id (Вариант A). Возвращает None, если заказа нет."""
    return get_order_by_id(state, args.order_id)


# ---------------------------------------------------------------------------
# Вариант B: Автоматическое создание + start_new_order
# ---------------------------------------------------------------------------
def ensure_active_order(state: InMemoryState) -> InMemoryOrder:
    """
    Вариант B: создаёт DRAFT автоматически, если активного заказа нет.
    Вызывается при set_pickup_address / set_destination_address.
    """
    order = get_active_order(state)
    if order is None:
        order = InMemoryOrder(id=uuid4(), state="draft")
        state.orders.append(order)
        state.active_order_id = order.id
    return order


async def handle_set_pickup_b(args: SetPickupAddressInputB, state: InMemoryState) -> dict:
    """set_pickup_address(street, house?, landmark?) — без order_id."""
    order = ensure_active_order(state)
    order.pickup = _format_address(args)
    return {
        "status": "success",
        "message": f"Адрес подачи установлен: {order.pickup}",
        "order_id": str(order.id),
    }


async def handle_set_destination_b(
    args: SetDestinationAddressInputB, state: InMemoryState
) -> dict:
    """set_destination_address(street, house?, landmark?) — без order_id."""
    order = ensure_active_order(state)
    order.destination = _format_address(args)
    return {
        "status": "success",
        "message": f"Адрес назначения установлен: {order.destination}",
        "order_id": str(order.id),
    }


async def handle_confirm_order_b(_args: ConfirmOrderInputB, state: InMemoryState) -> dict:
    """confirm_order() — подтверждает текущий активный заказ."""
    order = get_active_order(state)
    if order is None:
        return {"status": "error", "message": "Нет активного заказа для подтверждения"}
    if order.pickup is None or order.destination is None:
        return {
            "status": "error",
            "message": "Нельзя подтвердить заказ: не указаны адрес подачи и/или назначения",
        }

    order.state = "confirmed"
    order.price = 200
    return {
        "status": "success",
        "message": f"Заказ {order.id} подтверждён. Стоимость: {order.price} руб.",
        "order_id": str(order.id),
    }


async def handle_cancel_order_b(_args: CancelOrderInputB, state: InMemoryState) -> dict:
    """cancel_order() — отменяет текущий активный заказ."""
    order = get_active_order(state)
    if order is None:
        return {"status": "error", "message": "Нет активного заказа для отмены"}

    order.state = "cancelled"
    return {
        "status": "success",
        "message": f"Заказ {order.id} отменён",
        "order_id": str(order.id),
    }


async def handle_start_new_order_b(_args: StartNewOrderInputB, state: InMemoryState) -> dict:
    """start_new_order() — создаёт новый DRAFT (для мульти-заказов)."""
    order = InMemoryOrder(id=uuid4(), state="draft")
    state.orders.append(order)
    state.active_order_id = order.id
    return {
        "status": "success",
        "message": f"Новый заказ создан. ID: {order.id}",
        "order_id": str(order.id),
    }


# ---------------------------------------------------------------------------
# Общие утилиты
# ---------------------------------------------------------------------------
def _format_address(addr: AddressFields) -> str:
    """Собирает адрес из street/house/landmark."""
    parts = [p for p in (addr.street, addr.house, addr.landmark) if p]
    return " ".join(parts).strip()


# ---------------------------------------------------------------------------
# System prompts
# ---------------------------------------------------------------------------
SYSTEM_PROMPT_A = """Ты — диспетчер такси. Помоги пользователю заказать такси.

Ты можешь:
- оформить поездку;
- указать адрес подачи;
- указать адрес назначения;
- добавить промежуточную остановку;
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

SYSTEM_PROMPT_B = """Ты — диспетчер такси. Помоги пользователю заказать такси.

Правила:
1. Когда пользователь называет адрес подачи, вызови set_pickup_address
2. Когда пользователь называет адрес назначения, вызови set_destination_address
3. Когда оба адреса установлены, спроси подтверждение
4. При подтверждении вызови confirm_order
5. Если пользователь хочет ещё один заказ, вызови start_new_order
6. Когда пользоваться называет адрес остановки(промежуточной точки), вызови set_waypoint_address
7. Адрес передавай ЛИБО парой «street»+«house» одновременно, ЛИБО только
   «landmark» (ориентир), но НИКОГДА не оба варианта сразу.
8. НИКОГДА не выдумывай номер дома или ориентир. Если пользователь не назвал
   номер дома или ориентир — переспроси его, не придумывай данные сам.
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
- Школьнаяы
"""


# ---------------------------------------------------------------------------
# Схемы tools
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
        "Установить адрес остановки (промежуточная точка) для заказа. "
        "Адрес: либо street+house одновременно, либо ТОЛЬКО landmark. "
        "Не выдумывай номер дома — если его нет, переспроси.",
        SetWaypointAddressInputA,
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


def build_tools_a() -> list[dict]:
    """OpenAI tool-specs для варианта A (с order_id)."""
    return [_tool_spec(name, desc, model) for name, desc, model in TOOLS_A]


TOOLS_B: list[tuple[str, str, type[BaseModel]]] = [
    (
        "set_pickup_address",
        "Установить адрес подачи (откуда забрать пассажира) для текущего заказа. "
        "Адрес: либо street+house одновременно, либо ТОЛЬКО landmark. "
        "Не выдумывай номер дома — если его нет, переспроси.",
        SetPickupAddressInputB,
    ),
    (
        "set_destination_address",
        "Установить адрес назначения (куда ехать) для текущего заказа. "
        "Адрес: либо street+house одновременно, либо ТОЛЬКО landmark. "
        "Не выдумывай номер дома — если его нет, переспроси.",
        SetDestinationAddressInputB,
    ),
    (
        "confirm_order",
        "Подтвердить текущий заказ после того, как оба адреса установлены.",
        ConfirmOrderInputB,
    ),
    (
        "cancel_order",
        "Отменить текущий заказ.",
        CancelOrderInputB,
    ),
    (
        "start_new_order",
        "Создать новый заказ. Вызывай только для второго и последующих заказов.",
        StartNewOrderInputB,
    ),
]


def build_tools_b() -> list[dict]:
    """OpenAI tool-specs для варианта B (без order_id)."""
    return [_tool_spec(name, desc, model) for name, desc, model in TOOLS_B]


def build_tool_models(variant: str) -> dict[str, type[BaseModel]]:
    """Возвращает {имя tool: Pydantic-модель} для валидации аргументов LLM."""
    table = TOOLS_A if variant == "A" else TOOLS_B
    return {name: model for name, _, model in table}


# ---------------------------------------------------------------------------
# Конфигурация вариантов: system prompt + tools + handlers
# ---------------------------------------------------------------------------
def build_handlers_a() -> dict[str, ToolHandler]:
    """Обработчики для варианта A."""
    return {
        "create_order": handle_create_order_a,
        "set_pickup_address": handle_set_pickup_a,
        "set_destination_address": handle_set_destination_a,
        "set_waypoint_address": handle_set_waypoint,
        "confirm_order": handle_confirm_order_a,
        "cancel_order": handle_cancel_order_a,
    }


def build_handlers_b() -> dict[str, ToolHandler]:
    """Обработчики для варианта B."""
    return {
        "set_pickup_address": handle_set_pickup_b,
        "set_destination_address": handle_set_destination_b,
        "confirm_order": handle_confirm_order_b,
        "cancel_order": handle_cancel_order_b,
        "start_new_order": handle_start_new_order_b,
    }


def get_variant_config(
    variant: str,
) -> tuple[str, list[dict], dict[str, ToolHandler], dict[str, type[BaseModel]]]:
    """Возвращает (system_prompt, tools, handlers, tool_models) для варианта."""
    if variant == "A":
        return (
            SYSTEM_PROMPT_A,
            build_tools_a(),
            build_handlers_a(),
            build_tool_models("A"),
        )
    return (
        SYSTEM_PROMPT_B,
        build_tools_b(),
        build_handlers_b(),
        build_tool_models("B"),
    )


# ---------------------------------------------------------------------------
# Основной цикл диалога
# ---------------------------------------------------------------------------
async def process_user_message(
    client: AsyncOpenAI,
    model: str,
    state: InMemoryState,
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

        # Учитываем токены (метрика для сравнения)
        if response.usage:
            state.total_tokens += response.usage.total_tokens or 0

        message = response.choices[0].message

        # --- LLM хочет вызвать tools ---
        if message.tool_calls:
            # Сохраняем ответ ассистента с tool_calls в историю.
            # Используем полный model_dump, чтобы сохранить все поля ответа,
            # включая нестандартные. Gemini API требует возвращать
            # thought_signature вместе с function call при повторной отправке,
            # иначе вернётся ошибка 400 "Function call is missing a
            # thought_signature". Ручное построение tool_calls теряло это поле.
            assistant_msg: dict[str, Any] = message.model_dump(exclude_none=True)
            state.history.append(assistant_msg)

            for tool_call in message.tool_calls:
                name = tool_call.function.name
                try:
                    arguments: dict = json.loads(tool_call.function.arguments or "{}")
                except json.JSONDecodeError:
                    logger.warning("Не удалось распарсить аргументы tool %s", name)
                    arguments = {}

                # Валидируем аргументы LLM через Pydantic-схему соответствующего tool
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

    # Защита от бесконечного цикла
    logger.warning(
        "Достигнут максимум итераций tool_calls (%d)", MAX_TOOL_CALL_ITERATIONS
    )
    print(f"\n⚠️  Достигнут максимум итераций tool_calls ({MAX_TOOL_CALL_ITERATIONS})")


async def run_interactive_dialog(
    client: AsyncOpenAI,
    model: str,
    state: InMemoryState,
    tools: list[dict],
    handlers: dict[str, ToolHandler],
    tool_models: dict[str, type[BaseModel]],
) -> None:
    """
    Интерактивный цикл диалога: пользователь вводит сообщения,
    LLM отвечает. Завершение по словам «выход»/«exit»/«quit»/«q»/«стоп»/«stop».
    """
    print("\nВводите сообщения. Для завершения введите «выход».")
    while True:
        try:
            user_text = input("\n🧑 Вы: ").strip()
        except EOFError, KeyboardInterrupt:
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
def print_summary(variant: str, state: InMemoryState) -> None:
    """Выводит итоговую сводку по tool calls и заказам."""
    print("\n" + "=" * 60)
    print(f"📊 СВОДКА (Вариант {variant}):")
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
    print(f"  Создано заказов: {len(state.orders)}")

    for order in state.orders:
        print(f"    {order}")

    print("=" * 60)


# ---------------------------------------------------------------------------
# Главная функция
# ---------------------------------------------------------------------------
async def main() -> None:
    """Точка входа: выбор варианта, запуск диалога, вывод сводки."""
    # 1. Загружаем .env и проверяем настройки LLM
    load_env_file(PROJECT_ROOT / ".env")

    api_key = os.getenv("OPENAI_API_KEY", "").strip()
    base_url = os.getenv("OPENAI_BASE_URL", "").strip()
    model = os.getenv("OPENAI_MODEL", "").strip()

    if not api_key or not base_url or not model:
        logger.error(
            "Не заданы настройки LLM. Проверьте OPENAI_API_KEY, "
            "OPENAI_BASE_URL, OPENAI_MODEL в файле .env"
        )
        sys.exit(1)

    # 2. Выбор варианта
    print()
    print("Скрипт сравнения подходов к созданию заказа в LLM-диспетчере такси")
    print("  Вариант A: отдельный tool create_order")
    print("  Вариант B: автоматическое создание + start_new_order")

    try:
        variant = input("\nВыберите вариант (A/B): ").strip().upper()
    except EOFError, KeyboardInterrupt:
        print("\nЗавершение.")
        return

    # Нормализация кириллицы: «А» -> "A", «Б» -> "B"
    variant = {"А": "A", "Б": "B"}.get(variant, variant)

    if variant not in ("A", "B"):
        logger.error("Недопустимый вариант. Ожидается A или B.")
        sys.exit(1)

    # 3. Конфигурация варианта
    system_prompt, tools, handlers, tool_models = get_variant_config(variant)

    print(f"\n🔧 Доступные tools (Вариант {variant}):")
    for tool in tools:
        print(f"  - {tool['function']['name']}")

    # 4. Состояние и клиент
    state = InMemoryState()
    state.history = [{"role": "system", "content": system_prompt}]

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
        # Корректное закрытие клиента
        await client.close()

    # 6. Сводка
    print_summary(variant, state)


if __name__ == "__main__":
    asyncio.run(main())
