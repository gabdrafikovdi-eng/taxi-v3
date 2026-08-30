"""VAD (Voice Activity Detection) на базе Silero VAD.

Всё выполняется на CPU, модель загружается один раз (см. app.main).
Используется для:
- отсечения тишины перед STT;
- детекции конца фразы в потоковом режиме (transcribe/stream).
"""

from __future__ import annotations

import numpy as np
import torch
from torch import Tensor

from app.audio import converter
from app.logging import get_logger

logger = get_logger(__name__)

VAD_SAMPLE_RATE = 16000
# Silero VAD работает окнами по 512 сэмплов (32 мс @ 16 кГц).
_VAD_WINDOW_SAMPLES = 512
# Порог "вероятность речи", при котором окно считается речью.
_DEFAULT_THRESHOLD = 0.5


class VAD:
    """Обёртка над моделью Silero VAD для проверки речи и конца фразы."""

    def __init__(self, model: object, threshold: float = _DEFAULT_THRESHOLD) -> None:
        """Инициализировать VAD.

        :param model: загруженная модель Silero VAD (torch.jit).
        :param threshold: порог вероятности речи (0.0 - 1.0).
        """
        self._model = model
        self._threshold = threshold

    def _speech_prob(self, samples: np.ndarray) -> float:
        """Вернуть вероятность речи для одного окна 512 сэмплов."""
        # Копия обязательна: torch.from_numpy на read-only массиве даёт
        # undefined behavior (Silero VAD выполняет in-place операции).
        writable = np.ascontiguousarray(samples, dtype=np.float32)
        tensor = torch.from_numpy(writable.copy()).div(32768.0)
        with torch.inference_mode():
            prob = self._model(tensor, VAD_SAMPLE_RATE)
        if isinstance(prob, Tensor):
            return float(prob.reshape(-1)[-1])
        return float(prob)

    def _reset_state(self) -> None:
        """Сбросить внутреннее состояние аннотатора Silero VAD перед анализом."""
        reset = getattr(self._model, "reset_states", None)
        if callable(reset):
            reset()

    def is_speech(self, audio_chunk: bytes, sample_rate: int = VAD_SAMPLE_RATE) -> bool:
        """Есть ли речь хотя бы в одном окне переданного PCM16-чанка.

        :param audio_chunk: PCM 16-bit little-endian.
        :param sample_rate: частота дискретизации входного чанка.
        :return: True, если в аудио есть речь.
        """
        if not audio_chunk:
            return False

        pcm = audio_chunk
        if sample_rate != VAD_SAMPLE_RATE:
            pcm = converter.resample(audio_chunk, sample_rate, VAD_SAMPLE_RATE)

        samples = np.frombuffer(pcm, dtype=np.int16)
        if samples.size == 0:
            return False
        if samples.size < _VAD_WINDOW_SAMPLES:
            samples = np.pad(
                samples, (0, _VAD_WINDOW_SAMPLES - samples.size), mode="constant"
            )

        self._reset_state()
        for start in range(0, samples.size, _VAD_WINDOW_SAMPLES):
            window = samples[start : start + _VAD_WINDOW_SAMPLES]
            if window.size < _VAD_WINDOW_SAMPLES:
                window = np.pad(
                    window,
                    (0, _VAD_WINDOW_SAMPLES - window.size),
                    mode="constant",
                )
            if self._speech_prob(window) >= self._threshold:
                return True
        return False

    def detect_end_of_speech(
        self,
        buffer: bytearray,
        chunk: bytes,
        sample_rate: int = VAD_SAMPLE_RATE,
        silence_ms: int = 800,
    ) -> bool:
        """Определить конец фразы по хвосту накопленного аудио.

        Аудио накапливается в ``buffer`` (перед вызовом) и расширяется
        ``chunk``. Если последние ``silence_ms`` целиком тишина, фраза
        считается завершённой.

        :param buffer: накопительный bytearray (мутируется).
        :param chunk: новый PCM16-чанк.
        :param sample_rate: частота дискретизации чанка.
        :param silence_ms: требуемая длительность тишины для конца фразы.
        :return: True, если хвост фразы тихий -> фраза завершена.
        """
        buffer.extend(chunk)

        window_bytes = int(silence_ms / 1000.0 * VAD_SAMPLE_RATE * 2)
        # Для детекции важен только хвост — ограничиваем память.
        if len(buffer) > window_bytes * 2:
            del buffer[: len(buffer) - window_bytes]

        if len(buffer) < window_bytes:
            return False

        tail = bytes(buffer[-window_bytes:])
        return not self.is_speech(tail, VAD_SAMPLE_RATE)