"""Последовательный benchmark ASR-моделей.

Один и тот же WAV последовательно прогоняется через каждую модель из
реестра: загрузка модели → инференс → сбор результата → выгрузка модели.

Это сознательное решение для машин с ограниченной памятью (Apple M2,
8 GB unified memory): никогда не держим в памяти больше одной benchmark-
модели одновременно (плюс production-модель, если сервис запущен).

Замеры разделяются: ``load_time_ms`` и ``inference_time_ms`` считаются
отдельно, ``total_time_ms = load + inference``.

Падение одной модели не останавливает benchmark: для неё возвращается
результат с ``success=false`` и коротким ``error`` (без stack trace —
подробности пишутся в логи).
"""

from __future__ import annotations

import time
from dataclasses import dataclass

from app.logging import get_logger
from app.stt.factory import STTModelFactory
from app.stt.registry import BENCHMARK_MODEL_KEYS

logger = get_logger(__name__)


@dataclass
class BenchmarkResult:
    """Результат одного прогона одной модели."""

    model: str
    text: str = ""
    load_time_ms: float = 0.0
    inference_time_ms: float = 0.0
    total_time_ms: float = 0.0
    success: bool = True
    error: str | None = None

    def to_dict(self) -> dict[str, object]:
        """Сериализация для JSON-ответа (без stack trace)."""
        payload: dict[str, object] = {
            "model": self.model,
            "text": self.text,
            "load_time_ms": round(self.load_time_ms, 1),
            "inference_time_ms": round(self.inference_time_ms, 1),
            "total_time_ms": round(self.total_time_ms, 1),
            "success": self.success,
        }
        if not self.success and self.error:
            payload["error"] = self.error
        return payload


class BenchmarkRunner:
    """Запускает все модели реестра последовательно на одном WAV."""

    def __init__(
        self,
        factory: STTModelFactory,
        model_keys: tuple[str, ...] = BENCHMARK_MODEL_KEYS,
    ) -> None:
        self._factory = factory
        self._model_keys = model_keys

    @property
    def model_keys(self) -> tuple[str, ...]:
        """Порядок прогона моделей."""
        return self._model_keys

    def run(self, wav_path: str, sample_count: int) -> list[BenchmarkResult]:
        """Прогнать WAV через все модели реестра последовательно."""
        logger.info(
            "benchmark_started",
            model_count=len(self._model_keys),
            wav_path=wav_path,
            sample_count=sample_count,
        )
        results: list[BenchmarkResult] = []
        for key in self._model_keys:
            result = self._run_model(key, wav_path, sample_count)
            results.append(result)
        logger.info(
            "benchmark_finished",
            model_count=len(results),
            success_count=sum(1 for r in results if r.success),
        )
        return results

    # ------------------------------------------------------------------
    # Внутреннее
    # ------------------------------------------------------------------

    def _run_model(self, key: str, wav_path: str, sample_count: int) -> BenchmarkResult:
        """Одна модель: load → transcribe → unload → результат."""
        logger.info("benchmark_model_started", model=key)
        adapter = self._factory.build(key)
        started = time.perf_counter()
        load_time_ms = 0.0
        inference_time_ms = 0.0
        try:
            adapter.load()
            load_time_ms = (time.perf_counter() - started) * 1000

            idx = time.perf_counter()
            text = adapter.transcribe_audio(wav_path, sample_count)
            inference_time_ms = (time.perf_counter() - idx) * 1000

            total = load_time_ms + inference_time_ms
            logger.info(
                "benchmark_model_finished",
                model=key,
                load_time_ms=round(load_time_ms, 1),
                inference_time_ms=round(inference_time_ms, 1),
                total_time_ms=round(total, 1),
                success=True,
            )
            return BenchmarkResult(
                model=key,
                text=text.strip(),
                load_time_ms=load_time_ms,
                inference_time_ms=inference_time_ms,
                total_time_ms=total,
                success=True,
            )
        except Exception as exc:
            total = load_time_ms + inference_time_ms
            logger.exception(
                "benchmark_model_finished",
                model=key,
                load_time_ms=round(load_time_ms, 1),
                inference_time_ms=round(inference_time_ms, 1),
                success=False,
            )
            return BenchmarkResult(
                model=key,
                load_time_ms=load_time_ms,
                inference_time_ms=inference_time_ms,
                total_time_ms=total,
                success=False,
                error=str(exc).strip() or type(exc).__name__,
            )
        finally:
            # Модель всегда выгружается, чтобы последовательный прогон
            # не держал в памяти накопленные чекпоинты.
            adapter.unload()