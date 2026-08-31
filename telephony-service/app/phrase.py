"""Энергетическая сегментация фраз (turn-taking) на входящем G.711-потоке.

Работает поверх RTP-чанков 20 мс (160 байт G.711): копит preroll, детектирует
начало речи (2 чанка подряд выше порога RMS), завершает фразу по паузе
(``SILENCE_MS``), отбрасывает короткий шум (< ``MIN_SPEECH_MS``) и
принудительно отдаёт фразу при превышении ``MAX_UTTERANCE_MS``.
"""

from __future__ import annotations

from collections import deque

from app import g711

CHUNK_MS = 20  # длительность одного RTP-чанка G.711 (160 байт @8kHz)

_SILENT = "silent"
_CAPTURING = "capturing"


class PhraseDetector:
    def __init__(
        self,
        codec: str = "ulaw",
        speech_threshold: float = 900.0,
        silence_ms: int = 700,
        min_speech_ms: int = 300,
        max_utterance_ms: int = 15000,
        preroll_ms: int = 200,
        start_frames: int = 2,
    ) -> None:
        if codec not in ("ulaw", "alaw"):
            raise ValueError(f"unsupported codec: {codec!r}")
        self._codec = codec
        self._threshold = speech_threshold
        self._silence_frames = max(1, silence_ms // CHUNK_MS)
        self._min_speech_frames = max(1, min_speech_ms // CHUNK_MS)
        self._max_utterance_frames = max(1, max_utterance_ms // CHUNK_MS)
        self._preroll: deque[bytes] = deque(maxlen=max(1, preroll_ms // CHUNK_MS))
        self._start_frames = max(1, start_frames)
        self._state = _SILENT
        self._buf: list[bytes] = []
        self._speech_frames = 0
        self._silence_frames_run = 0
        self._speech_run = 0

    @property
    def capturing(self) -> bool:
        return self._state == _CAPTURING

    def feed(self, chunk: bytes) -> bytes | None:
        """Добавить G.711-чанк. Вернуть G.711-байты завершённой фразы или None."""
        if not chunk:
            return None
        level = g711.rms(g711.decode(self._codec, chunk))
        is_speech = level >= self._threshold

        if self._state == _SILENT:
            self._preroll.append(chunk)
            if is_speech:
                self._speech_run += 1
                if self._speech_run >= self._start_frames:
                    self._state = _CAPTURING
                    self._buf = list(self._preroll)
                    # считаем только РЕЧЬ (preroll — тишина перед ней)
                    self._speech_frames = self._start_frames
                    self._silence_frames_run = 0
            else:
                self._speech_run = 0
            if self._state == _SILENT:
                return None

        # capturing
        self._buf.append(chunk)
        if is_speech:
            self._speech_frames += 1
            self._silence_frames_run = 0
        else:
            self._silence_frames_run += 1

        if self._speech_frames >= self._max_utterance_frames:
            return self._emit()
        if self._silence_frames_run >= self._silence_frames:
            if self._speech_frames >= self._min_speech_frames:
                return self._emit()
            self._reset_capture()
        return None

    def flush(self) -> bytes | None:
        """Принудительно отдать недозавершённую фразу (hangup/stop)."""
        if (
            self._state == _CAPTURING
            and self._speech_frames >= self._min_speech_frames
        ):
            return self._emit()
        self.reset()
        return None

    def reset(self) -> None:
        """Сброс состояния (после playback — не захватывать хвосты)."""
        self._state = _SILENT
        self._buf = []
        self._speech_frames = 0
        self._silence_frames_run = 0
        self._speech_run = 0
        self._preroll.clear()

    def _emit(self) -> bytes:
        phrase = b"".join(self._buf)
        self._reset_capture()
        return phrase

    def _reset_capture(self) -> None:
        self._state = _SILENT
        self._buf = []
        self._speech_frames = 0
        self._silence_frames_run = 0
        self._speech_run = 0
        self._preroll.clear()
