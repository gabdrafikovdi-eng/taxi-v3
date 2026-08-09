"""Общие фикстуры и настройки тестового окружения."""

import os

# Устанавливаем переменные окружения ДО импорта app-модулей:
# app.core.database при импорте создаёт engine и читает DATABASE_URL,
# который строится из этих переменных.
os.environ.setdefault("POSTGRES_USER", "test")
os.environ.setdefault("POSTGRES_PASSWORD", "test")
os.environ.setdefault("POSTGRES_HOST", "localhost")
os.environ.setdefault("POSTGRES_PORT", "5432")
os.environ.setdefault("POSTGRES_DB", "test")
os.environ.setdefault("OPENAI_API_KEY", "test-key")
os.environ.setdefault("OPENAI_BASE_URL", "https://example.invalid")
os.environ.setdefault("OPENAI_MODEL", "test-model")

import pytest

from app.models.order import Order, OrderState


@pytest.fixture
def draft_order() -> Order:
    """Заказ в состоянии DRAFT без адресов и цены."""
    return Order(state=OrderState.DRAFT)


@pytest.fixture
def confirmable_order() -> Order:
    """Заказ в DRAFT, готовый к подтверждению: оба адреса и цена."""
    order = Order(state=OrderState.DRAFT)
    order.pickup_street_id = 1
    order.destination_street_id = 2
    order.price = 500
    return order


@pytest.fixture
def confirmed_order() -> Order:
    """Заказ в состоянии CONFIRMED."""
    return Order(state=OrderState.CONFIRMED)


@pytest.fixture
def completed_order() -> Order:
    """Заказ в состоянии COMPLETED."""
    return Order(state=OrderState.COMPLETED)


@pytest.fixture
def cancelled_order() -> Order:
    """Заказ в состоянии CANCELLED."""
    return Order(state=OrderState.CANCELLED)