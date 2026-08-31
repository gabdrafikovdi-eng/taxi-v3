"""Тесты клиентского FSM из test_telephony_mic.py и release/reload в app.main.

Проверяют именно обнаруженный дефект: во время долгого benchmark-запроса
клиент не должен записывать/отправлять новые фразы (ровно один HTTP-запрос
на одну фразу), а после ошибки — возвращаться в состояние ожидания.
"""

from __future__ import annotations

import importlib.util
import sys
import threading
import time
from pathlib import Path
from types import ModuleType, SimpleNamespace

import numpy as np
import pytest
import requests

MODULE_PATH = Path(__file__).resolve().parent.parent / "test_telephony_mic.py"


def _load_client_module() -> ModuleType:
    for skip in ("sounddevice", "soundfile", "silero_vad"):
        pytest.importorskip(skip)
    spec = importlib.util.spec_from_file_location(
        "test_telephony_mic_under_test", MODULE_PATH
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def client() -> ModuleType:
    return _load_client_module()


# ---------------------------------------------------------------------------
# Фейки
# ---------------------------------------------------------------------------


class FakeVAD:
    """Детерминированный VAD: отдаёт результаты из списка по очереди."""

    def __init__(self, results: list[bool]) -> None:
        self._results = list(results)
        self.calls = 0

    def __call__(self, chunk: np.ndarray) -> bool:
        self.calls += 1
        if self._results:
            return self._results.pop(0)
        return False


class FakePoster:
    """Инъекция вместо requests.post; опционально медленный/падающий."""

    def __init__(
        self,
        delay: float = 0.0,
        fail: bool = False,
        exit_on_call: bool = False,
        payload: dict | None = None,
    ) -> None:
        self.calls: list[dict] = []
        self._delay = delay
        self._fail = fail
        self._exit = exit_on_call
        self._payload = payload or {"results": [], "duration_ms": 100}
        self._lock = threading.Lock()

    def __call__(self, url: str, files=None, timeout=None):
        with self._lock:
            self.calls.append({"url": url, "timeout": timeout})
        if self._delay:
            time.sleep(self._delay)
        if self._exit:
            raise requests.exceptions.ConnectionError("server gone")
        if self._fail:
            raise requests.exceptions.Timeout("benchmark too slow")
        response = SimpleNamespace()
        response.raise_for_status = lambda: None
        response.json = lambda: dict(self._payload)
        return response


class EmitCollector:
    def __init__(self) -> None:
        self.lines: list[str] = []

    def __call__(self, text: str) -> None:
        self.lines.append(text)


def _chunk(client: ModuleType) -> np.ndarray:
    return np.zeros(client.CHUNK_SAMPLES_48K, dtype=np.float32)


def _make_fsm(client: ModuleType, vad: FakeVAD, emit: EmitCollector):
    return client.PhraseStateMachine(
        vad,
        min_speech_chunks=2,
        max_silence_chunks=2,
        emit=emit,
    )


def _feed_phrase(client: ModuleType, fsm, vad: FakeVAD):
    """Прокормить фразу: речь + пауза; вернуть завершённую фразу или None."""
    for _ in range(2):  # речь (>= min_speech_chunks)
        fsm.handle_chunk(_chunk(client))
    for _ in range(2):  # тишина до конца фразы
        phrase = fsm.handle_chunk(_chunk(client))
        if phrase is not None:
            return phrase
    return None


def _run_handle_phrase(client: ModuleType, phrase, fsm, poster) -> None:
    client.handle_phrase(
        phrase,
        fsm=fsm,
        benchmark=True,
        server_url="http://testserver/api/v1/benchmark/transcribe",
        use_wav=False,
        timeout=5.0,
        poster=poster,
    )


# ---------------------------------------------------------------------------
# Сценарий 1: одна фраза → ровно один HTTP-запрос
# ---------------------------------------------------------------------------


def test_one_phrase_exactly_one_request(client, tmp_path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)  # изолируем debug_last_record.wav/.ulaw
    emit = EmitCollector()
    vad = FakeVAD([True, True, False, False])
    fsm = _make_fsm(client, vad, emit)

    phrase = _feed_phrase(client, fsm, vad)
    assert phrase is not None
    assert fsm.state is client.ClientState.PROCESSING

    poster = FakePoster()
    _run_handle_phrase(client, phrase, fsm, poster)

    assert len(poster.calls) == 1
    assert fsm.state is client.ClientState.IDLE


# ---------------------------------------------------------------------------
# Сценарий 2: VAD-события во время долгого HTTP-запроса игнорируются
# ---------------------------------------------------------------------------


def test_vad_events_ignored_during_long_request(client, tmp_path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    emit = EmitCollector()
    vad = FakeVAD([True, True, False, False])
    fsm = _make_fsm(client, vad, emit)

    phrase = _feed_phrase(client, fsm, vad)
    assert phrase is not None
    assert fsm.state is client.ClientState.PROCESSING
    calls_before = vad.calls

    poster = FakePoster(delay=0.3)  # «долгий» benchmark-запрос
    worker = threading.Thread(
        target=_run_handle_phrase, args=(client, phrase, fsm, poster), daemon=True
    )
    worker.start()

    # Пока запрос выполняется, в микрофон сыплются новые «речевые» чанки.
    fed = 0
    while worker.is_alive() and fed < 5:
        result = fsm.handle_chunk(_chunk(client))
        assert result is None  # новая фраза начаться не может
        fed += 1
        time.sleep(0.03)
    worker.join(timeout=5)

    assert not worker.is_alive()
    assert fed == 5  # чанки действительно поступали, пока запрос висел
    assert vad.calls == calls_before  # VAD в PROCESSING не вызывался ни разу
    assert len(poster.calls) == 1  # и новый benchmark-запрос не отправлен
    assert fsm.state is client.ClientState.IDLE

    # Ни одного нового «ОБНАРУЖЕНА РЕЧЬ» после ухода в PROCESSING.
    pause_idx = emit.lines.index("\n⏸️ ПАУЗА. Отправка на распознавание...")
    assert not any(
        "ОБНАРУЖЕНА РЕЧЬ" in line for line in emit.lines[pause_idx + 1 :]
    )


# ---------------------------------------------------------------------------
# Сценарий 3: после завершения benchmark можно начать следующую фразу
# ---------------------------------------------------------------------------


def test_second_phrase_allowed_after_first_completes(
    client, tmp_path, monkeypatch
) -> None:
    monkeypatch.chdir(tmp_path)
    emit = EmitCollector()
    # Ровно на две фразы: speech, speech, silence, silence — дважды.
    vad = FakeVAD([True, True, False, False, True, True, False, False])
    fsm = _make_fsm(client, vad, emit)

    phrase1 = _feed_phrase(client, fsm, vad)
    assert phrase1 is not None
    poster = FakePoster()
    _run_handle_phrase(client, phrase1, fsm, poster)
    assert len(poster.calls) == 1
    assert fsm.state is client.ClientState.IDLE

    phrase2 = _feed_phrase(client, fsm, vad)
    assert phrase2 is not None  # FSM снова слушает микрофон
    _run_handle_phrase(client, phrase2, fsm, poster)
    assert len(poster.calls) == 2


# ---------------------------------------------------------------------------
# Сценарий 4: ошибка HTTP не оставляет клиент в PROCESSING навсегда
# ---------------------------------------------------------------------------


def test_http_error_returns_client_to_idle(client, tmp_path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    emit = EmitCollector()
    vad = FakeVAD([True, True, False, False, True, True, False, False])
    fsm = _make_fsm(client, vad, emit)

    phrase1 = _feed_phrase(client, fsm, vad)
    assert phrase1 is not None
    poster = FakePoster(fail=True)  # requests.exceptions.Timeout
    _run_handle_phrase(client, phrase1, fsm, poster)
    assert fsm.state is client.ClientState.IDLE  # release() в finally

    # После ошибки клиент снова работает: вторая фраза отправляется.
    phrase2 = _feed_phrase(client, fsm, vad)
    assert phrase2 is not None
    poster_ok = FakePoster()
    _run_handle_phrase(client, phrase2, fsm, poster_ok)
    assert len(poster_ok.calls) == 1
    assert fsm.state is client.ClientState.IDLE


def test_connection_error_still_releases(client, tmp_path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    emit = EmitCollector()
    vad = FakeVAD([True, True, False, False])
    fsm = _make_fsm(client, vad, emit)

    phrase = _feed_phrase(client, fsm, vad)
    assert phrase is not None
    # ConnectionError → send_to_server делает sys.exit(1); SystemExit
    # пробрасывается, но release() в finally всё равно вернёт FSM в IDLE.
    with pytest.raises(SystemExit):
        _run_handle_phrase(client, phrase, fsm, FakePoster(exit_on_call=True))
    assert fsm.state is client.ClientState.IDLE


# ---------------------------------------------------------------------------
# Защита от ложных срабатываний: короткий шум отбрасывается
# ---------------------------------------------------------------------------


def test_short_noise_is_discarded(client, tmp_path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    emit = EmitCollector()
    # Один «речевой» чанк (щелчок) и тишина — меньше min_speech_chunks=2.
    vad = FakeVAD([True, False, False])
    fsm = _make_fsm(client, vad, emit)

    result = None
    for _ in range(3):
        result = fsm.handle_chunk(_chunk(client))
    assert result is None  # фраза не отправляется
    assert fsm.state is client.ClientState.IDLE
    assert any("Слишком короткий" in line for line in emit.lines)

    # Критерий — именно длительность РЕЧИ: длинная тишина не «дотягивает»
    # короткий щелчок до минимальной фразы.
    vad2 = FakeVAD([True] + [False] * 20)
    fsm2 = _make_fsm(client, vad2, emit)
    for _ in range(21):
        result = fsm2.handle_chunk(_chunk(client))
    assert result is None
    assert fsm2.state is client.ClientState.IDLE


def test_release_is_idempotent(client) -> None:
    vad = FakeVAD([])
    fsm = _make_fsm(client, vad, EmitCollector())

    # release() из состояния IDLE безопасен и не трогает VAD.
    fsm.release()
    fsm.release()
    assert fsm.state is client.ClientState.IDLE
    assert vad.calls == 0


# ---------------------------------------------------------------------------
# Серверная часть: release production-модели и ленивый reload
# ---------------------------------------------------------------------------


class _UnloadableASR:
    def __init__(self, name: str = "gigaam_v3_rnnt") -> None:
        self.name = name
        self.unloaded = False

    def load(self) -> None:
        pass

    def unload(self) -> None:
        self.unloaded = True


class _CountingFactory:
    """Фабрика, считающая загрузки (для проверки отсутствия двойной загрузки)."""

    def __init__(self, load_delay: float = 0.0) -> None:
        self.load_calls = 0
        self._load_delay = load_delay
        self._lock = threading.Lock()

    def load(self):
        with self._lock:
            self.load_calls += 1
        if self._load_delay:
            time.sleep(self._load_delay)
        return _UnloadableASR(), 123.0


def test_release_disabled_by_default(monkeypatch) -> None:
    import app.main as main_module

    monkeypatch.setattr(
        main_module.settings, "STT_BENCHMARK_RELEASES_PRODUCTION", False
    )
    models = main_module.ModelState()
    models.stt = main_module.STTClient(_UnloadableASR())

    assert main_module._release_stt_for_benchmark(models) is False
    assert models.stt is not None  # модель не тронута
    assert not models.stt.model.unloaded


def test_release_unloads_production_model(monkeypatch) -> None:
    import app.main as main_module

    monkeypatch.setattr(main_module.settings, "STT_BENCHMARK_RELEASES_PRODUCTION", True)
    models = main_module.ModelState()
    asr = _UnloadableASR()
    models.stt = main_module.STTClient(asr)

    assert main_module._release_stt_for_benchmark(models) is True
    assert models.stt is None  # ссылка снята — модель не удерживается в RAM
    assert asr.unloaded  # и выгружена через adapter.unload()


def test_reload_is_thread_safe_single_load() -> None:
    import app.main as main_module

    models = main_module.ModelState()
    factory = _CountingFactory(load_delay=0.05)
    models.stt_factory = factory

    results: list = []
    threads = [
        threading.Thread(target=lambda: results.append(main_module._reload_stt(models)))
        for _ in range(4)
    ]
    for t in threads:
        t.start()
    for t in threads:
        t.join(timeout=5)

    assert factory.load_calls == 1  # двойной загрузки нет
    assert len(results) == 4
    assert all(r is results[0] for r in results)  # все получили один клиент
    assert models.stt is results[0]


def test_reload_returns_none_without_factory() -> None:
    import app.main as main_module

    models = main_module.ModelState()
    models.stt_factory = None
    assert main_module._reload_stt(models) is None
    assert models.stt is None
