"""Тесты CallManager: событийная модель ARI + полный медиа-цикл по UDP.

Эмулируются только REST-вызовы Asterisk (FakeARI); RTP-медиа ходит по
настоящему UDP (тестовый сокет — роль Asterisk): фраза → STT (fake) →
backend (mock) → TTS (fake) → RTP-пакеты обратно в тестовый сокет.
"""

from __future__ import annotations

import asyncio
import math
import socket
import struct

from app import g711, wavutil
from app.backend.mock import MockBackendClient
from app.calls.manager import CallManager
from app.calls.state import CallState
from app.config import Settings
from app.rtp import build_rtp, parse_rtp


# --------------------------------------------------------------------- fakes


class FakeARI:
    def __init__(self) -> None:
        self.calls: list[tuple[str, str]] = []
        self._counter = 0

    def _next_id(self, prefix: str) -> str:
        self._counter += 1
        return f"{prefix}-{self._counter}"

    async def answer(self, channel_id: str) -> None:
        self.calls.append(("answer", channel_id))

    async def hangup(self, channel_id: str, reason: str = "normal") -> None:
        self.calls.append(("hangup", channel_id))

    async def create_external_media(
        self, external_host: str, app: str | None = None, media_format: str = "ulaw"
    ) -> str:
        self.calls.append(("external_media", external_host))
        return self._next_id("extmedia")

    async def create_bridge(self, name: str) -> str:
        return self._next_id("bridge")

    async def add_channel_to_bridge(self, bridge_id: str, channel_id: str) -> None:
        self.calls.append(("bridge_add", channel_id))

    async def destroy_bridge(self, bridge_id: str) -> None:
        self.calls.append(("bridge_destroy", bridge_id))


class FakeSpeech:
    def __init__(self) -> None:
        self.stt_calls: list[tuple[int, str]] = []
        self.tts_texts: list[str] = []

    async def transcribe(self, audio: bytes, content_type: str = "audio/x-mulaw") -> str:
        self.stt_calls.append((len(audio), content_type))
        return "хочу такси на советскую"

    async def synthesize(self, text: str, speaker: str | None = None) -> bytes:
        self.tts_texts.append(text)
        pcm = struct.pack("<2400h", *([3000] * 2400))  # 0.3 с PCM16 @8кГц
        return wavutil.pcm16_to_wav(pcm, 8000)


def _test_settings(**overrides) -> Settings:
    params = dict(
        BACKEND_MODE="mock",
        MEDIA_FORMAT="ulaw",
        PLAY_GREETING=False,
        ENERGY_SPEECH_THRESHOLD=900.0,
        SILENCE_MS=200,
        MIN_SPEECH_MS=100,
        MAX_UTTERANCE_MS=5000,
        PREROLL_MS=60,
        RTP_SERVICE_PORT_START=28000,
        RTP_SERVICE_PORT_END=28020,
        _env_file=None,
    )
    params.update(overrides)
    return Settings(**params)


def _stasis_start(channel_id: str = "ch-1", context: str = "from-goip") -> dict:
    return {
        "type": "StasisStart",
        "timestamp": "2026-08-31T12:00:00.000+0000",
        "channel": {
            "id": channel_id,
            "name": "PJSIP/goip4-00000001",
            "state": "Ring",
            "dialplan": {"context": context},
            "caller": {"number": "79920770402"},
        },
    }


def _hangup(channel_id: str = "ch-1") -> dict:
    return {
        "type": "ChannelHangupRequest",
        "timestamp": "2026-08-31T12:01:00.000+0000",
        "channel": {"id": channel_id},
    }


def _loud_chunk() -> bytes:
    samples = [int(10000 * math.sin(2 * math.pi * 440 * i / 8000)) for i in range(160)]
    return g711.ulaw_encode(struct.pack("<160h", *samples))


def _silence_chunk() -> bytes:
    return g711.ulaw_encode(struct.pack("<160h", *([0] * 160)))


# --------------------------------------------------------------------- tests


async def test_ignores_aux_and_foreign_channels():
    manager = CallManager(
        _test_settings(), FakeARI(), FakeSpeech(), MockBackendClient()
    )
    snoop_event = _stasis_start("sn-1")
    snoop_event["channel"]["name"] = "Snoop/ch-1-1"
    await manager.handle_event(snoop_event)
    other_event = _stasis_start("ch-2", context="from-internal")
    await manager.handle_event(other_event)
    assert manager.stats()["calls_total"] == 0


async def test_duplicate_event_ignored():
    manager = CallManager(
        _test_settings(), FakeARI(), FakeSpeech(), MockBackendClient()
    )
    await manager.handle_event(_stasis_start("dup-1"))
    await manager.handle_event(_stasis_start("dup-1"))  # идентичный event
    assert manager.stats()["calls_total"] == 1


async def test_full_call_media_cycle():
    settings = _test_settings()
    ari = FakeARI()
    speech = FakeSpeech()
    backend = MockBackendClient()
    manager = CallManager(settings, ari, speech, backend)

    await manager.handle_event(_stasis_start("ch-1"))
    assert manager.active_calls == 1
    call = manager._calls["ch-1"]  # noqa: SLF001 — тестовый доступ
    assert call.state.current == CallState.CONNECTED
    assert call.caller_phone == "79920770402"
    assert call.backend_call_session_id is not None
    assert ("answer", "ch-1") in ari.calls
    assert call.external_media_channel_id and call.bridge_id
    # caller и externalMedia добавлены в бридж
    bridge_adds = [t for action, t in ari.calls if action == "bridge_add"]
    assert "ch-1" in bridge_adds
    assert call.external_media_channel_id in bridge_adds

    # Ждём, пока pipeline забиндит RTP-сокет
    await asyncio.sleep(0.2)
    assert call.pipeline is not None

    # "Asterisk" шлёт RTP-медиа: тишина → речь (200 мс) → тишина (240 мс)
    probe = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    probe.bind(("127.0.0.1", 0))
    probe.setblocking(False)
    loop = asyncio.get_running_loop()
    target = ("127.0.0.1", call.rtp_port)
    seq = 0
    try:
        chunks = [_silence_chunk() for _ in range(3)]
        chunks += [_loud_chunk() for _ in range(10)]
        chunks += [_silence_chunk() for _ in range(12)]
        for chunk in chunks:
            await loop.sock_sendto(probe, build_rtp(0, seq, seq * 160, 555, chunk), target)
            seq += 1

        # Фраза должна дойти до STT (с запасом на обработку)
        for _ in range(50):
            await asyncio.sleep(0.05)
            if speech.stt_calls:
                break
        assert speech.stt_calls, "фраза не дошла до STT"
        length, content_type = speech.stt_calls[0]
        assert content_type == "audio/x-mulaw"
        assert length > 100

        # Backend получил текст
        session_id = call.backend_call_session_id
        assert backend.calls[session_id] == ["хочу такси на советскую"]

        # TTS-ответ должен прийти RTP-пакетами в тестовый сокет
        received: bytes | None = None
        try:
            received, _addr = await asyncio.wait_for(
                loop.sock_recvfrom(probe, 2048), timeout=3
            )
        except asyncio.TimeoutError:
            pass
        assert received is not None, "TTS-ответ не пришёл по RTP"
        parsed = parse_rtp(received)
        assert parsed is not None
        assert parsed.payload_type == 0
        assert len(parsed.payload) == 160
        assert speech.tts_texts == [
            "Принято: хочу такси на советскую. Что-нибудь ещё?"
        ]
    finally:
        probe.close()

    # Hangup: teardown всех ресурсов
    await manager.handle_event(_hangup("ch-1"))
    assert call.state.current == CallState.ENDED
    assert manager.active_calls == 0
    hangup_targets = {t for action, t in ari.calls if action == "hangup"}
    assert {"ch-1", call.external_media_channel_id} <= hangup_targets
    assert ("bridge_destroy", call.bridge_id) in ari.calls


async def test_call_setup_backend_error_fails_call():
    from app.backend.base import BackendError

    class FailingBackend(MockBackendClient):
        async def start_call(self, external_id: str, caller_phone: str | None) -> str:
            raise BackendError("backend down")

    ari = FakeARI()
    manager = CallManager(_test_settings(), ari, FakeSpeech(), FailingBackend())
    await manager.handle_event(_stasis_start("ch-err"))
    # Звонок не остался активным, answer не вызывался
    assert manager.active_calls == 0
    assert ("answer", "ch-err") not in ari.calls
