"""Клиент STT поверх единого ASR-протокола.

``STTClient`` занимается только общими задачами:

* принимает PCM16 (mono, 16-bit LE) с любым sample rate;
* при необходимости ресемплирует до 16 кГц;
* упаковывает в WAV (временный файл);
* вызывает ASR-абстракцию (``transcribe`` / longform);
* логирует latency и ошибки;

и НЕ знает внутренний API конкретной модели (GigaAM/любая другая).
Если конкретная модель не потокобезопасна, инференс сериализуется
через ``threading.Lock``.
"""

from __future__ import annotations

import tempfile
import threading
import time

import numpy as np

from app.audio import converter
from app.logging import get_logger
from app.stt.protocols import ASRModel

logger = get_logger(__name__)

# Пиковое значение амплитуды, ниже которого сигнал считается тишиной
# (грубая проверка до VAD; VAD используется на уровне endpoints).
_SILENCE_PEAK = 200


class STTClient:
    """Обёртка над ASR-моделью для распознавания PCM16-байтов."""

    def __init__(self, model: ASRModel) -> None:
        self._model = model
        # Модели GigaAM не потокобезопасны — сериализуем инференс.
        self._lock = threading.Lock()

    @property
    def model_name(self) -> str:
        """Каноническое имя загруженной модели (например ``gigaam_v3_rnnt``)."""
        return self._model.name

    @property
    def model(self) -> ASRModel:
        """Доступ к нижележащей модели (для тестов/health)."""
        return self._model

    def transcribe(self, audio_bytes: bytes, sample_rate: int = 16000) -> tuple[str, float]:
        """Распознать речь в PCM16-аудио.

        :param audio_bytes: PCM 16-bit little-endian, mono.
        :param sample_rate: частота дискретизации входа (будет ресемплировано до 16 кГц).
        :return: ``(текст, inference_time_ms)``; при тишине/ошибке текст пустой.
        """
        if not audio_bytes:
            return "", 0.0

        pcm = audio_bytes
        if sample_rate != converter.TARGET_SAMPLE_RATE:
            pcm = converter.resample(
                audio_bytes, sample_rate, converter.TARGET_SAMPLE_RATE
            )

        if not self._has_speech(pcm):
            return "", 0.0

        wav_bytes = converter.to_wav(pcm, converter.TARGET_SAMPLE_RATE)
        logger.info("stt_inference_started", model=self._model.name)
        started = time.perf_counter()
        try:
            with self._lock:
                text = self._run_inference(wav_bytes)
        except Exception:
            inference_ms = (time.perf_counter() - started) * 1000
            logger.exception(
                "stt_inference_failed",
                model=self._model.name,
                inference_time_ms=round(inference_ms, 1),
            )
            return "", round(inference_ms, 1)

        inference_ms = (time.perf_counter() - started) * 1000
        logger.info(
            "stt_inference_finished",
            model=self._model.name,
            inference_time_ms=round(inference_ms, 1),
            text_length=len(text),
        )
        return text, round(inference_ms, 1)

    # ------------------------------------------------------------------
    # Внутреннее
    # ------------------------------------------------------------------

    def _run_inference(self, wav_bytes: bytes) -> str:
        """Выполнить инференс через временный WAV-файл."""
        with tempfile.NamedTemporaryFile(suffix=".wav", prefix="speech_") as tmp:
            tmp.write(wav_bytes)
            tmp.flush()
            sample_count = len(wav_bytes) // 2
            return self._model.transcribe_audio(tmp.name, sample_count).strip()

    def _has_speech(self, pcm_bytes: bytes) -> bool:
        """Грубая проверка тишины по пиковой амплитуде (без VAD)."""
        samples = np.frombuffer(pcm_bytes, dtype=np.int16)
        if samples.size == 0:
            return False
        return bool(np.abs(samples).max() >= _SILENCE_PEAK)