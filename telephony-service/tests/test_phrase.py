"""Тесты PhraseDetector: сегментация фраз на G.711-чанках."""

from __future__ import annotations

import math
import struct

from app import g711
from app.phrase import PhraseDetector

CHUNK = 160  # байт G.711 = 20 мс


def _loud_chunk() -> bytes:
    """Синусоида амплитудой 10000 (RMS ~7070 > порога 900)."""
    samples = [int(10000 * math.sin(2 * math.pi * 440 * i / 8000)) for i in range(160)]
    return g711.ulaw_encode(struct.pack("<160h", *samples))


def _silence_chunk() -> bytes:
    return g711.ulaw_encode(struct.pack("<160h", *([0] * 160)))


def _detector(**overrides) -> PhraseDetector:
    params = dict(
        codec="ulaw",
        speech_threshold=900.0,
        silence_ms=300,
        min_speech_ms=100,
        max_utterance_ms=5000,
        preroll_ms=60,
    )
    params.update(overrides)
    return PhraseDetector(**params)


def test_silence_only_emits_nothing():
    detector = _detector()
    for _ in range(50):
        assert detector.feed(_silence_chunk()) is None


def test_short_noise_is_discarded():
    detector = _detector()
    for _ in range(50):
        detector.feed(_silence_chunk())
    # 3 чанка речи (60 мс) < min_speech_ms=100, затем тишина → None
    for _ in range(3):
        assert detector.feed(_loud_chunk()) is None
    for _ in range(20):
        assert detector.feed(_silence_chunk()) is None


def test_phrase_emitted_after_silence():
    detector = _detector()
    for _ in range(10):
        detector.feed(_silence_chunk())
    for _ in range(10):  # 200 мс речи
        assert detector.feed(_loud_chunk()) is None
    phrase = None
    for _ in range(20):
        result = detector.feed(_silence_chunk())
        if result is not None:
            phrase = result
            break
    assert phrase is not None
    # Фраза включает preroll (60 мс = 3 чанка) + 10 чанков речи + тишину
    assert len(phrase) > 13 * CHUNK
    assert not detector.capturing


def test_max_utterance_forces_emit():
    detector = _detector(max_utterance_ms=1000)
    emitted = None
    for _ in range(80):  # 1.6 с непрерывной речи при лимите 1.0 с
        result = detector.feed(_loud_chunk())
        if result is not None:
            emitted = result
            break
    assert emitted is not None
    assert len(emitted) >= 50 * CHUNK


def test_flush_returns_ongoing_phrase():
    detector = _detector()
    for _ in range(5):
        detector.feed(_silence_chunk())
    for _ in range(10):
        detector.feed(_loud_chunk())
    phrase = detector.flush()
    assert phrase is not None
    assert len(phrase) >= 10 * CHUNK


def test_reset_clears_state():
    detector = _detector()
    for _ in range(5):
        detector.feed(_silence_chunk())
    for _ in range(10):
        detector.feed(_loud_chunk())
    assert detector.capturing
    detector.reset()
    assert not detector.capturing
    assert detector.flush() is None


def test_invalid_codec():
    try:
        PhraseDetector(codec="opus")
    except ValueError:
        pass
    else:  # pragma: no cover
        raise AssertionError("ValueError expected")
