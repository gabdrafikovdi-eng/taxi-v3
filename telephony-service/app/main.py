"""Точка входа telephony-service.

Компоненты: ARI-клиент (WebSocket + REST), CallManager (сессии звонков),
SpeechServiceClient (существующий speech-service), BackendClient (адаптер
backend), health-сервер. Graceful shutdown по SIGTERM/SIGINT.
"""

from __future__ import annotations

import asyncio
import contextlib
import signal

from aiohttp import web

from app.ari.client import ARIClient
from app.backend import build_backend
from app.calls.manager import CallManager
from app.config import settings
from app.health import build_health_app, start_health_server, stop_health_server
from app.logging import jinfo, setup_logging
from app.speech.client import SpeechServiceClient, periodic_health_check


async def run() -> None:
    setup_logging(settings.LOG_LEVEL)
    jinfo(
        "service_starting",
        ari_url=settings.ASTERISK_ARI_URL,
        ari_app=settings.ASTERISK_ARI_APP,
        speech_service_url=settings.SPEECH_SERVICE_URL,
        backend_mode=settings.BACKEND_MODE,
        backend_url=settings.BACKEND_URL,
        media_format=settings.MEDIA_FORMAT,
        rtp_ports=f"{settings.RTP_SERVICE_PORT_START}-{settings.RTP_SERVICE_PORT_END}",
    )

    backend = build_backend(settings)
    speech = SpeechServiceClient(
        base_url=settings.SPEECH_SERVICE_URL,
        stt_timeout=settings.STT_TIMEOUT_SEC,
        tts_timeout=settings.TTS_TIMEOUT_SEC,
    )
    # Делегат нужен, т.к. ARIClient требует обработчик событий до создания
    # CallManager, а CallManager — до ARIClient (циклическая зависимость DI).
    holder: dict[str, CallManager] = {}

    async def on_event(event: dict) -> None:
        await holder["manager"].handle_event(event)

    ari = ARIClient(settings, on_event=on_event)
    manager = CallManager(settings, ari, speech, backend)
    holder["manager"] = manager

    # Health-сервер стартует сразу: оркестратор виден compose healthcheck,
    # даже если Asterisk ещё не поднялся (reconnect в ARI-клиенте)
    runner = await start_health_server(
        build_health_app(manager, ari, speech, settings),
        settings.HEALTH_HOST,
        settings.HEALTH_PORT,
    )
    jinfo("health_server_started", host=settings.HEALTH_HOST, port=settings.HEALTH_PORT)

    await ari.start()
    speech_health_task = asyncio.create_task(periodic_health_check(speech, 30.0))

    stop = asyncio.Event()
    loop = asyncio.get_running_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        with contextlib.suppress(NotImplementedError):
            loop.add_signal_handler(sig, stop.set)

    jinfo("service_started")
    await stop.wait()

    jinfo("service_stopping")
    speech_health_task.cancel()
    with contextlib.suppress(asyncio.CancelledError):
        await speech_health_task
    await manager.shutdown()
    await ari.close()
    await speech.close()
    close_backend = getattr(backend, "close", None)
    if callable(close_backend):
        with contextlib.suppress(Exception):
            await close_backend()
    await stop_health_server(runner)
    jinfo("service_stopped")


def main() -> None:
    asyncio.run(run())


if __name__ == "__main__":
    main()
