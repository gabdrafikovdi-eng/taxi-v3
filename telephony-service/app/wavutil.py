"""Минимальная работа с WAV (PCM16) без внешних зависимостей.

Используется ТОЛЬКО для TTS-playback: speech-service возвращает WAV
(PCM16 или float32, любой sample rate / число каналов) — здесь он
приводится к моно PCM16 и ресемплируется к 8 кГц для кодирования в G.711.
"""

from __future__ import annotations

import struct


class WavParseError(ValueError):
    """Некорректный/неподдерживаемый WAV."""


def parse_wav(data: bytes) -> tuple[bytes, int]:
    """Разобрать WAV. Вернуть ``(pcm16_mono_bytes, sample_rate)``.

    Поддержка: PCM16 (format 1, bits 16) и IEEE float32 (format 3, bits 32).
    Многоканальное аудио микшируется в моно (усреднение с насыщением).
    """
    if len(data) < 12 or data[0:4] != b"RIFF" or data[8:12] != b"WAVE":
        raise WavParseError("not a RIFF/WAVE file")

    pos = 12
    audio_format: int | None = None
    channels = 1
    sample_rate = 8000
    bits = 16
    raw: bytes | None = None

    while pos + 8 <= len(data):
        chunk_id = data[pos : pos + 4]
        (chunk_size,) = struct.unpack("<I", data[pos + 4 : pos + 8])
        body = data[pos + 8 : pos + 8 + chunk_size]
        if chunk_id == b"fmt ":
            if chunk_size < 16:
                raise WavParseError("fmt chunk too small")
            audio_format, channels, sample_rate = struct.unpack(
                "<HHI", body[0:8]
            )
            (bits,) = struct.unpack("<H", body[14:16])
        elif chunk_id == b"data":
            raw = body
        pos += 8 + chunk_size + (chunk_size & 1)

    if raw is None:
        raise WavParseError("no data chunk")
    if audio_format == 1 and bits == 16:
        return _mono_or_stereo(raw, channels), sample_rate
    if audio_format == 3 and bits == 32:
        n = len(raw) // 4
        floats = struct.unpack(f"<{n}f", raw[: n * 4])
        pcm = b"".join(
            struct.pack("<h", _clamp16(v * 32767.0)) for v in floats
        )
        return _mono_or_stereo(pcm, channels), sample_rate
    raise WavParseError(f"unsupported WAV format={audio_format} bits={bits}")


def _clamp16(value: float) -> int:
    if value > 32767:
        return 32767
    if value < -32768:
        return -32768
    return int(value)


def _mono_or_stereo(pcm16: bytes, channels: int) -> bytes:
    if channels <= 1:
        return pcm16
    return _mixdown_to_mono(pcm16)


def _mixdown_to_mono(pcm16: bytes) -> bytes:
    n = len(pcm16) // 2
    if n == 0:
        return b""
    samples = struct.unpack(f"<{n}h", pcm16[: n * 2])
    mono = [
        _clamp16((samples[i] + samples[i + 1]) / 2.0)
        for i in range(0, n - 1, 2)
    ]
    if n % 2 == 1:
        mono.append(samples[n - 1])
    return struct.pack(f"<{len(mono)}h", *mono)


def resample_linear(pcm: bytes, from_rate: int, to_rate: int) -> bytes:
    """Ресемплинг PCM16-моно линейной интерполяцией (8/16/24/48 кГц -> 8 кГц)."""
    if from_rate == to_rate or not pcm:
        return pcm
    n = len(pcm) // 2
    if n < 2:
        return pcm
    samples = struct.unpack(f"<{n}h", pcm[: n * 2])
    ratio = from_rate / to_rate
    out_len = max(1, int(n / ratio))
    out: list[int] = []
    for i in range(out_len):
        pos = i * ratio
        i0 = int(pos)
        if i0 >= n - 1:
            out.append(samples[n - 1])
            continue
        frac = pos - i0
        s0, s1 = samples[i0], samples[i0 + 1]
        out.append(_clamp16(s0 + (s1 - s0) * frac))
    return struct.pack(f"<{len(out)}h", *out)


def pcm16_to_wav(pcm: bytes, sample_rate: int, channels: int = 1) -> bytes:
    """Упаковать PCM16 в WAV (для тестов/отладки)."""
    if len(pcm) % 2 != 0:
        pcm += b"\x00"
    byte_rate = sample_rate * channels * 2
    block_align = channels * 2
    header = b"RIFF" + struct.pack(
        "<I4s4sIHHIIHH4s",
        36 + len(pcm),
        b"WAVE",
        b"fmt ",
        16,
        1,
        channels,
        sample_rate,
        byte_rate,
        block_align,
        16,
        b"data",
    ) + struct.pack("<I", len(pcm))
    return header + pcm


# --------------------------------------------------------------------------
# Универсальное декодирование (WAV / MP3 / OGG) в PCM16-моно заданной частоты.
# speech-service /synthesize возвращает сырой поток edge-tts — это MP3
# (content-type при этом audio/wav), поэтому MP3 — штатный случай.
# --------------------------------------------------------------------------

def decode_audio(data: bytes, target_rate: int = 8000) -> bytes:
    """Декодировать аудио (WAV/MP3/OGG) в PCM16-моно @ target_rate.

    WAV обрабатывается встроенным парсером, остальное — через ffmpeg
    (должен быть в контейнере; см. Dockerfile).
    """
    if not data:
        raise WavParseError("empty audio payload")
    if data[:4] == b"RIFF" and data[8:12] == b"WAVE":
        pcm, rate = parse_wav(data)
    elif _is_ffmpeg_supported(data):
        pcm, rate = _ffmpeg_decode(data)
    else:
        raise WavParseError(
            f"unsupported audio format: {data[:12].hex()}"
        )
    if rate != target_rate:
        pcm = resample_linear(pcm, rate, target_rate)
    return pcm


def _is_ffmpeg_supported(data: bytes) -> bool:
    if data[:3] == b"ID3":
        return True
    if len(data) >= 2 and data[0] == 0xFF and (data[1] & 0xE0) == 0xE0:
        return True  # MPEG audio frame sync (mp3)
    if data[:4] == b"OggS" or data[:4] == b"fLaC":
        return True
    return False


def _ffmpeg_decode(data: bytes) -> tuple[bytes, int]:
    import shutil
    import subprocess

    ffmpeg = shutil.which("ffmpeg")
    if ffmpeg is None:
        raise WavParseError("ffmpeg not installed — cannot decode audio")
    try:
        result = subprocess.run(
            [
                ffmpeg, "-hide_banner", "-loglevel", "error",
                "-i", "pipe:0",
                "-f", "s16le", "-ac", "1", "-ar", "8000",
                "pipe:1",
            ],
            input=data,
            capture_output=True,
            timeout=30,
            check=True,
        )
    except subprocess.CalledProcessError as exc:
        raise WavParseError(f"ffmpeg decode failed: {exc.stderr[:200]!r}") from exc
    except subprocess.TimeoutExpired as exc:
        raise WavParseError("ffmpeg decode timeout") from exc
    return result.stdout, 8000
