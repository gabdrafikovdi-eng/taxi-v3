"""Медиа-pipeline звонка.

Поток данных:

    GSM → GoIP4 → SIP/RTP → Asterisk → (snoop+externalMedia/UnicastRTP)
        → UDP-сокет pipeline → PhraseDetector (сегментация фраз)
        → speech-service STT → backend (LLM) → speech-service TTS
        → WAV → PCM16 8kHz → G.711 → RTP → Asterisk → GoIP4 → абонент

Между Asterisk и telephony-service аудио передаётся в исходном G.711
(µ-law/A-law) — преобразований на лету нет;speech-service декодирует G.711
сам. Playback: RTP-пакеты 20 мс (160 байт) отправляются на адрес,
с которого Asterisk присылает медиа (UnicastRTP bidirectional).
"""

from __future__ import annotations

import asyncio
import contextlib
import random
import socket
import time

from app import g711, wavutil
from app.ari.client import ARIClient
from app.backend.base import BackendClient, BackendError
from app.calls.call import Call
from app.calls.state import CallState
from app.config import Settings
from app.logging import call_id_var, jexception, jinfo, jwarning
from app.phrase import PhraseDetector
from app.rtp import build_rtp, parse_rtp
from app.speech.client import SpeechError, SpeechServiceClient

RTP_CHUNK_BYTES = 160  # 20 мс G.711 @ 8 кГц
RTP_CHUNK_SEC = 0.02
_SORRY_TEXT = "Извините, произошла техническая ошибка. Повторите, пожалуйста."


class CallPipeline:
    def __init__(
        self,
        settings: Settings,
        ari: ARIClient,
        speech: SpeechServiceClient,
        backend: BackendClient,
        call: Call,
        port: int,
    ) -> None:
        self._settings = settings
        self._ari = ari
        self._speech = speech
        self._backend = backend
        self._call = call
        self._port = port
        self._detector = PhraseDetector(
            codec=settings.MEDIA_FORMAT,
            speech_threshold=settings.ENERGY_SPEECH_THRESHOLD,
            silence_ms=settings.SILENCE_MS,
            min_speech_ms=settings.MIN_SPEECH_MS,
            max_utterance_ms=settings.MAX_UTTERANCE_MS,
            preroll_ms=settings.PREROLL_MS,
        )
        self._pt = settings.rtp_payload_type
        self._sock: socket.socket | None = None
        self._task: asyncio.Task | None = None
        self._stopping = False
        self._tx_seq = random.randint(0, 0xFFFF)
        self._tx_ts = random.randint(0, 0xFFFFFFFF)
        self._tx_ssrc = random.randint(1, 0xFFFFFFFF)
        self._asterisk_addr: tuple[str, int] | None = None

    # ---------------------------------------------------------------- lifecycle

    @property
    def port(self) -> int:
        return self._port

    async def start(self) -> None:
        self._task = asyncio.create_task(
            self.run(), name=f"call-pipeline-{self._call.call_id}"
        )

    async def stop(self) -> None:
        self._stopping = True
        if self._sock is not None:
            with contextlib.suppress(OSError):
                self._sock.close()
        if self._task:
            self._task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await self._task
            self._task = None

    # ------------------------------------------------------------------ receive

    async def run(self) -> None:
        loop = asyncio.get_running_loop()
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            sock.bind(("0.0.0.0", self._port))
            sock.setblocking(False)
            self._sock = sock
            jinfo(
                "pipeline_started",
                port=self._port,
                codec=self._settings.MEDIA_FORMAT,
                **self._call.log_fields(),
            )
            rx_packets = 0
            rx_bytes = 0
            last_stats = time.monotonic()
            while not self._stopping:
                data, addr = await loop.sock_recvfrom(sock, 4096)
                rx_packets += 1
                rx_bytes += len(data)
                now = time.monotonic()
                if now - last_stats >= 5.0:
                    jinfo(
                        "pipeline_stats",
                        rx_packets=rx_packets,
                        rx_bytes=rx_bytes,
                        rtp_source=(
                            f"{addr[0]}:{addr[1]}" if addr else None
                        ),
                        **self._call.log_fields(),
                    )
                    last_stats = now
                self._handle_datagram(data, addr)
        except (asyncio.CancelledError, OSError):
            pass
        except Exception:
            jexception("pipeline_crashed", **self._call.log_fields())
        finally:
            self._sock = None
            with contextlib.suppress(OSError):
                sock.close()
            jinfo(
                "pipeline_stopped",
                rx_packets=rx_packets,
                rx_bytes=rx_bytes,
                **self._call.log_fields(),
            )

    def _handle_datagram(self, data: bytes, addr: tuple[str, int]) -> None:
        packet = parse_rtp(data)
        if packet is None or not packet.payload:
            return
        if self._asterisk_addr is None:
            self._asterisk_addr = addr
            jinfo(
                "rtp_source_learned",
                address=f"{addr[0]}:{addr[1]}",
                **self._call.log_fields(),
            )
        if packet.payload_type != self._pt:
            return  # comfort noise/keepalive и др.
        state = self._call.state.current
        if state in (CallState.SPEAKING, CallState.PROCESSING, CallState.ENDING):
            return  # во время ответа речь абонента не собираем
        chunk = self._detector.feed(packet.payload)
        if chunk is None:
            return
        # Фраза завершена: сразу занимаем состояние и обрабатываем в фоне
        if not self._call.state.transition(CallState.PROCESSING):
            self._detector.reset()
            return
        task = asyncio.create_task(self._process_phrase(chunk))
        task.add_done_callback(lambda _t: None)

    # -------------------------------------------------------------- фраза: STT→LLM→TTS

    async def _process_phrase(self, audio: bytes) -> None:
        call = self._call
        token = call_id_var.set(call.call_id)
        try:
            try:
                text = await self._speech.transcribe(
                    audio, self._settings.stt_content_type
                )
            except SpeechError as exc:
                jwarning("stt_failed", error=str(exc), **call.log_fields())
                return
            jinfo(
                "phrase_recognized",
                text=text,
                audio_bytes=len(audio),
                **call.log_fields(),
            )
            if not text.strip():
                return
            if call.backend_call_session_id is None:
                jwarning("no_backend_session", **call.log_fields())
                return
            try:
                response = await self._backend.handle_message(
                    call.backend_call_session_id, text
                )
            except BackendError as exc:
                jwarning("backend_message_failed", error=str(exc), **call.log_fields())
                response = None
            if response:
                await self._speak(response)
        except Exception:
            jexception("phrase_processing_failed", **call.log_fields())
        finally:
            call_id_var.reset(token)
            self._detector.reset()
            if call.state.current == CallState.PROCESSING:
                call.state.transition(CallState.LISTENING)

    async def speak_greeting(self) -> None:
        """Приветствие из backend после answer (best-effort)."""
        if not self._settings.PLAY_GREETING:
            return
        call = self._call
        if call.backend_call_session_id is None:
            return
        try:
            greeting = await self._backend.greeting(call.backend_call_session_id)
        except BackendError as exc:
            jwarning("backend_greeting_failed", error=str(exc), **call.log_fields())
            return
        if greeting:
            await self._speak(greeting)

    # ----------------------------------------------------------------- playback

    async def _speak(self, text: str) -> None:
        call = self._call
        if not call.state.can(CallState.SPEAKING):
            return
        try:
            wav = await self._speech.synthesize(text)
            # speech-service возвращает WAV или MP3 (edge-tts) — приводим
            # к PCM16-моно 8 кГц и кодируем в телефонный G.711
            pcm = wavutil.decode_audio(wav, target_rate=8000)
            if not pcm:
                jwarning("tts_empty_audio", **call.log_fields())
                return
            audio = g711.encode(self._settings.MEDIA_FORMAT, pcm)
        except (SpeechError, wavutil.WavParseError) as exc:
            jwarning("tts_failed", error=str(exc), **call.log_fields())
            return
        if not call.state.transition(CallState.SPEAKING):
            return
        jinfo(
            "speaking_started",
            text=text,
            audio_bytes=len(audio),
            duration_ms=len(audio) // 8,  # 1 байт G.711 = 1 сэмпл @8кГц
            **call.log_fields(),
        )
        try:
            await self._send_rtp_stream(audio)
        finally:
            call.state.transition(CallState.LISTENING)

    async def _send_rtp_stream(self, audio: bytes) -> None:
        sock = self._sock
        addr = self._asterisk_addr
        if sock is None or sock.fileno() == -1 or addr is None:
            jwarning(
                "rtp_playback_skipped",
                reason="no_socket" if sock is None else "no_rtp_source",
                **self._call.log_fields(),
            )
            return
        loop = asyncio.get_running_loop()
        next_send = time.monotonic()
        for offset in range(0, len(audio), RTP_CHUNK_BYTES):
            if self._stopping or self._call.state.current in (
                CallState.ENDING,
                CallState.ENDED,
                CallState.FAILED,
            ):
                break
            chunk = audio[offset : offset + RTP_CHUNK_BYTES]
            packet = build_rtp(
                self._pt,
                self._tx_seq & 0xFFFF,
                self._tx_ts & 0xFFFFFFFF,
                self._tx_ssrc,
                chunk,
            )
            self._tx_seq += 1
            self._tx_ts += len(chunk)
            try:
                await loop.sock_sendto(sock, packet, addr)
            except OSError as exc:
                jwarning("rtp_send_failed", error=str(exc), **self._call.log_fields())
                break
            next_send += RTP_CHUNK_SEC
            delay = next_send - time.monotonic()
            if delay > 0:
                await asyncio.sleep(delay)
        jinfo("speaking_finished", **self._call.log_fields())
