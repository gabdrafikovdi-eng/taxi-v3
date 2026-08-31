"""Конвертация аудиоформатов: G.711 (mulaw/alaw) <-> PCM 16-bit 16kHz, WAV."""

from __future__ import annotations

import io

import numpy as np
import soundfile as sf
import torchaudio
import torch

TARGET_SAMPLE_RATE = 16000


def mulaw_to_pcm16(audio_bytes: bytes, sample_rate: int = 8000) -> tuple[bytes, int]:
    """Декодировать G.711 µ-law в PCM16 через libsndfile (100% стандарт).

    :return: ``(pcm_bytes, sample_rate)``.
    """
    if not audio_bytes:
        return b"", sample_rate
    with io.BytesIO(audio_bytes) as f:
        # format='RAW' говорит soundfile не искать WAV-заголовок
        data, _ = sf.read(
            f,
            dtype="int16",
            format="RAW",
            channels=1,
            samplerate=sample_rate,
            subtype="ULAW",
        )
    return data.tobytes(), sample_rate


def alaw_to_pcm16(audio_bytes: bytes, sample_rate: int = 8000) -> tuple[bytes, int]:
    """Декодировать G.711 A-law в PCM16 через libsndfile (100% стандарт).

    :return: ``(pcm_bytes, sample_rate)``.
    """
    if not audio_bytes:
        return b"", sample_rate
    with io.BytesIO(audio_bytes) as f:
        data, _ = sf.read(
            f,
            dtype="int16",
            format="RAW",
            channels=1,
            samplerate=sample_rate,
            subtype="ALAW",
        )
    return data.tobytes(), sample_rate


def resample(audio_bytes: bytes, from_rate: int, to_rate: int) -> bytes:
    """Ресемплировать PCM16-аудио через torchaudio (Sinc-интерполяция, высокое качество)."""
    if not audio_bytes or from_rate == to_rate:
        return audio_bytes

    # Преобразуем байты в тензор float32 (torchaudio требует float).
    # .astype() создаёт новый записываемый массив — избегаем предупреждения
    # PyTorch про read-only буфер.
    samples = np.frombuffer(audio_bytes, dtype=np.int16).astype(np.float32)
    samples = torch.from_numpy(samples)
    # Добавляем размерность канала: (samples,) -> (1, samples)
    samples = samples.unsqueeze(0)

    # Ресемплинг
    resampler = torchaudio.transforms.Resample(orig_freq=from_rate, new_freq=to_rate)
    resampled = resampler(samples)

    # Обрезаем пики и возвращаем в int16 байты
    resampled = torch.clamp(resampled, -32768.0, 32767.0).short()
    return resampled.squeeze(0).numpy().tobytes()


def to_wav(pcm_bytes: bytes, sample_rate: int, channels: int = 1) -> bytes:
    """Упаковать PCM16-байты в WAV файл."""
    if not pcm_bytes:
        raise ValueError("empty PCM data cannot be encoded to WAV")

    samples = np.frombuffer(pcm_bytes, dtype=np.int16).reshape(-1, channels)
    buffer = io.BytesIO()
    with sf.SoundFile(
        buffer,
        mode="w",
        samplerate=sample_rate,
        channels=channels,
        format="WAV",
        subtype="PCM_16",
    ) as wav_file:
        wav_file.write(samples)
    return buffer.getvalue()


def duration_ms(pcm_bytes: bytes, sample_rate: int = TARGET_SAMPLE_RATE) -> int:
    """Длительность PCM16-аудио в миллисекундах."""
    if not pcm_bytes:
        return 0
    return int((len(pcm_bytes) // 2) / sample_rate * 1000)
