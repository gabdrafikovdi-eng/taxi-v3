"""Тесты backend-адаптеров: MockBackendClient и HTTPBackendClient."""

from __future__ import annotations

import pytest
from aiohttp import web
from aiohttp.test_utils import TestServer

from app.backend import build_backend
from app.backend.base import BackendError
from app.backend.http_client import HTTPBackendClient
from app.backend.mock import MockBackendClient
from app.config import Settings


async def test_mock_backend_lifecycle():
    backend = MockBackendClient()
    session_id = await backend.start_call("ext-1", "79990001122")
    assert session_id
    # Идемпотентность по external_id
    again = await backend.start_call("ext-1", "79990001122")
    assert again == session_id
    greeting = await backend.greeting(session_id)
    assert greeting and "такси" in greeting.lower()
    answer = await backend.handle_message(session_id, "мне нужна машина")
    assert "мне нужна машина" in answer
    operator = await backend.handle_message(session_id, "переведи на оператора")
    assert "оператор" in operator.lower()
    await backend.end_call(session_id)


async def test_mock_backend_unknown_session_raises():
    backend = MockBackendClient()
    with pytest.raises(KeyError):
        await backend.handle_message("no-such-id", "тест")


async def test_build_backend_modes():
    settings = Settings(BACKEND_MODE="mock", _env_file=None)
    assert isinstance(build_backend(settings), MockBackendClient)
    settings_http = Settings(
        BACKEND_MODE="http", BACKEND_URL="http://x", _env_file=None
    )
    assert isinstance(build_backend(settings_http), HTTPBackendClient)
    with pytest.raises(ValueError):
        build_backend(Settings(BACKEND_MODE="carrier-pigeon", _env_file=None))


# --------------------------------------------------------------------- HTTP

async def _start_backend_app() -> TestServer:
    state: dict = {"sessions": set(), "flaky": 0}

    async def start_call(request: web.Request) -> web.Response:
        payload = await request.json()
        state["last_start"] = payload
        state["sessions"].add("sess-1")
        return web.json_response({"call_session_id": "sess-1"}, status=201)

    async def greeting(request: web.Request) -> web.Response:
        call_id = request.match_info["call_id"]
        if call_id not in state["sessions"]:
            return web.json_response({"detail": "not found"}, status=404)
        return web.json_response({"text": "Здравствуйте!"})

    async def messages(request: web.Request) -> web.Response:
        call_id = request.match_info["call_id"]
        if call_id not in state["sessions"]:
            return web.json_response({"detail": "not found"}, status=404)
        if call_id == "sess-flaky":
            state["flaky"] += 1
            if state["flaky"] < 3:
                return web.json_response({"detail": "boom"}, status=503)
        payload = await request.json()
        state.setdefault("messages", []).append(payload["text"])
        return web.json_response({"response": f"эхо: {payload['text']}"})

    async def end_call(request: web.Request) -> web.Response:
        state["sessions"].add(request.match_info["call_id"])
        return web.Response(status=204)

    app = web.Application()
    app["state"] = state
    app.router.add_post("/api/v1/calls", start_call)
    app.router.add_get("/api/v1/calls/{call_id}/greeting", greeting)
    app.router.add_post("/api/v1/calls/{call_id}/messages", messages)
    app.router.add_post("/api/v1/calls/{call_id}/end", end_call)
    server = TestServer(app)
    await server.start_server()
    return server


async def test_http_backend_full_lifecycle():
    server = await _start_backend_app()
    client = HTTPBackendClient(f"http://127.0.0.1:{server.port}", timeout=5)
    try:
        session_id = await client.start_call("ext-9", "79990001122")
        assert session_id == "sess-1"
        # несуществующая сессия: 404 → None (приветствия нет)
        assert await client.greeting("no-such-session") is None
        assert await client.greeting(session_id) == "Здравствуйте!"
        response = await client.handle_message(session_id, "закажи такси")
        assert response == "эхо: закажи такси"
        await client.end_call(session_id)
    finally:
        await client.close()
        await server.close()


async def test_http_backend_retry_on_5xx():
    server = await _start_backend_app()
    server.app["state"]["sessions"].add("sess-flaky")
    client = HTTPBackendClient(f"http://127.0.0.1:{server.port}", timeout=5)
    try:
        response = await client.handle_message("sess-flaky", "раз, два")
        assert response == "эхо: раз, два"
        assert server.app["state"]["flaky"] == 3  # 2 x 503 + 1 success
    finally:
        await client.close()
        await server.close()


async def test_http_backend_4xx_raises():
    server = await _start_backend_app()
    client = HTTPBackendClient(f"http://127.0.0.1:{server.port}", timeout=5)
    try:
        with pytest.raises(BackendError):
            await client.handle_message("unknown-session", "текст")
    finally:
        await client.close()
        await server.close()


async def test_http_backend_unavailable_raises():
    client = HTTPBackendClient("http://127.0.0.1:1", timeout=1)
    try:
        with pytest.raises(BackendError, match="unavailable"):
            await client.start_call("ext", None)
    finally:
        await client.close()
