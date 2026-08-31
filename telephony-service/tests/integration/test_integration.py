"""Интеграционные тесты с РЕАЛЬНЫМИ сервисами (требуют запущенных Asterisk
и/или speech-service). Запускаются только если сервисы доступны:

    # Asterisk:      docker compose up asterisk
    # speech-service: uvicorn app.main:app --port 8001 (в speech-service)
    pytest -m integration
"""

from __future__ import annotations

import os

import aiohttp
import pytest

from app.config import settings

pytestmark = pytest.mark.integration


async def _reachable(url: str) -> bool:
    try:
        timeout = aiohttp.ClientTimeout(total=2)
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=timeout):
                return True
    except Exception:  # noqa: BLE001
        return False


@pytest.mark.skipif(
    os.getenv("SKIP_ASTERSIK_IT", "") == "1",
    reason="SKIP_ASTERSIK_IT=1",
)
async def test_asterisk_ari_alive():
    base = settings.ASTERISK_ARI_URL.rstrip("/")
    if not await _reachable(f"{base}/ari/asterisk/info"):
        pytest.skip("Asterisk ARI недоступен")
    auth = aiohttp.BasicAuth(
        settings.ASTERISK_ARI_USERNAME, settings.ASTERISK_ARI_PASSWORD
    )
    async with aiohttp.ClientSession() as session:
        async with session.get(
            f"{base}/ari/asterisk/info", params={"only": "system"}, auth=auth
        ) as resp:
            assert resp.status == 200
            data = await resp.json()
            assert data.get("system", {}).get("version")


async def test_speech_service_alive():
    if not await _reachable(f"{settings.SPEECH_SERVICE_URL.rstrip('/')}/health"):
        pytest.skip("speech-service недоступен")
    async with aiohttp.ClientSession() as session:
        async with session.get(
            f"{settings.SPEECH_SERVICE_URL.rstrip('/')}/health"
        ) as resp:
            data = await resp.json()
            assert data["status"] == "ok"


async def test_speech_service_tts_roundtrip():
    if not await _reachable(f"{settings.SPEECH_SERVICE_URL.rstrip('/')}/health"):
        pytest.skip("speech-service недоступен")
    import shutil

    from app import wavutil
    from app.speech.client import SpeechServiceClient

    client = SpeechServiceClient(settings.SPEECH_SERVICE_URL)
    try:
        wav = await client.synthesize("Интеграционная проверка")
        # speech-service (edge-tts) возвращает MP3 — декодируем как продакшн-путь
        if not shutil.which("ffmpeg"):
            pytest.skip("ffmpeg недоступен на хосте")
        pcm = wavutil.decode_audio(wav, target_rate=8000)
        assert len(pcm) > 1000
    finally:
        await client.close()
