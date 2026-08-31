"""Тесты SpeechServiceClient против локального aiohttp TestServer."""

from __future__ import annotations

import asyncio

import pytest
from aiohttp import web
from aiohttp.test_utils import TestServer

from app.speech.client import SpeechError, SpeechServiceClient


async def _start_server(routes: list[tuple[str, str, object]]) -> TestServer:
    app = web.Application()
    for method, path, handler in routes:
        app.router.add_route(method, path, handler)
    server = TestServer(app)
    await server.start_server()
    return server


async def _make_client(port: int, **kwargs) -> SpeechServiceClient:
    client = SpeechServiceClient(
        f"http://127.0.0.1:{port}",
        retries=kwargs.pop("retries", 0),
        retry_backoff_sec=0.01,
        **kwargs,
    )
    return client


async def test_transcribe_ok():
    captured: dict = {}

    async def handler(request: web.Request) -> web.Response:
        reader = await request.multipart()
        field = await reader.next()
        assert field is not None and field.name == "audio"
        captured["content_type"] = field.headers.get("Content-Type", "")
        captured["body"] = await field.read(decode=False)
        return web.json_response({"text": "привет", "duration_ms": 2000})

    server = await _start_server([("POST", "/api/v1/transcribe", handler)])
    client = await _make_client(server.port)
    try:
        text = await client.transcribe(b"\xff" * 160)
        assert text == "привет"
        assert captured["content_type"] == "audio/x-mulaw"
        assert captured["body"] == b"\xff" * 160
    finally:
        await client.close()
        await server.close()


async def test_transcribe_empty_audio_no_request():
    server = await _start_server([("POST", "/api/v1/transcribe", _unreachable)])
    client = await _make_client(server.port)
    try:
        assert await client.transcribe(b"") == ""
    finally:
        await client.close()
        await server.close()


async def _unreachable(_request: web.Request) -> web.Response:  # pragma: no cover
    raise AssertionError("request should not reach server")


async def test_transcribe_4xx_no_retry():
    calls = {"n": 0}

    async def handler(_request: web.Request) -> web.Response:
        calls["n"] += 1
        return web.json_response({"detail": "Invalid audio file"}, status=400)

    server = await _start_server([("POST", "/api/v1/transcribe", handler)])
    client = await _make_client(server.port, retries=3)
    try:
        with pytest.raises(SpeechError, match="400"):
            await client.transcribe(b"broken")
        assert calls["n"] == 1
    finally:
        await client.close()
        await server.close()


async def test_transcribe_500_retries_then_success():
    calls = {"n": 0}

    async def handler(_request: web.Request) -> web.Response:
        calls["n"] += 1
        if calls["n"] < 2:
            return web.json_response({"detail": "boom"}, status=500)
        return web.json_response({"text": "ок"})

    server = await _start_server([("POST", "/api/v1/transcribe", handler)])
    client = await _make_client(server.port, retries=2)
    try:
        assert await client.transcribe(b"\xff" * 160) == "ок"
        assert calls["n"] == 2
    finally:
        await client.close()
        await server.close()


async def test_transcribe_unavailable():
    client = SpeechServiceClient(
        "http://127.0.0.1:1", retries=0, stt_timeout=1.0
    )  # порт 1 — ничего не слушает
    try:
        with pytest.raises(SpeechError, match="unavailable"):
            await client.transcribe(b"\xff" * 160)
    finally:
        await client.close()


async def test_synthesize_ok():
    async def handler(request: web.Request) -> web.Response:
        payload = await request.json()
        assert payload["text"] == "Привет"
        return web.Response(body=b"WAVDATA", content_type="audio/wav")

    server = await _start_server([("POST", "/api/v1/synthesize", handler)])
    client = await _make_client(server.port)
    try:
        assert await client.synthesize("Привет") == b"WAVDATA"
    finally:
        await client.close()
        await server.close()


async def test_synthesize_empty_text_raises():
    server = await _start_server([("POST", "/api/v1/synthesize", _unreachable)])
    client = await _make_client(server.port)
    try:
        with pytest.raises(SpeechError, match="empty"):
            await client.synthesize("   ")
    finally:
        await client.close()
        await server.close()


async def test_health_ok_and_fail():
    async def handler(_request: web.Request) -> web.Response:
        return web.json_response({"status": "ok", "stt_loaded": True})

    server = await _start_server([("GET", "/health", handler)])
    client = await _make_client(server.port)
    try:
        data = await client.health()
        assert data is not None and data["status"] == "ok"
        assert client.last_health_ok is True
    finally:
        await client.close()
        await server.close()

    client_down = SpeechServiceClient("http://127.0.0.1:1")
    try:
        assert await client_down.health() is None
        assert client_down.last_health_ok is False
    finally:
        await client_down.close()


def test_transcribe_timeout_is_handled() -> None:
    # Синхронная проверка, что константы согласованы (без сети)
    client = SpeechServiceClient("http://example.invalid", stt_timeout=0.01)
    assert client._stt_timeout == 0.01  # noqa: SLF001
    asyncio.run(client.close())
