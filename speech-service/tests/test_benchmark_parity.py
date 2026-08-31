"""Регрессионные тесты паритета production vs benchmark (Этап 12).

Ловят конкретный найденный дефект: benchmark-ручка упаковывала µ-law/A-law
PCM (8 кГц) в WAV с заголовком 16 кГц БЕЗ ресемплинга — модели получали
речь с 2× скоростью/высотой и выдавали мусор, хотя production-ручка
ресемплировала корректно внутри ``STTClient.transcribe``.

Ключевой инвариант: ОДИН и тот же вход → ОДИН и тот же WAV в руках модели
в обоих путях (production == benchmark, байт в байт).

Все модели — фейки (SpyAdapter записывает WAV, который ему передали);
реальные веса не загружаются. Реальный parity-тест на весах GigaAM —
в ``test_real_models_parity.py`` (опциональный).
"""

from __future__ import annotations

import io
import wave
from typing import Any

import numpy as np
import pytest
import soundfile as sf
from fastapi.testclient import TestClient

import app.main as main_module
from app.audio import converter
from app.stt.client import STTClient
from app.stt.registry import BENCHMARK_MODEL_KEYS


# ---------------------------------------------------------------------------
# Фейки: SpyAdapter запоминает WAV, который ему передали на распознавание
# ---------------------------------------------------------------------------


class SpyAdapter:
    """Фейковый ASR-адаптер: пишет, какой WAV-файл ему отдали."""

    def __init__(self, key: str, captures: list[dict[str, Any]] | None = None) -> None:
        self.name = key
        self._captures = captures if captures is not None else []
        self.load_calls = 0
        self.unload_calls = 0
        self.unloaded = False

    def load(self) -> None:
        self.load_calls += 1
        self.unloaded = False

    def unload(self) -> None:
        self.unload_calls += 1
        self.unloaded = True

    def transcribe(self, wav_path: str) -> str:
        return f"text {self.name}"

    def transcribe_audio(self, wav_path: str, sample_count: int | None = None) -> str:
        with open(wav_path, "rb") as f:
            wav_data = f.read()
        with wave.open(wav_path, "rb") as wf:
            self._captures.append(
                {
                    "model": self.name,
                    "wav_bytes": wav_data,
                    "framerate": wf.getframerate(),
                    "channels": wf.getnchannels(),
                    "sampwidth": wf.getsampwidth(),
                    "nframes": wf.getnframes(),
                    "sample_count_arg": sample_count,
                }
            )
        return f"text {self.name}"


class SpyFactory:
    """Фейковая фабрика: новый SpyAdapter на каждый build (как production).

    ``load()`` повторяет контракт ``STTModelFactory.load`` — он используется
    ленивой перезагрузкой production-модели после benchmark-release.
    """

    def __init__(self) -> None:
        self.captures: list[dict[str, Any]] = []
        self.adapters: list[SpyAdapter] = []
        self.built_keys: list[str] = []

    def build(self, key: str) -> SpyAdapter:
        self.built_keys.append(key)
        adapter = SpyAdapter(key, self.captures)
        self.adapters.append(adapter)
        return adapter

    def load(self, model_key: str | None = None) -> tuple[SpyAdapter, float]:
        adapter = self.build(model_key or "gigaam_v3_rnnt")
        adapter.load()
        return adapter, 0.0


class FakeVAD:
    def is_speech(self, audio_chunk: bytes, sample_rate: int = 16000) -> bool:
        return True


class FakeTTS:
    async def synthesize(self, text: str, speaker: str | None = None) -> bytes:
        return b"RIFF-fake-wav-data"


def _make_spy_loaders(factory: SpyFactory):
    """Лоадеры lifespan с общей SpyFactory (production-адаптер — 'gigaam_v3_rnnt')."""

    def fake_load_stt(models: main_module.ModelState) -> None:
        production = SpyAdapter("gigaam_v3_rnnt", factory.captures)
        models.stt = STTClient(production)
        models.stt_factory = factory
        models.stt_model_name = production.name
        models.stt_device = "cpu"

    return fake_load_stt


@pytest.fixture()
def factory() -> SpyFactory:
    return SpyFactory()


@pytest.fixture()
def client(factory: SpyFactory, monkeypatch: pytest.MonkeyPatch):
    # Явно выключаем release production-модели: в .env разработчика может
    # быть true — тесты состояния (Вариант A/B) должны быть детерминированы.
    monkeypatch.setattr(
        main_module.settings, "STT_BENCHMARK_RELEASES_PRODUCTION", False
    )
    monkeypatch.setattr(main_module, "_load_stt", _make_spy_loaders(factory))
    monkeypatch.setattr(
        main_module, "_load_vad", lambda models: setattr(models, "vad", FakeVAD())
    )
    monkeypatch.setattr(
        main_module, "_load_tts", lambda models: setattr(models, "tts", FakeTTS())
    )
    with TestClient(main_module.app) as test_client:
        yield test_client


# ---------------------------------------------------------------------------
# Аудио-фабрики (телефонный вход, как у test_telephony_mic.py по умолчанию)
# ---------------------------------------------------------------------------


def _sine_pcm16(duration: float, sample_rate: int) -> bytes:
    t = np.linspace(0.0, duration, int(sample_rate * duration), endpoint=False)
    samples = (np.sin(2 * np.pi * 440 * t) * 3000).astype(np.int16)
    return samples.tobytes()


def _g711_bytes(subtype: str, duration: float = 0.4, sample_rate: int = 8000) -> bytes:
    """G.711 µ-law/A-law 8 кГц — реальный путь телефонного клиента."""
    buffer = io.BytesIO()
    samples = np.frombuffer(_sine_pcm16(duration, sample_rate), dtype=np.int16)
    with sf.SoundFile(
        buffer, mode="w", samplerate=sample_rate, channels=1, format="RAW",
        subtype=subtype,
    ) as f:
        f.write(samples)
    return buffer.getvalue()


def _mulaw_bytes() -> bytes:
    return _g711_bytes("ULAW")


def _alaw_bytes() -> bytes:
    return _g711_bytes("ALAW")



# ---------------------------------------------------------------------------
# Test 1: production и benchmark получают байт-в-байт одинаковый WAV
# ---------------------------------------------------------------------------


def test_production_and_benchmark_receive_identical_wav(
    client: TestClient, factory: SpyFactory
) -> None:
    """Один µ-law payload → одинаковый WAV у модели в обоих путях (Этап 2/5)."""
    payload = _mulaw_bytes()

    bench_response = client.post(
        "/api/v1/benchmark/transcribe",
        files={"audio": ("g711.ulaw", payload, "audio/x-mulaw")},
    )
    assert bench_response.status_code == 200
    assert len(factory.captures) == len(BENCHMARK_MODEL_KEYS)
    bench_wav = factory.captures[0]["wav_bytes"]

    factory.captures.clear()
    prod_response = client.post(
        "/api/v1/transcribe",
        files={"audio": ("g711.ulaw", payload, "audio/x-mulaw")},
    )
    assert prod_response.status_code == 200
    assert len(factory.captures) == 1
    prod_wav = factory.captures[0]["wav_bytes"]

    # Главный инвариант: одинаковый вход → одинаковый WAV в обоих путях.
    assert prod_wav == bench_wav
    # И это честный 16 кГц WAV (не 8 кГц семплы с заголовком 16 кГц).
    with wave.open(io.BytesIO(prod_wav)) as wf:
        assert wf.getframerate() == converter.TARGET_SAMPLE_RATE
        assert wf.getnchannels() == 1
        assert wf.getsampwidth() == 2


def test_benchmark_resamples_telephony_inputs_to_16k(
    client: TestClient, factory: SpyFactory
) -> None:
    """µ-law и A-law: benchmark обязан ресемплировать до 16 кГц (регрессия)."""
    for payload, content_type, decode in (
        (_mulaw_bytes(), "audio/x-mulaw", converter.mulaw_to_pcm16),
        (_alaw_bytes(), "audio/x-alaw", converter.alaw_to_pcm16),
    ):
        factory.captures.clear()
        response = client.post(
            "/api/v1/benchmark/transcribe",
            files={"audio": ("g711", payload, content_type)},
        )
        assert response.status_code == 200
        assert len(factory.captures) == len(BENCHMARK_MODEL_KEYS)

        pcm_8k, source_rate = decode(payload)
        expected_pcm = converter.resample(
            pcm_8k, source_rate, converter.TARGET_SAMPLE_RATE
        )
        expected_nframes = len(expected_pcm) // 2

        for capture in factory.captures:
            # Заголовок и фактическое число семплов согласованы: 16 кГц.
            assert capture["framerate"] == converter.TARGET_SAMPLE_RATE
            assert capture["nframes"] == expected_nframes
            # sample_count, переданный адаптеру, согласован с WAV (longform).
            assert capture["sample_count_arg"] == expected_nframes
            # WAV байт-в-байт равен тому, что production-путь даёт STTClient.
            assert capture["wav_bytes"] == converter.to_wav(
                expected_pcm, converter.TARGET_SAMPLE_RATE
            )


def test_benchmark_reports_target_sample_rate(client: TestClient) -> None:
    """Метаданные ответа: sample_rate = 16 кГц (частота, отданная моделям)."""
    response = client.post(
        "/api/v1/benchmark/transcribe",
        files={"audio": ("g711.ulaw", _mulaw_bytes(), "audio/x-mulaw")},
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["sample_rate"] == converter.TARGET_SAMPLE_RATE
    assert payload["duration_ms"] > 0


# ---------------------------------------------------------------------------
# Test 2: lifecycle — свежий адаптер на модель, unload после прогона
# ---------------------------------------------------------------------------




# ---------------------------------------------------------------------------
# Test 3: результат benchmark не зависит от загруженной production-модели
# ---------------------------------------------------------------------------


def _benchmark_texts(client: TestClient) -> dict[str, str]:
    response = client.post(
        "/api/v1/benchmark/transcribe",
        files={"audio": ("g711.ulaw", _mulaw_bytes(), "audio/x-mulaw")},
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["speech_detected"] is True
    return {r["model"]: r["text"] for r in payload["results"]}


def test_benchmark_result_independent_of_production_model(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Вариант B (production выгружена) == Вариант A (production загружена)."""
    models = client.app.state.models

    # Вариант B: production-модель не загружена (только factory).
    models.stt = None
    bench_without_prod = _benchmark_texts(client)

    # Вариант A: production-модель загружена заранее.
    production = SpyAdapter("gigaam_v3_rnnt")
    models.stt = STTClient(production)
    bench_with_prod = _benchmark_texts(client)

    assert bench_with_prod == bench_without_prod
    # Production-модель при выключенном release остаётся загруженной.
    assert models.stt is not None
    assert production.unload_calls == 0


def test_benchmark_with_release_production_still_correct_and_reloads(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    """STT_BENCHMARK_RELEASES_PRODUCTION=true: production выгружается,
    benchmark не меняется, production перезагружается лениво."""
    monkeypatch.setattr(
        main_module.settings, "STT_BENCHMARK_RELEASES_PRODUCTION", True
    )
    models = client.app.state.models
    assert models.stt is not None

    bench_texts = _benchmark_texts(client)
    assert len(bench_texts) == len(BENCHMARK_MODEL_KEYS)

    # Production-модель выгружена benchmark'ом...
    assert models.stt is None
    health = client.get("/health").json()
    assert health["stt_loaded"] is False
    assert health["stt_reloadable"] is True

    # ...и лениво перезагружается следующим production-запросом.
    prod_response = client.post(
        "/api/v1/transcribe",
        files={"audio": ("g711.ulaw", _mulaw_bytes(), "audio/x-mulaw")},
    )
    assert prod_response.status_code == 200
    assert client.get("/health").json()["stt_loaded"] is True


# ---------------------------------------------------------------------------
# Test 4: последовательный прогон A → unload → B → unload → A не меняет A
# ---------------------------------------------------------------------------


class _SequenceFactory:
    """Фабрика, запоминающая порядок сборки/выгрузки адаптеров."""

    def __init__(self) -> None:
        self.built: list[str] = []
        self.unloaded: list[str] = []

    def build(self, key: str) -> _SequenceAdapter:
        self.built.append(key)
        return _SequenceAdapter(key, self.unloaded)


class _SequenceAdapter:
    """Детерминированный адаптер: текст зависит только от имени модели."""

    def __init__(self, key: str, unloaded: list[str]) -> None:
        self.name = key
        self._unloaded = unloaded
        self.unload_calls = 0

    def load(self) -> None:
        return None

    def transcribe_audio(self, wav_path: str, sample_count: int | None = None) -> str:
        return f"text {self.name}"

    def unload(self) -> None:
        self.unload_calls += 1
        self._unloaded.append(self.name)


def test_sequential_a_b_a_produces_same_result_for_a() -> None:
    from app.stt.benchmark import BenchmarkRunner

    factory = _SequenceFactory()
    runner = BenchmarkRunner(factory=factory, model_keys=("a", "b", "a"))
    results = runner.run(wav_path="fake.wav", sample_count=16000)

    # A выполняется дважды (до и после B) с одинаковым результатом.
    assert results[0].model == results[-1].model == "a"
    assert results[0].text == results[-1].text == "text a"
    assert all(r.success for r in results)

    # На каждый прогон — свежий адаптер, выгруженный сразу после инференса.
    assert factory.built == ["a", "b", "a"]


# ---------------------------------------------------------------------------
# Test 5: unload базового адаптера полностью освобождает модель
# ---------------------------------------------------------------------------


class _FakeGigaAMModule:
    """Фейковый модуль gigaam: load_model создаёт новый объект каждый раз."""

    def __init__(self) -> None:
        self.instances: list[_FakeGigaAMModel] = []

    def load_model(self, name: str, **kwargs: object) -> _FakeGigaAMModel:
        model = _FakeGigaAMModel(name)
        self.instances.append(model)
        return model


class _FakeGigaAMModel:
    """Фейковая модель gigaam: transcribe есть, счётчик live-ссылок общий."""

    def __init__(self, name: str) -> None:
        self.name = name

    def transcribe(self, wav_path: str) -> str:
        return "ok"


def test_base_adapter_unload_drops_model_and_allows_reload(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """unload(): ссылка на модель сброшена; повторный load() работает (Этап 4)."""
    from app.stt.models import build_adapter
    from app.stt.registry import get_model_spec

    fake_module = _FakeGigaAMModule()
    adapter = build_adapter(get_model_spec("gigaam_v3_rnnt"), "cpu")
    monkeypatch.setattr(adapter, "_import_gigaam", lambda: fake_module)

    adapter.load()
    assert adapter.loaded is True
    assert adapter.transcribe("x.wav") == "ok"
    first_model = adapter._require_loaded()

    adapter.unload()
    assert adapter.loaded is False
    with pytest.raises(RuntimeError, match="не загружена"):
        adapter.transcribe("x.wav")

    # unload идемпотентен; повторная загрузка создаёт НОВЫЙ объект модели.
    adapter.unload()
    adapter.load()
    assert adapter.loaded is True
    second_model = adapter._require_loaded()
    assert second_model is not first_model
    assert adapter.transcribe("x.wav") == "ok"


def test_benchmark_lifecycle_fresh_adapter_and_unload(
    client: TestClient, factory: SpyFactory
) -> None:
    """Каждая модель: build → load → infer → unload (Этап 4/6)."""
    response = client.post(
        "/api/v1/benchmark/transcribe",
        files={"audio": ("g711.ulaw", _mulaw_bytes(), "audio/x-mulaw")},
    )
    assert response.status_code == 200
    results = response.json()["results"]

    # На каждую модель — ровно один СВЕЖИЙ адаптер (никаких shared instance).
    assert factory.built_keys == list(BENCHMARK_MODEL_KEYS)
    assert len(factory.adapters) == len(BENCHMARK_MODEL_KEYS)
    assert len({id(a) for a in factory.adapters}) == len(BENCHMARK_MODEL_KEYS)

    for adapter in factory.adapters:
        assert adapter.load_calls == 1
        # Модель выгружена сразу после своего инференса.
        assert adapter.unload_calls == 1
        assert adapter.unloaded

    # Все модели отработали успешно и в порядке реестра.
    assert [r["model"] for r in results] == list(BENCHMARK_MODEL_KEYS)
    assert all(r["success"] for r in results)
