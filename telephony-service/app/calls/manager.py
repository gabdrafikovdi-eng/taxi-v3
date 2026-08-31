"""CallManager: оркестрация звонков поверх событий Asterisk ARI.

Обрабатывает StasisStart/ChannelHangupRequest/StasisEnd/ChannelStateChange/
ChannelDtmfReceived, создаёт медиа-топологию (snoop + externalMedia +
mixing bridge), запускает pipeline и следит за таймаутами. Дедуплицирует
события (duplicate protection), все ошибки изолируются — сервис не падает.
"""

from __future__ import annotations

import asyncio
import contextlib
from collections import OrderedDict
from uuid import uuid4

from app.ari.client import ARIClient, ARIError
from app.backend.base import BackendClient, BackendError
from app.calls.call import Call
from app.calls.pipeline import CallPipeline
from app.calls.state import CallState
from app.config import Settings
from app.logging import jexception, jinfo, jwarning
from app.speech.client import SpeechServiceClient

_DEDUP_MAX = 5000
# Контексты dialplan, из которых принимаем звонки в приложение
_ALLOWED_CONTEXTS = {"from-goip", "test"}
# Префиксы служебных каналов (snoop/externalMedia), не являющихся звонками
_AUX_CHANNEL_PREFIXES = ("Snoop/", "UnicastRTP/")


class CallManager:
    def __init__(
        self,
        settings: Settings,
        ari: ARIClient,
        speech: SpeechServiceClient,
        backend: BackendClient,
    ) -> None:
        self._settings = settings
        self._ari = ari
        self._speech = speech
        self._backend = backend
        self._calls: dict[str, Call] = {}  # by asterisk channel id
        self._busy_ports: set[int] = set()
        self._seen_events: OrderedDict[str, None] = OrderedDict()
        self._stopping = False

    # ------------------------------------------------------------------ status

    @property
    def active_calls(self) -> int:
        return sum(1 for c in self._calls.values() if c.state.is_active())

    def stats(self) -> dict[str, object]:
        return {
            "active_calls": self.active_calls,
            "calls_total": len(self._calls),
            "busy_ports": len(self._busy_ports),
        }

    async def shutdown(self) -> None:
        """Graceful shutdown: завершить активные звонки."""
        self._stopping = True
        for call in list(self._calls.values()):
            with contextlib.suppress(Exception):
                await self._teardown_call(call, reason="service_shutdown")
        self._calls.clear()

    # -------------------------------------------------------------- event entry

    async def handle_event(self, event: dict) -> None:
        event_type = event.get("type")
        channel = event.get("channel") or {}
        channel_id = str(channel.get("id", ""))
        key = f"{event_type}:{channel_id}:{event.get('timestamp')}"
        if self._is_duplicate(key):
            jinfo("ari_event_duplicate", type=str(event_type), channel_id=channel_id)
            return
        handler = {
            "StasisStart": self._on_stasis_start,
            "ChannelHangupRequest": self._on_hangup_request,
            "StasisEnd": self._on_stasis_end,
            "ChannelStateChange": self._on_channel_state_change,
            "ChannelDtmfReceived": self._on_dtmf,
        }.get(str(event_type))
        if handler is None:
            return
        await handler(event)

    def _is_duplicate(self, key: str) -> bool:
        if key in self._seen_events:
            self._seen_events.move_to_end(key)
            return True
        self._seen_events[key] = None
        if len(self._seen_events) > _DEDUP_MAX:
            self._seen_events.popitem(last=False)
        return False

    # ------------------------------------------------------------ event handlers

    async def _on_stasis_start(self, event: dict) -> None:
        channel = event.get("channel") or {}
        name = str(channel.get("name", ""))
        if name.startswith(_AUX_CHANNEL_PREFIXES):
            return
        context = str((channel.get("dialplan") or {}).get("context", ""))
        if context not in _ALLOWED_CONTEXTS:
            return
        channel_id = str(channel.get("id", ""))
        if channel_id in self._calls:  # повторный StasisStart того же канала
            return
        caller = channel.get("caller") or {}
        caller_phone = str(caller["number"]) if caller.get("number") else None

        call = Call(
            call_id=str(uuid4()),
            channel_id=channel_id,
            caller_phone=caller_phone,
            external_id=str(uuid4()),
        )
        self._calls[channel_id] = call
        jinfo("call_incoming", caller=caller_phone, context=context, **call.log_fields())
        try:
            await self._setup_call(call)
        except (ARIError, BackendError) as exc:
            jwarning("call_setup_failed", error=str(exc), **call.log_fields())
            await self._teardown_call(call, reason="setup_failed")
        except asyncio.CancelledError:
            raise
        except Exception as exc:
            jexception("call_setup_unexpected_error", error=str(exc), **call.log_fields())
            await self._teardown_call(call, reason="setup_error")

    async def _setup_call(self, call: Call) -> None:
        # 1. Сессия в backend (модель backend НЕ меняется — только API-слой)
        call.backend_call_session_id = await self._backend.start_call(
            call.external_id, call.caller_phone
        )
        # 2. RTP-порт external media
        port = self._allocate_port()
        call.rtp_port = port
        # 3. Ответить и построить медиа-топологию:
        #    caller + UnicastRTP(externalMedia) в одном mixing-бридже.
        #    RTP абонента идёт в наш UDP-сокет, наш RTP — абоненту.
        #    Один retry на externalMedia — защита от переходных гонок.
        await self._ari.answer(call.channel_id)
        call.external_media_channel_id = await self._retry_once(
            lambda: self._ari.create_external_media(
                f"{self._settings.TELEPHONY_EXTERNAL_HOST}:{port}",
                media_format=self._settings.MEDIA_FORMAT,
            ),
            f"external_media:{call.channel_id}",
        )
        call.bridge_id = await self._ari.create_bridge(f"taxi-{call.call_id}")
        await self._ari.add_channel_to_bridge(call.bridge_id, call.channel_id)
        await self._ari.add_channel_to_bridge(
            call.bridge_id, call.external_media_channel_id
        )
        call.state.transition(CallState.CONNECTED)
        # 4. Pipeline: RTP-приём, фразы, STT→backend→TTS
        pipeline = CallPipeline(
            self._settings, self._ari, self._speech, self._backend, call, port
        )
        call.pipeline = pipeline
        await pipeline.start()
        await pipeline.speak_greeting()
        # 5. Watchdog максимальной длительности
        call.watchdog_task = asyncio.create_task(
            self._watchdog(call), name=f"watchdog-{call.call_id}"
        )
        jinfo("call_established", rtp_port=port, **call.log_fields())

    async def _retry_once(self, factory, label: str):
        """Выполнить операцию с одним повтором при ошибке ARI (задержка 150 мс)."""
        try:
            return await factory()
        except ARIError as exc:
            jwarning("ari_setup_retry", target=label, error=str(exc))
            await asyncio.sleep(0.15)
            return await factory()

    async def _on_hangup_request(self, event: dict) -> None:
        channel_id = str((event.get("channel") or {}).get("id", ""))
        call = self._calls.get(channel_id)
        if call is None:
            return
        await self._teardown_call(call, reason="caller_hangup")

    async def _on_stasis_end(self, event: dict) -> None:
        channel_id = str((event.get("channel") or {}).get("id", ""))
        call = self._calls.get(channel_id)
        if call is None:
            return
        await self._teardown_call(call, reason="stasis_end")

    async def _on_channel_state_change(self, event: dict) -> None:
        channel = event.get("channel") or {}
        call = self._calls.get(str(channel.get("id", "")))
        if call is None:
            return
        if (
            str(channel.get("state", "")) == "Up"
            and call.state.current == CallState.RINGING
        ):
            call.state.transition(CallState.CONNECTED)
            jinfo("call_answered", **call.log_fields())

    async def _on_dtmf(self, event: dict) -> None:
        digit = str(event.get("digit") or "").strip()
        if digit:
            jinfo("dtmf_received", digit=digit)

    # ------------------------------------------------------------------ teardown

    async def _teardown_call(self, call: Call, reason: str) -> None:
        if call.state.is_terminal():
            return
        if call.state.can(CallState.ENDING):
            call.state.transition(CallState.ENDING)
        # Pipeline: закрыть RTP-сокет и остановить обработку
        if call.pipeline is not None:
            with contextlib.suppress(Exception):
                await call.pipeline.stop()
        # Watchdog
        if call.watchdog_task is not None:
            call.watchdog_task.cancel()  # type: ignore[union-attr]
        # Asterisk: external media канал и бридж (best-effort)
        if call.external_media_channel_id:
            with contextlib.suppress(ARIError, asyncio.TimeoutError):
                await self._ari.hangup(call.external_media_channel_id)
        if call.bridge_id:
            with contextlib.suppress(ARIError, asyncio.TimeoutError):
                await self._ari.destroy_bridge(call.bridge_id)
        # Caller
        with contextlib.suppress(ARIError, asyncio.TimeoutError):
            await self._ari.hangup(call.channel_id)
        # Backend: end_call (best-effort)
        if call.backend_call_session_id:
            with contextlib.suppress(BackendError, asyncio.TimeoutError):
                await self._backend.end_call(call.backend_call_session_id)
        call.state.transition(CallState.ENDED)
        self._release_port(call.rtp_port)
        self._calls.pop(call.channel_id, None)
        jinfo("call_ended", reason=reason, **call.log_fields())

    # ------------------------------------------------------------------ watchdog

    async def _watchdog(self, call: Call) -> None:
        try:
            await asyncio.sleep(self._settings.MAX_CALL_DURATION_SEC)
        except asyncio.CancelledError:
            return
        if call.state.is_active():
            jwarning("call_max_duration_reached", **call.log_fields())
            with contextlib.suppress(ARIError):
                await self._ari.hangup(call.channel_id)

    # --------------------------------------------------------------------- ports

    def _allocate_port(self) -> int:
        start = self._settings.RTP_SERVICE_PORT_START
        end = self._settings.RTP_SERVICE_PORT_END
        for port in range(start, end + 1):
            if port in self._busy_ports:
                continue
            if self._port_bindable(port):
                self._busy_ports.add(port)
                return port
        raise RuntimeError(f"no free RTP port in range {start}-{end}")

    @staticmethod
    def _port_bindable(port: int) -> bool:
        import socket

        with contextlib.suppress(OSError):
            probe = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            try:
                probe.bind(("0.0.0.0", port))
                return True
            finally:
                probe.close()
        return False

    def _release_port(self, port: int | None) -> None:
        if port is not None:
            self._busy_ports.discard(port)
