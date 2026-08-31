"""Фабрика STT-моделей.

Продакшен использует ровно одну модель, выбранную через ``STT_MODEL``:

    settings.STT_MODEL
          │
          ▼
    STTModelFactory   ─►  ModelSpec (из registry)
          │
          ▼
    адаптер (GigaAMV2/V3/Multilingual) ─► load()
          │
          ▼
    STTClient

Такой же factory применяется benchmark-раннером для последовательной
загрузки/выгрузки каждой модели из реестра.
"""

from __future__ import annotations

import time

import torch

from app.logging import get_logger
from app.stt.models import build_adapter
from app.stt.registry import ModelSpec, canonical_model_key, get_model_spec
from app.stt.protocols import ASRModel

logger = get_logger(__name__)


def pick_stt_device(device: str, fallback_to_cpu: bool) -> str:
    """Выбрать реальное устройство для STT-моделей.

    :param device: запрошенное устройство (``cpu``, ``cuda:0``, ``mps``).
    :param fallback_to_cpu: если CUDA недоступна — упасть на CPU.
    """
    device = device.strip().lower()
    cuda_available = torch.cuda.is_available()
    if device == "cpu" or device.startswith("mps"):
        return device
    if device.startswith("cuda") and cuda_available:
        return device
    if fallback_to_cpu:
        logger.warning(
            "stt_device_unavailable_fallback_to_cpu",
            requested=device,
            cuda_available=cuda_available,
        )
        return "cpu"
    raise RuntimeError(
        f"STT device '{device}' is unavailable and STT_FALLBACK_TO_CPU is disabled"
        f" (cuda_available={cuda_available})"
    )


class STTModelFactory:
    """Создаёт и загружает адаптеры ASR-моделей из единого реестра."""

    def __init__(self, model_key: str, device: str) -> None:
        self.model_key = canonical_model_key(model_key)
        self.spec = get_model_spec(self.model_key)
        self.device = device

    def build(self, model_key: str | None = None) -> ASRModel:
        """Создать (без загрузки) адаптер для модели из реестра.

        :param model_key: канонический ключ; по умолчанию — production-модель.
        """
        spec = self.spec if model_key is None else get_model_spec(model_key)
        logger.info(
            "stt_adapter_created", model=spec.key, family=spec.family, device=self.device
        )
        return build_adapter(spec, self.device)

    def load(self, model_key: str | None = None) -> tuple[ASRModel, float]:
        """Создать адаптер и загрузить модель.

        Возвращает ``(adapter, load_time_ms)``. Продакшен вызывает этот
        метод при старте; benchmark вызывает его под-моделью в цикле.
        """
        adapter = self.build(model_key)
        started = time.perf_counter()
        adapter.load()
        load_time_ms = (time.perf_counter() - started) * 1000
        return adapter, load_time_ms