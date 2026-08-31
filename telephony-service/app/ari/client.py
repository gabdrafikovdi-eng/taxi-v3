"""Клиент Asterisk REST Interface (ARI): REST + WebSocket-события.

* REST-методы для управления каналами/бриджами (answer, snoop, externalMedia…);
* WebSocket ``/ari/events`` — событийная модель Stasis-приложения;
* автоматический реконнект с экспоненциальным backoff;
* события кладутся в очередь и обрабатываются последовательно (порядок
  сохраняется, WS-чтение не блокируется долгими обработчиками).
"""

from __future__ import annotations

import asyncio
import contextlib
import json
from collections.abc import Awaitable, Callable

import aiohttp

from app.config import Settings
from app.logging import jexception, jinfo, jwarning

EventHandler = Callable[[dict], Awaitable[None]]

_OK_STATUSES = {200, 201, 202, 204}


class ARIError(RuntimeError):
    """Ошибка REST-запроса к ARI."""


class ARINotConnected(ARIError):
    """ARI-сессия ещё не установлена."""


class ARIClient:
    def __init__(self, settings: Settings, on_event: EventHandler) -> None:
        self._base_url = settings.ASTERISK_ARI_URL.rstrip("/")
        self._username = settings.ASTERISK_ARI_USERNAME
        self._password = settings.ASTERISK_ARI_PASSWORD
        self._app = settings.ASTERISK_ARI_APP
        self._on_event = on_event
        self._min_reconnect = settings.ARI_RECONNECT_MIN_SEC
        self._max_reconnect = settings.ARI_RECONNECT_MAX_SEC

        self._session: aiohttp.ClientSession | None = None
        self._auth = aiohttp.BasicAuth(self._username, self._password)
        self._ws_task: asyncio.Task | None = None
        self._worker_task: asyncio.Task | None = None
        self._queue: asyncio.Queue[dict] = asyncio.Queue()
        self._connected = asyncio.Event()
        self._stopping = asyncio.Event()
        self._reconnect_delay = self._min_reconnect

    # ---------------------------------------------------------------- lifecycle

    @property
    def connected(self) -> bool:
        return self._connected.is_set()

    async def start(self) -> None:
        self._stopping.clear()
        self._worker_task = asyncio.create_task(
            self._event_worker(), name="ari-event-worker"
        )
        self._ws_task = asyncio.create_task(self._run_forever(), name="ari-ws")

    async def close(self) -> None:
        self._stopping.set()
        self._connected.clear()
        for task in (self._ws_task, self._worker_task):
            if task:
                task.cancel()
                with contextlib.suppress(asyncio.CancelledError):
                    await task
        if self._session:
            await self._session.close()
            self._session = None

    async def wait_connected(self, timeout: float | None = None) -> bool:
        try:
            await asyncio.wait_for(self._connected.wait(), timeout)
        except asyncio.TimeoutError:
            return False
        return True

    # ------------------------------------------------------------------ ws loop

    async def _run_forever(self) -> None:
        while not self._stopping.is_set():
            try:
                await self._ws_once()
            except asyncio.CancelledError:
                raise
            except Exception as exc:  # noqa: BLE001 — реконнект на любую ошибку сети
                jwarning("ari_connection_lost", error=str(exc))
            self._connected.clear()
            if self._stopping.is_set():
                break
            delay = self._reconnect_delay
            jinfo("ari_reconnect_scheduled", delay_sec=round(delay, 1))
            with contextlib.suppress(asyncio.TimeoutError):
                await asyncio.wait_for(self._stopping.wait(), timeout=delay)
            self._reconnect_delay = min(delay * 2, self._max_reconnect)

    async def _ws_once(self) -> None:
        session = self._ensure_session()
        ws_url = self._base_url.replace("http", "ws", 1) + "/ari/events"
        params = {"app": self._app, "api_key": f"{self._username}:{self._password}"}
        async with session.ws_connect(
            ws_url,
            params=params,
            auth=self._auth,
            timeout=aiohttp.ClientWSTimeout(ws_close=5),
        ) as ws:
            jinfo("ari_websocket_connected", url=self._base_url, app=self._app)
            self._connected.set()
            self._reconnect_delay = self._min_reconnect
            keepalive = asyncio.create_task(self._keepalive(ws))
            try:
                async for msg in ws:
                    if msg.type == aiohttp.WSMsgType.TEXT:
                        try:
                            event = json.loads(msg.data)
                        except json.JSONDecodeError:
                            jwarning("ari_event_malformed_json", length=len(msg.data))
                            continue
                        if isinstance(event, dict):
                            await self._queue.put(event)
                    elif msg.type in (
                        aiohttp.WSMsgType.CLOSED,
                        aiohttp.WSMsgType.ERROR,
                    ):
                        break
            finally:
                keepalive.cancel()
                with contextlib.suppress(asyncio.CancelledError):
                    await keepalive

    @staticmethod
    async def _keepalive(ws: aiohttp.ClientWebSocketResponse) -> None:
        """Периодический ping, чтобы соединение не рвалось по inactivity."""
        while True:
            await asyncio.sleep(20)
            with contextlib.suppress(ConnectionError, RuntimeError):
                await ws.ping()

    async def _event_worker(self) -> None:
        while True:
            event = await self._queue.get()
            try:
                await self._on_event(event)
            except asyncio.CancelledError:
                raise
            except Exception:  # noqa: BLE001 — ошибка одного события не роняет сервис
                jexception("ari_event_handler_failed", type=event.get("type"))
            finally:
                self._queue.task_done()

    def _ensure_session(self) -> aiohttp.ClientSession:
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession()
        return self._session

    # --------------------------------------------------------------------- REST

    async def request(
        self,
        method: str,
        path: str,
        params: dict | None = None,
        json_body: dict | None = None,
    ) -> object:
        if self._session is None or self._session.closed:
            raise ARINotConnected("ARI session is not established")
        url = f"{self._base_url}/ari{path}"
        timeout = aiohttp.ClientTimeout(total=10)
        async with self._session.request(
            method, url, params=params, json=json_body, auth=self._auth, timeout=timeout
        ) as resp:
            if resp.status not in _OK_STATUSES:
                body = (await resp.text())[:200]
                raise ARIError(f"{method} {path} -> {resp.status}: {body}")
            if resp.status == 204:
                return None
            if resp.content_type == "application/json":
                return await resp.json()
            return await resp.read()

    # -------------------------------------------------------------- каналы/медиа

    async def answer(self, channel_id: str) -> None:
        await self.request("POST", f"/channels/{channel_id}/answer")

    async def hangup(self, channel_id: str, reason: str = "normal") -> None:
        await self.request("DELETE", f"/channels/{channel_id}", params={"reason": reason})

    async def create_snoop(
        self, channel_id: str, spy: str = "in", whisper: str = "out"
    ) -> str:
        """Создать snoop-канал (опциональный API, напр. для записи одной стороны)."""
        result = await self.request(
            "POST",
            f"/channels/{channel_id}/snoop",
            params={"spy": spy, "whisper": whisper, "app": self._app},
        )
        return str(result["id"]) if isinstance(result, dict) else ""

    async def create_external_media(
        self, external_host: str, app: str | None = None, media_format: str = "ulaw"
    ) -> str:
        """Создать UnicastRTP-канал (external media). Вернуть его id."""
        result = await self.request(
            "POST",
            "/channels/externalMedia",
            params={
                "app": app or self._app,
                "external_host": external_host,
                "format": media_format,
                "encapsulation": "rtp",
                "transport": "udp",
            },
        )
        return str(result["id"]) if isinstance(result, dict) else ""

    async def create_bridge(self, name: str) -> str:
        result = await self.request(
            "POST", "/bridges", params={"type": "mixing", "name": name}
        )
        return str(result["id"]) if isinstance(result, dict) else ""

    async def add_channel_to_bridge(self, bridge_id: str, channel_id: str) -> None:
        await self.request(
            "POST", f"/bridges/{bridge_id}/addChannel", params={"channel": channel_id}
        )

    async def destroy_bridge(self, bridge_id: str) -> None:
        await self.request("DELETE", f"/bridges/{bridge_id}")

    async def get_channel(self, channel_id: str) -> dict | None:
        try:
            result = await self.request("GET", f"/channels/{channel_id}")
        except ARIError:
            return None
        return result if isinstance(result, dict) else None
