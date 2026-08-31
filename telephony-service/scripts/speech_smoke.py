"""Проверка speech-service (smoke test, сервис НЕ изменяется).

Usage:
    python scripts/speech_smoke.py "Привет, как дела?"   # TTS → out.wav
    python scripts/speech_smoke.py --stt file.ulaw       # STT файла G.711
"""

from __future__ import annotations

import asyncio
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.config import settings  # noqa: E402
from app.speech.client import SpeechServiceClient  # noqa: E402


async def main() -> None:
    args = sys.argv[1:]
    client = SpeechServiceClient(
        base_url=settings.SPEECH_SERVICE_URL,
        stt_timeout=settings.STT_TIMEOUT_SEC,
        tts_timeout=settings.TTS_TIMEOUT_SEC,
    )
    try:
        health = await client.health()
        print(f"health: {health}")
        if health is None:
            print("speech-service недоступен")
            sys.exit(1)
        if args and args[0] == "--stt":
            path = args[1]
            with open(path, "rb") as f:  # noqa: PTH123
                audio = f.read()
            text = await client.transcribe(
                audio, settings.stt_content_type
            )
            print(f"STT text: {text!r}")
        else:
            text = args[0] if args else "Проверка синтеза речи."
            wav = await client.synthesize(text)
            with open("out.wav", "wb") as f:  # noqa: PTH123
                f.write(wav)
            print(f"TTS OK: {len(wav)} bytes -> out.wav")
    finally:
        await client.close()


if __name__ == "__main__":
    asyncio.run(main())
