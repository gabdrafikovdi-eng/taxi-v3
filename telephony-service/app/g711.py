"""G.711 µ-law / A-law <-> PCM16 (pure python, без внешних зависимостей).

Реализация по reference-коду Sun Microsystems (g711.c). Кодеки используются
только для локальной обработки медиа (сегментация фраз, playback TTS);
сам конверт «на лету» НЕ выполняется: между Asterisk и telephony-service
аудио ходит в исходном G.711 (без преобразований), а speech-service сам
декодирует µ-law/A-law (см. его /api/v1/transcribe content-type).
"""

from __future__ import annotations

import math
import struct

__all__ = [
    "ulaw_decode",
    "ulaw_encode",
    "alaw_decode",
    "alaw_encode",
    "decode",
    "encode",
    "rms",
]

_BIAS = 0x84
_QUANT_MASK = 0x0F
_SEG_MASK = 0x70
_SEG_SHIFT = 4
_SIGN_BIT = 0x80

_SEG_UEND = (0x3F, 0x7F, 0xFF, 0x1FF, 0x3FF, 0x7FF, 0xFFF, 0x1FFF)
_SEG_AEND = (0x1F, 0x3F, 0x7F, 0xFF, 0x1FF, 0x3FF, 0x7FF, 0xFFF)


def _search(value: int, table: tuple[int, ...]) -> int:
    for i, bound in enumerate(table):
        if value <= bound:
            return i
    return len(table)


# --- µ-law -------------------------------------------------------------------

def _ulaw2linear(u: int) -> int:
    u ^= 0xFF
    t = ((u & _QUANT_MASK) << 3) + _BIAS
    t <<= (u & _SEG_MASK) >> _SEG_SHIFT
    return (_BIAS - t) if (u & _SIGN_BIT) else (t - _BIAS)


def _linear2ulaw(pcm: int) -> int:
    if pcm < 0:
        value, mask = -pcm, 0x7F
    else:
        value, mask = pcm, 0xFF
    value >>= 2
    seg = _search(value, _SEG_UEND)
    if seg >= 8:
        return 0x7F ^ mask
    uval = (seg << 4) | ((value >> (seg + 3)) & _QUANT_MASK)
    return uval ^ mask


# --- A-law -------------------------------------------------------------------

def _alaw2linear(a: int) -> int:
    a ^= 0x55
    t = (a & _QUANT_MASK) << 4
    seg = (a & _SEG_MASK) >> _SEG_SHIFT
    if seg == 0:
        t += 8
    elif seg == 1:
        t += 0x108
    else:
        t += 0x108
        t <<= seg - 1
    return t if (a & _SIGN_BIT) else -t


def _linear2alaw(pcm: int) -> int:
    if pcm >= 0:
        mask = 0xD5
    else:
        mask = 0x55
        pcm = -pcm - 1
    value = pcm >> 3
    seg = _search(value, _SEG_AEND)
    if seg >= 8:
        return 0x7F ^ mask
    aval = seg << _SEG_SHIFT
    if seg < 2:
        aval |= (value >> 4) & _QUANT_MASK
    else:
        aval |= (value >> (seg + 3)) & _QUANT_MASK
    return aval ^ mask


# --- Таблицы (ленивые) ---------------------------------------------------------

_ULAW_DECODE: list[int] | None = None
_ALAW_DECODE: list[int] | None = None
_ULAW_ENCODE: list[int] | None = None
_ALAW_ENCODE: list[int] | None = None


def _get_ulaw_decode() -> list[int]:
    global _ULAW_DECODE
    if _ULAW_DECODE is None:
        _ULAW_DECODE = [_ulaw2linear(i) for i in range(256)]
    return _ULAW_DECODE


def _get_alaw_decode() -> list[int]:
    global _ALAW_DECODE
    if _ALAW_DECODE is None:
        _ALAW_DECODE = [_alaw2linear(i) for i in range(256)]
    return _ALAW_DECODE


def _build_encode_table(decode_table: list[int]) -> list[int]:
    """Построить таблицу кодирования PCM16->G.711 ИЗ эталонного декодера.

    Для каждого int16 выбирается код, декодированное значение которого
    ближе всего к сэмплу (гарантирует round-trip ошибку не больше половины
    шага квантования сегмента и соответствие ITU-таблицам).
    """
    import bisect

    entries = sorted((decode_table[c], c) for c in range(256))
    decoded = [e[0] for e in entries]
    table: list[int] = []
    for pcm in range(-32768, 32768):
        i = bisect.bisect_left(decoded, pcm)
        if i >= 256:
            table.append(entries[255][1])
        elif i == 0:
            table.append(entries[0][1])
        else:
            d_lo, c_lo = entries[i - 1]
            d_hi, c_hi = entries[i]
            table.append(c_lo if abs(d_lo - pcm) <= abs(d_hi - pcm) else c_hi)
    return table


def _get_ulaw_encode() -> list[int]:
    """Таблица int16 -> код µ-law (65536 записей, строится один раз)."""
    global _ULAW_ENCODE
    if _ULAW_ENCODE is None:
        _ULAW_ENCODE = _build_encode_table(_get_ulaw_decode())
    return _ULAW_ENCODE


def _get_alaw_encode() -> list[int]:
    global _ALAW_ENCODE
    if _ALAW_ENCODE is None:
        _ALAW_ENCODE = _build_encode_table(_get_alaw_decode())
    return _ALAW_ENCODE


# --- Публичный API -------------------------------------------------------------


def ulaw_decode(data: bytes) -> bytes:
    """Декодировать G.711 µ-law в PCM16 (little-endian)."""
    table = _get_ulaw_decode()
    return struct.pack(f"<{len(data)}h", *(table[b] for b in data))


def alaw_decode(data: bytes) -> bytes:
    """Декодировать G.711 A-law в PCM16 (little-endian)."""
    table = _get_alaw_decode()
    return struct.pack(f"<{len(data)}h", *(table[b] for b in data))


def ulaw_encode(pcm: bytes) -> bytes:
    """Кодировать PCM16 (little-endian) в G.711 µ-law."""
    table = _get_ulaw_encode()
    n = len(pcm) // 2
    samples = struct.unpack(f"<{n}h", pcm[: n * 2])
    return bytes(table[s + 32768] for s in samples)


def alaw_encode(pcm: bytes) -> bytes:
    """Кодировать PCM16 (little-endian) в G.711 A-law."""
    table = _get_alaw_encode()
    n = len(pcm) // 2
    samples = struct.unpack(f"<{n}h", pcm[: n * 2])
    return bytes(table[s + 32768] for s in samples)


def decode(codec: str, data: bytes) -> bytes:
    if codec == "ulaw":
        return ulaw_decode(data)
    if codec == "alaw":
        return alaw_decode(data)
    raise ValueError(f"unsupported codec: {codec!r}")


def encode(codec: str, pcm: bytes) -> bytes:
    if codec == "ulaw":
        return ulaw_encode(pcm)
    if codec == "alaw":
        return alaw_encode(pcm)
    raise ValueError(f"unsupported codec: {codec!r}")


def rms(pcm: bytes) -> float:
    """RMS PCM16-сегмента (для энергетической детекции речи)."""
    n = len(pcm) // 2
    if n == 0:
        return 0.0
    samples = struct.unpack(f"<{n}h", pcm[: n * 2])
    acc = 0
    for s in samples:
        acc += s * s
    return math.sqrt(acc / n)
