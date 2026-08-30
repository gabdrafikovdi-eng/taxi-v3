"""Клиент TTS на базе edge-tts (Microsoft)."""

from __future__ import annotations

import edge_tts

from app.logging import get_logger

logger = get_logger(__name__)


class TTSClient:
    def __init__(self, default_voice: str = "ru-RU-DmitryNeural") -> None:
        # ru-RU-DmitryNeural (мужской) или ru-RU-SvetlanaNeural (женский)
        self._default_voice = default_voice

    async def synthesize(self, text: str, speaker: str | None = None) -> bytes:
        if not text or not text.strip():
            return b""

        voice = speaker or self._default_voice

        try:
            communicate = edge_tts.Communicate(text, voice)
            audio_bytes = b""

            # Собираем аудио-чанки асинхронно
            async for chunk in communicate.stream():
                if chunk["type"] == "audio":
                    audio_bytes += chunk["data"]

            return audio_bytes

        except Exception as e:
            logger.error(
                "tts_synthesis_failed", text=text[:50], voice=voice, error=str(e)
            )
            return b""
