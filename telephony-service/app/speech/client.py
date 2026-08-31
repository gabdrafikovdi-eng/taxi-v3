"""Клиент существующего speech-service (STT/TTS). Сервис НЕ изменяется.

Используемые endpoints (см. speech-service/app/main.py):
* ``POST /api/v1/transcribe`` — multipart-поле ``audio``; содержимое
  декодируется по content-type: 'mulaw' → G.711 µ-law 8 кГц, 'alaw' → A-law,
  иначе WAV. Ответ: ``{"text", "duration_ms", "sample_rate", ...}``.
* ``POST /api/v1/synthesize`` — JSON ``{"text", "speaker"?}`` → ``audio/wav``.
* ``GET /health`` — статус сервиса.

Телефонное аудио пересылается в исходном G.711 (без перекодирования):
µ-law/A-law принимается speech-service напрямую.
"""

from __future__ import annotations

import asyncio
import contextlib

import aiohttp

from app.logging import jinfo, jwarning


class SpeechError(RuntimeError):
    """Ошибка обращения к speech-service (timeout/недоступен/плохой ответ)."""


class SpeechServiceClient:
    def __init__(
        self,
        base_url: str,
        stt_timeout: float = 10.0,
        tts_timeout: float = 20.0,
        retries: int = 1,
        retry_backoff_sec: float = 0.5,
    ) -> None:
        self._base_url = base_url.rstrip("/")
        self._stt_timeout = stt_timeout
        self._tts_timeout = tts_timeout
        self._retries = max(0, retries)
        self._retry_backoff = retry_backoff_sec
        self._session: aiohttp.ClientSession | None = None
        self._last_health_ok: bool | None = None

    async def close(self) -> None:
        if self._session:
            await self._session.close()
            self._session = None

    def _ensure_session(self) -> aiohttp.ClientSession:
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession()
        return self._session

    @property
    def last_health_ok(self) -> bool | None:
        return self._last_health_ok

    # --------------------------------------------------------------------- STT

    async def transcribe(self, audio: bytes, content_type: str = "audio/x-mulaw") -> str:
        """Распознать G.711/WAV-аудио. Вернуть текст (может быть пустым)."""
        if not audio:
            return ""
        url = f"{self._base_url}/api/v1/transcribe"
        timeout = aiohttp.ClientTimeout(total=self._stt_timeout)
        last_error: SpeechError | None = None

        for attempt in range(self._retries + 1):
            form = aiohttp.FormData()
            form.add_field(
                "audio", audio, filename="audio.g711", content_type=content_type
            )
            try:
                async with self._ensure_session().post(
                    url, data=form, timeout=timeout
                ) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        return str(data.get("text", ""))
                    body = (await resp.text())[:200]
                    # 4xx (кроме 429) — проблема запроса, повторы бессмысленны
                    if 400 <= resp.status < 500 and resp.status != 429:
                        raise SpeechError(f"STT bad request {resp.status}: {body}")
                    last_error = SpeechError(f"STT failed {resp.status}: {body}")
            except SpeechError:
                raise
            except (asyncio.TimeoutError, aiohttp.ClientError) as exc:
                last_error = SpeechError(f"STT unavailable: {exc!r}")
            jwarning(
                "speech_stt_attempt_failed", attempt=attempt + 1, error=str(last_error)
            )
            await asyncio.sleep(self._retry_backoff * (attempt + 1))
        raise last_error or SpeechError("STT failed")

    # --------------------------------------------------------------------- TTS

    async def synthesize(self, text: str, speaker: str | None = None) -> bytes:
        """Синтезировать речь. Вернуть WAV-байты."""
        if not text.strip():
            raise SpeechError("TTS empty text")
        url = f"{self._base_url}/api/v1/synthesize"
        payload: dict = {"text": text}
        if speaker:
            payload["speaker"] = speaker
        timeout = aiohttp.ClientTimeout(total=self._tts_timeout)
        last_error: SpeechError | None = None

        for attempt in range(self._retries + 1):
            try:
                async with self._ensure_session().post(
                    url, json=payload, timeout=timeout
                ) as resp:
                    if resp.status == 200:
                        return await resp.read()
                    body = (await resp.text())[:200]
                    if 400 <= resp.status < 500 and resp.status != 429:
                        raise SpeechError(f"TTS bad request {resp.status}: {body}")
                    last_error = SpeechError(f"TTS failed {resp.status}: {body}")
            except SpeechError:
                raise
            except (asyncio.TimeoutError, aiohttp.ClientError) as exc:
                last_error = SpeechError(f"TTS unavailable: {exc!r}")
            jwarning(
                "speech_tts_attempt_failed", attempt=attempt + 1, error=str(last_error)
            )
            await asyncio.sleep(self._retry_backoff * (attempt + 1))
        raise last_error or SpeechError("TTS failed")

    # ------------------------------------------------------------------ health

    async def health(self) -> dict | None:
        """Проверить доступность speech-service. None при недоступности."""
        try:
            timeout = aiohttp.ClientTimeout(total=3)
            async with self._ensure_session().get(
                f"{self._base_url}/health", timeout=timeout
            ) as resp:
                if resp.status != 200:
                    self._last_health_ok = False
                    return None
                data = await resp.json()
                self._last_health_ok = True
                return data if isinstance(data, dict) else {}
        except (asyncio.TimeoutError, aiohttp.ClientError) as exc:
            jwarning("speech_health_check_failed", error=str(exc))
            self._last_health_ok = False
            return None


async def periodic_health_check(
    client: SpeechServiceClient, interval_sec: float = 30.0
) -> None:
    """Фоновая проверка доступности speech-service (для health-сервера)."""
    while True:
        result = await client.health()
        if result is not None:
            jinfo("speech_service_health_ok", stt=result.get("stt_loaded"))
        await asyncio.sleep(interval_sec)


async def close_quietly(client: SpeechServiceClient) -> None:
    with contextlib.suppress(Exception):
        await client.close()
