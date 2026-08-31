"""Адаптеры моделей и маппинг family -> класс адаптера.

Маппинг используется ``STTModelFactory``: выбор класса адаптера
происходит по ``family`` из ModelSpec, а не по ``if/elif`` в коде.
"""

from __future__ import annotations

from app.stt.models.base import GigaAMBaseAdapter
from app.stt.models.gigaam_multilingual import GigaAMMultilingualAdapter
from app.stt.models.gigaam_v2 import GigaAMV2Adapter
from app.stt.models.gigaam_v3 import GigaAMV3Adapter

__all__ = [
    "GigaAMBaseAdapter",
    "GigaAMV2Adapter",
    "GigaAMV3Adapter",
    "GigaAMMultilingualAdapter",
    "ADAPTER_FACTORIES",
]

#: family -> класс адаптера. Ключ соответствует ``ModelSpec.family``.
ADAPTER_FACTORIES: dict[str, type[GigaAMBaseAdapter]] = {
    "v2": GigaAMV2Adapter,
    "v3": GigaAMV3Adapter,
    "multilingual": GigaAMMultilingualAdapter,
}


def build_adapter(spec: object, device: str) -> GigaAMBaseAdapter:
    """Создать адаптер для ModelSpec по его family."""
    from app.stt.registry import ModelSpec

    if not isinstance(spec, ModelSpec):
        raise TypeError(f"Ожидается ModelSpec, получено {type(spec).__name__}")
    adapter_class = ADAPTER_FACTORIES.get(spec.family)
    if adapter_class is None:
        raise ValueError(f"Нет адаптера для family '{spec.family}'")
    return adapter_class(spec=spec, device=device)