"""Пакет STT: распознавание речи (GigaAM) + VAD (Silero)."""

from app.stt.client import STTClient
from app.stt.vad import VAD

__all__ = ["VAD", "STTClient"]