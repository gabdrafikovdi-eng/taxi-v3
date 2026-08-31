"""Health-сервер telephony-service (aiohttp).

* ``GET /health``  — общее состояние (ARI, speech-service, звонки);
* ``GET /readyz``  — готовность принимать звонки (200, если ARI подключён).
"""

from __future__ import annotations

from aiohttp import web

from app.ari.client import ARIClient
from app.calls.manager import CallManager
from app.config import Settings
from app.speech.client import SpeechServiceClient

VERSION = "0.1.0"


def build_health_app(
    manager: CallManager,
    ari: ARIClient,
    speech: SpeechServiceClient,
    settings: Settings,
) -> web.Application:
    app = web.Application()

    async def health(_request: web.Request) -> web.Response:
        ari_ok = ari.connected
        speech_ok = speech.last_health_ok
        degraded = not ari_ok or speech_ok is False
        return web.json_response(
            {
                "status": "ok" if not degraded else "degraded",
                "version": VERSION,
                "ari": {
                    "connected": ari_ok,
                    "url": settings.ASTERISK_ARI_URL,
                    "app": settings.ASTERISK_ARI_APP,
                },
                "speech_service": {
                    "url": settings.SPEECH_SERVICE_URL,
                    "last_check_ok": speech_ok,
                },
                "media": {
                    "format": settings.MEDIA_FORMAT,
                    "rtp_ports": f"{settings.RTP_SERVICE_PORT_START}-{settings.RTP_SERVICE_PORT_END}",
                },
                "backend_mode": settings.BACKEND_MODE,
                "calls": manager.stats(),
            }
        )

    async def readyz(_request: web.Request) -> web.Response:
        if not ari.connected:
            return web.json_response({"status": "not-ready", "ari": False}, status=503)
        return web.json_response({"status": "ready", "ari": True})

    app.router.add_get("/health", health)
    app.router.add_get("/readyz", readyz)
    return app


async def start_health_server(
    app: web.Application, host: str, port: int
) -> web.AppRunner:
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, host, port)
    await site.start()
    return runner


async def stop_health_server(runner: web.AppRunner) -> None:
    await runner.cleanup()
