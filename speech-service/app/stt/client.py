"""Клиент STT на базе GigaAM (RNNT/CTC).

Загруженная один раз модель принимает путь к WAV-файлу. Клиент
конвертирует PCM-байты через audio.converter, кладёт во временный
файл и вызывает ``transcribe`` (короткие) либо ``transcribe_longform``
(длинные) GigaAM. Все ошибки модели логируются, при тишине или сбое
возвращается пустая строка.
"""

from __future__ import annotations

import tempfile
import threading
import time
from typing import Protocol

import numpy as np

from app.audio import converter
from app.logging import get_logger

logger = get_logger(__name__)

# GigaAM ограничивает transcribe 25 секундами (LONGFORM_THRESHOLD).
_LONGFORM_THRESHOLD_SAMPLES = 25 * converter.TARGET_SAMPLE_RATE
# Пиковое значение амплитуды, ниже которого сигнал считается тишиной.
_SILENCE_PEAK = 200


class GigaAMASRModel(Protocol):
    """Минимальный интерфейс модели GigaAM для распознавания."""

    def transcribe(self, wav_file: str) -> str:
        """Распознать короткий WAV-файл (до 25 сек)."""

    def transcribe_longform(
        self, wav_file: str, **kwargs: object
    ) -> list[dict[str, object]]:
        """Распознать длинный WAV-файл и вернуть сегменты."""


class STTClient:
    """Обёртка над моделью GigaAM для распознавания PCM16-байтов."""

    def __init__(self, model: GigaAMASRModel, device: str) -> None:
        """Инициализировать STT-клиент.

        :param model: загруженная модель GigaAM ASR (см. app.main).
        :param device: устройство модели ("cuda:0", "cuda:1", "cpu").
        """
        self._model = model
        self._device = device
        # Модель не потокобезопасна — сериализуем инференс.
        self._lock = threading.Lock()

    def transcribe(self, audio_bytes: bytes, sample_rate: int = 16000) -> str:
        """Распознать речь в PCM16-аудио и вернуть текст.

        :param audio_bytes: PCM 16-bit little-endian, mono.
        :param sample_rate: частота дискретизации входа (будет ресемплировано до 16 кГц).
        :return: распознанный текст или пустая строка (тишина/ошибка).
        """
        if not audio_bytes:
            return ""

        pcm = audio_bytes
        if sample_rate != converter.TARGET_SAMPLE_RATE:
            pcm = converter.resample(audio_bytes, sample_rate, converter.TARGET_SAMPLE_RATE)

        if not self._has_speech(pcm):
            return ""

        wav_bytes = converter.to_wav(pcm, converter.TARGET_SAMPLE_RATE)
        started = time.perf_counter()
        try:
            with self._lock:
                text = self._run_inference(wav_bytes)
        except Exception:
            logger.exception(
                "stt_inference_failed", model_name="gigaam", device=self._device
            )
            return ""

        logger.info(
            "stt_transcribed",
            model_name="gigaam",
            device=self._device,
            inference_time_ms=round((time.perf_counter() - started) * 1000, 1),
            text_length=len(text),
        )
        return text

    def _run_inference(self, wav_bytes: bytes) -> str:
        """Выполнить инференс через временный WAV-файл."""
        with tempfile.NamedTemporaryFile(suffix=".wav", prefix="speech_") as tmp:
            tmp.write(wav_bytes)
            tmp.flush()
            path = tmp.name

            samples = len(wav_bytes) // 2
            if samples > _LONGFORM_THRESHOLD_SAMPLES:
                segments = self._model.transcribe_longform(path)
                texts = [
                    str(seg.get("transcription", ""))
                    for seg in segments
                    if isinstance(seg.get("transcription"), str)
                ]
                return " ".join(part.strip() for part in texts if part.strip())
            return self._model.transcribe(path).strip()

    def _has_speech(self, pcm_bytes: bytes) -> bool:
        """Грубая проверка тишины по пиковой амплитуде (без VAD)."""
        samples = np.frombuffer(pcm_bytes, dtype=np.int16)
        if samples.size == 0:
            return False
        return bool(np.abs(samples).max() >= _SILENCE_PEAK)