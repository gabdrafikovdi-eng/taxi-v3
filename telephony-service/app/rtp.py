"""Минимальный разбор/сборка RTP-пакетов (RFC 3550) для external media."""

from __future__ import annotations

import struct
from dataclasses import dataclass

RTP_HEADER_LEN = 12


@dataclass(slots=True)
class RtpPacket:
    payload_type: int
    marker: bool
    sequence: int
    timestamp: int
    ssrc: int
    payload: bytes


def parse_rtp(data: bytes) -> RtpPacket | None:
    """Разобрать RTP-пакет. Возвращает None при некорректных данных."""
    if len(data) < RTP_HEADER_LEN:
        return None
    first = data[0]
    if first >> 6 != 2:  # version
        return None
    csrc_count = first & 0x0F
    header_len = RTP_HEADER_LEN + csrc_count * 4
    if len(data) < header_len:
        return None
    second = data[1]
    sequence, timestamp, ssrc = struct.unpack("!HII", data[2:12])
    payload = data[header_len:]
    if first & 0x20:  # padding
        if not payload:
            return None
        pad = payload[-1]
        if pad == 0 or pad > len(payload):
            return None
        payload = payload[:-pad]
    return RtpPacket(
        payload_type=second & 0x7F,
        marker=bool(second & 0x80),
        sequence=sequence,
        timestamp=timestamp,
        ssrc=ssrc,
        payload=payload,
    )


def build_rtp(
    payload_type: int,
    sequence: int,
    timestamp: int,
    ssrc: int,
    payload: bytes,
    marker: bool = False,
) -> bytes:
    """Собрать RTP-пакет (version=2, без CSRC/padding/extensions)."""
    first = 0x80  # version 2
    second = (0x80 if marker else 0) | (payload_type & 0x7F)
    return (
        struct.pack(
            "!BBHII",
            first,
            second,
            sequence & 0xFFFF,
            timestamp & 0xFFFFFFFF,
            ssrc,
        )
        + payload
    )
