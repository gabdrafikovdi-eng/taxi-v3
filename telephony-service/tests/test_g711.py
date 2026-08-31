"""Тесты G.711 кодека: контрольные точки + round-trip точность + RMS."""

from __future__ import annotations

import math
import random
import struct

from app import g711


def test_ulaw_decode_known_points():
    # Классические значения (Sun g711.c)
    assert g711.ulaw_decode(b"\xff") == struct.pack("<h", 0)
    assert g711.ulaw_decode(b"\x7f") == struct.pack("<h", 0)
    assert g711.ulaw_decode(b"\x00") == struct.pack("<h", -32124)
    assert g711.ulaw_decode(b"\x80") == struct.pack("<h", 32124)


def test_ulaw_roundtrip_accuracy():
    random.seed(42)
    samples = [random.randint(-32768, 32767) for _ in range(20000)]
    for s in samples:
        encoded = g711.ulaw_encode(struct.pack("<h", s))
        decoded = struct.unpack("<h", g711.ulaw_decode(encoded))[0]
        # Квантование µ-law: максимум 512 в верхнем сегменте (шаг 1024);
        # на краях диапазона (|s| > 32124) — до 644 из-за BIAS-асимметрии
        assert abs(decoded - s) <= 700, (s, decoded)


def test_ulaw_roundtrip_silent_and_clip():
    for s in (0, 1, -1):
        encoded = g711.ulaw_encode(struct.pack("<h", s))
        decoded = struct.unpack("<h", g711.ulaw_decode(encoded))[0]
        assert abs(decoded - s) <= 8, (s, decoded)


def test_ulaw_roundtrip_fullscale_within_quantization():
    for s in (32767, -32768):
        encoded = g711.ulaw_encode(struct.pack("<h", s))
        decoded = struct.unpack("<h", g711.ulaw_decode(encoded))[0]
        assert abs(decoded - s) <= 700, (s, decoded)


def test_alaw_roundtrip_accuracy():
    random.seed(7)
    samples = [random.randint(-32768, 32767) for _ in range(20000)]
    for s in samples:
        encoded = g711.alaw_encode(struct.pack("<h", s))
        decoded = struct.unpack("<h", g711.alaw_decode(encoded))[0]
        # A-law: шаг верхнего сегмента 1024 (err <= 512), края — до 512+?
        assert abs(decoded - s) <= 600, (s, decoded)


def test_batch_encode_decode_consistency():
    n = 1000
    pcm = struct.pack(f"<{n}h", *[i * 31 % 16000 - 8000 for i in range(n)])
    ulaw = g711.ulaw_encode(pcm)
    assert len(ulaw) == n
    assert len(g711.ulaw_decode(ulaw)) == n * 2
    alaw = g711.alaw_encode(pcm)
    assert len(alaw) == n


def test_rms():
    assert g711.rms(b"") == 0.0
    silence = struct.pack("<4h", 0, 0, 0, 0)
    assert g711.rms(silence) == 0.0
    tone = struct.pack("<4h", 1000, -1000, 1000, -1000)
    assert math.isclose(g711.rms(tone), 1000.0)


def test_unsupported_codec_raises():
    try:
        g711.decode("opus", b"\x00")
    except ValueError:
        pass
    else:  # pragma: no cover
        raise AssertionError("ValueError expected")
