"""Тесты RTP: parse/build, некорректные данные."""

from __future__ import annotations

import struct

from app.rtp import build_rtp, parse_rtp


def test_build_parse_roundtrip():
    payload = b"\x55" * 160
    packet = build_rtp(
        payload_type=0, sequence=1234, timestamp=1600, ssrc=42, payload=payload
    )
    parsed = parse_rtp(packet)
    assert parsed is not None
    assert parsed.payload_type == 0
    assert parsed.sequence == 1234
    assert parsed.timestamp == 1600
    assert parsed.ssrc == 42
    assert parsed.payload == payload
    assert parsed.marker is False


def test_build_parse_marker():
    packet = build_rtp(8, 5, 320, 1, b"abc", marker=True)
    parsed = parse_rtp(packet)
    assert parsed is not None
    assert parsed.payload_type == 8
    assert parsed.marker is True


def test_parse_too_short():
    assert parse_rtp(b"\x80") is None
    assert parse_rtp(b"") is None


def test_parse_bad_version():
    data = struct.pack("!BBHII", 0x40, 0, 0, 0, 0) + b"payload"
    assert parse_rtp(data) is None


def test_parse_padding():
    payload = b"abc"
    padded = payload + b"\x01"  # 1 байт padding
    packet = build_rtp(0, 1, 160, 1, padded)[:-1]  # уберём и пересоберём вручную
    # Соберём пакет с padding вручную: length включает padding
    import struct as s

    header = s.pack("!BBHII", 0xA0, 0x80, 1, 160, 1)  # 0xA0: v2 + padding bit
    data = header + padded
    parsed = parse_rtp(data)
    assert parsed is not None
    assert parsed.payload == payload
    _ = packet  # silence unused
