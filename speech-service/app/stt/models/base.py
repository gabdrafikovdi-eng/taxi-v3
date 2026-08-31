"""Базовый адаптер для всех GigaAM ASR-моделей.

Адаптер скрывает от ``STTClient``/benchmark различия между версиями
библиотеки gigaam:

* gigaam 0.1.0 (PyPI) — ``transcribe() -> str``,
  ``transcribe_longform() -> list[dict]`` (ключ ``transcription``);
* gigaam 0.2.0 (GitHub master) — ``transcribe() -> TranscriptionResult``
  (есть ``.text``), ``transcribe_longform() -> LongformTranscriptionResult``.

Кроме того, адаптер отвечает за:

* проверку, что библиотека gigaam установлена и имеет нужную версию;
* загрузку чекпоинта через ``gigaam.load_model``;
* освобождение модели из памяти (для последовательного benchmark).
"""

from __future__ import annotations

import gc
import importlib.metadata
import time
import wave
from typing import Any

import torch

from app.logging import get_logger
from app.stt.registry import ModelSpec

logger = get_logger(__name__)

#: GigaAM ограничивает ``transcribe`` 25 секундами.
LONGFORM_THRESHOLD_SAMPLES = 25 * 16000


def gigaam_dist_version() -> tuple[int, int]:
    """Версия установленной библиотеки gigaam как (major, minor)."""
    try:
        version = importlib.metadata.version("gigaam")
    except importlib.metadata.PackageNotFoundError:
        return (0, 0)
    parts = version.split(".")[:2]
    try:
        return int(parts[0]), int(parts[1])
    except (IndexError, ValueError):
        return (0, 0)


def wav_sample_count(wav_path: str) -> int:
    """Число семплов PCM16-WAV (для решения transcribe vs longform)."""
    try:
        with wave.open(wav_path, "rb") as wf:
            return wf.getnframes()
    except Exception:
        return 0


def _as_text(result: Any) -> str:
    """Нормализовать результат gigaam (любой версии) к строке."""
    if result is None:
        return ""
    if isinstance(result, str):
        return result
    text = getattr(result, "text", None)
    if isinstance(text, str):
        return text
    if isinstance(result, (list, tuple)):
        parts: list[str] = []
        for segment in result:
            segment_text: Any = None
            if isinstance(segment, dict):
                segment_text = segment.get("transcription") or segment.get("text")
            else:
                segment_text = getattr(segment, "text", None)
            if isinstance(segment_text, str):
                parts.append(segment_text.strip())
            elif segment_text is not None:
                parts.append(str(segment_text).strip())
        return " ".join(part for part in parts if part)
    return str(result).strip()


class GigaAMBaseAdapter:
    """Абстрактный адаптер GigaAM ASR. Ожидается подкласс под family."""

    family: str = ""

    def __init__(self, spec: ModelSpec, device: str) -> None:
        if spec.family != self.family:
            raise ValueError(
                f"Адаптер '{self.family}' не подходит для модели "
                f"'{spec.key}' (family='{spec.family}')"
            )
        self.spec = spec
        self.name = spec.key
        self.device = device
        self._model: Any = None
        self._load_time_ms: float = 0.0

    @property
    def loaded(self) -> bool:
        """Загружена ли модель в память."""
        return self._model is not None

    @property
    def load_time_ms(self) -> float:
        """Время последней загрузки модели (мс)."""
        return self._load_time_ms

    # ------------------------------------------------------------------
    # Жизненный цикл
    # ------------------------------------------------------------------

    def load(self) -> None:
        """Загрузить модель в память. Идемпотентна."""
        if self._model is not None:
            return
        logger.info("stt_model_load_started", model=self.name, device=self.device)
        started = time.perf_counter()
        try:
            gigaam = self._import_gigaam()
            installed = gigaam_dist_version()
            if installed < self.spec.min_gigaam_version:
                raise RuntimeError(
                    f"Модель '{self.name}' требует gigaam >= "
                    f"{self.spec.min_gigaam_version[0]}.{self.spec.min_gigaam_version[1]}, "
                    f"установлена {installed}. Установите gigaam из GitHub master "
                    f"(см. pyproject.toml, секция gigaam)."
                )
            model = gigaam.load_model(
                self.spec.gigaam_model,
                fp16_encoder=True,
                use_flash=False,
                device=self.device,
            )
            if model is None or not callable(getattr(model, "transcribe", None)):
                raise RuntimeError(
                    f"Модель '{self.spec.gigaam_model}' не является ASR-моделью "
                    "(нет метода transcribe). SSL/Emo-модели в транскрипции не участвуют."
                )
            self._model = model
        except Exception:
            self._model = None
            logger.exception(
                "stt_model_load_failed", model=self.name, device=self.device
            )
            raise
        self._load_time_ms = (time.perf_counter() - started) * 1000
        logger.info(
            "stt_model_loaded",
            model=self.name,
            device=self.device,
            gigaam_model=self.spec.gigaam_model,
            load_time_ms=round(self._load_time_ms, 1),
        )

    def unload(self) -> None:
        """Освободить модель из памяти.

        Сбрасываем ссылку на чекпоинт, собираем мусор и при необходимости
        чистим кэш выделенного backend-а (CUDA/MPS). Для CPU достаточно
        ссылок и ``gc.collect()``.
        """
        if self._model is None:
            return
        self._model = None
        gc.collect()
        if self.device.startswith("cuda") and torch.cuda.is_available():
            torch.cuda.empty_cache()
        elif self.device.startswith("mps"):
            mps_empty = getattr(getattr(torch, "mps", None), "empty_cache", None)
            if callable(mps_empty):
                mps_empty()
# ------------------------------------------------------------------
    # Инференс
    # ------------------------------------------------------------------

    def transcribe(self, wav_path: str) -> str:
        """Распознать короткий WAV (<=25 сек)."""
        model = self._require_loaded()
        result = model.transcribe(wav_path)
        return _as_text(result)

    def transcribe_longform(self, wav_path: str) -> str:
        """Распознать длинный WAV через сегментацию (если поддерживается)."""
        model = self._require_loaded()
        if not callable(getattr(model, "transcribe_longform", None)):
            logger.warning(
                "stt_longform_not_supported",
                model=self.name,
                fallback_to_short_transcribe=True,
            )
            return _as_text(model.transcribe(wav_path))
        result = model.transcribe_longform(wav_path)
        return _as_text(result)

    def transcribe_audio(self, wav_path: str, sample_count: int | None = None) -> str:
        """Распознать WAV любой длины (longform для длинных аудио)."""
        if sample_count is None:
            sample_count = wav_sample_count(wav_path)
        if sample_count > LONGFORM_THRESHOLD_SAMPLES:
            return self.transcribe_longform(wav_path)
        return self.transcribe(wav_path)

    # ------------------------------------------------------------------
    # Внутреннее
    # ------------------------------------------------------------------

    def _require_loaded(self) -> Any:
        if self._model is None:
            raise RuntimeError("Модель не загружена (вызовите load() первым)")
        return self._model

    def _import_gigaam(self) -> Any:
        try:
            import gigaam
        except Exception as exc:
            raise RuntimeError(
                "Библиотека gigaam не установлена или не импортируется. "
                "Установите её (см. pyproject.toml)."
            ) from exc
        return gigaam