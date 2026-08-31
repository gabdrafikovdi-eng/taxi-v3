"""Тесты WAV-утилит: parse, mixdown, resample, float32."""

from __future__ import annotations

import struct

import pytest

from app import wavutil


def test_pcm16_wav_roundtrip():
    pcm = struct.pack("<8h", *range(-4, 4))
    wav = wavutil.pcm16_to_wav(pcm, 8000)
    parsed_pcm, rate = wavutil.parse_wav(wav)
    assert rate == 8000
    assert parsed_pcm == pcm


def test_parse_stereo_mixdown():
    stereo = struct.pack("<4h", 1000, 3000, -1000, -3000)
    wav = wavutil.pcm16_to_wav(stereo, 16000, channels=2)
    mono, rate = wavutil.parse_wav(wav)
    assert rate == 16000
    samples = struct.unpack("<2h", mono)
    assert samples == (2000, -2000)


def test_parse_float32():
    floats = struct.pack("<2f", 0.5, -0.5)
    header = b"RIFF" + struct.pack(
        "<I4s4sIHHIIHH4s",
        36 + len(floats),
        b"WAVE",
        b"fmt ",
        16,
        3,  # IEEE float
        1,
        8000,
        32000,
        4,
        32,
        b"data",
    ) + struct.pack("<I", len(floats))
    pcm, rate = wavutil.parse_wav(header + floats)
    assert rate == 8000
    assert struct.unpack("<2h", pcm) == (16383, -16383)


def test_parse_not_a_wav():
    with pytest.raises(wavutil.WavParseError):
        wavutil.parse_wav(b"ID3" + b"\x00" * 100)


def test_resample_up_and_down():
    pcm = struct.pack("<4h", 0, 1000, 2000, 3000)
    up = wavutil.resample_linear(pcm, 8000, 16000)
    samples_up = struct.unpack(f"<{len(up) // 2}h", up)
    assert len(samples_up) == 8
    assert samples_up[0] == 0
    assert abs(samples_up[2] - 1000) <= 1  # интерполяция середины
    down = wavutil.resample_linear(up, 16000, 8000)
    samples_down = struct.unpack(f"<{len(down) // 2}h", down)
    assert len(samples_down) == 4
    assert samples_down == (0, 1000, 2000, 3000)


def test_resample_same_rate_noop():
    pcm = struct.pack("<2h", 5, -5)
    assert wavutil.resample_linear(pcm, 8000, 8000) == pcm
