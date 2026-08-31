"""API-тесты FastAPI-приложения (health, transcribe, benchmark, TTS).

Все модели/сервисы заменяются фейками — реальные веса не загружаются.
"""

from __future__ import annotations

import io

import numpy as np
import pytest
import soundfile as sf
from fastapi.testclient import TestClient

import app.main as main_module
from app.audio import converter
from app.stt.client import STTClient
from app.stt.registry import BENCHMARK_MODEL_KEYS


# ---------------------------------------------------------------------------
# Фейки
# ---------------------------------------------------------------------------


class FakeASR:
    """Фейковая ASR-модель."""

    def __init__(self, name: str = "gigaam_v3_rnnt") -> None:
        self.name = name

    def load(self) -> None:
        pass

    def transcribe(self, wav_path: str) -> str:
        return "Мне нужна машина на улицу Ленина"

    def transcribe_audio(self, wav_path: str, sample_count: int | None = None) -> str:
        return self.transcribe(wav_path)

    def unload(self) -> None:
        pass


class FakeVAD:
    def __init__(self, speech: bool = True) -> None:
        self._speech = speech

    def is_speech(self, audio_chunk: bytes, sample_rate: int = 16000) -> bool:
        return self._speech


class FakeTTS:
    async def synthesize(self, text: str, speaker: str | None = None) -> bytes:
        return b"RIFF-fake-wav-data"


class FakeBenchmarkAdapter:
    def __init__(self, key: str, broken: str | None = None) -> None:
        self.name = key
        self._broken = broken

    def load(self) -> None:
        if self._broken == "load":
            raise RuntimeError(f"load boom {self.name}")

    def transcribe(self, wav_path: str) -> str:
        if self._broken == "transcribe":
            raise ValueError(f"infer boom {self.name}")
        return f"text {self.name}"

    def transcribe_audio(self, wav_path: str, sample_count: int | None = None) -> str:
        return self.transcribe(wav_path)

    def unload(self) -> None:
        pass


class FakeBenchmarkFactory:
    def __init__(self, broken: str | None = None) -> None:
        self._broken = broken

    def build(self, key: str) -> FakeBenchmarkAdapter:
        if self._broken and key == self._broken:
            return FakeBenchmarkAdapter(key, broken="load")
        return FakeBenchmarkAdapter(key)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


def _fake_load_stt(models: main_module.ModelState, broken: str | None = None) -> None:
    models.stt = STTClient(FakeASR())
    models.stt_factory = FakeBenchmarkFactory(broken=broken)
    models.stt_model_name = "gigaam_v3_rnnt"
    models.stt_device = "cpu"


def _fake_load_vad(models: main_module.ModelState) -> None:
    models.vad = FakeVAD()


def _fake_load_tts(models: main_module.ModelState) -> None:
    models.tts = FakeTTS()


@pytest.fixture()
def client(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr(main_module, "_load_stt", _fake_load_stt)
    monkeypatch.setattr(main_module, "_load_vad", _fake_load_vad)
    monkeypatch.setattr(main_module, "_load_tts", _fake_load_tts)
    with TestClient(main_module.app) as test_client:
        yield test_client


# ---------------------------------------------------------------------------
# Аудио-фабрики
# ---------------------------------------------------------------------------


def _pcm16(duration: float = 0.4, sample_rate: int = 16000) -> bytes:
    t = np.linspace(0.0, duration, int(sample_rate * duration), endpoint=False)
    samples = (np.sin(2 * np.pi * 440 * t) * 3000).astype(np.int16)
    return samples.tobytes()


def wav_bytes(duration: float = 0.4) -> bytes:
    return converter.to_wav(_pcm16(duration), converter.TARGET_SAMPLE_RATE)


def ulaw_bytes(duration: float = 0.4, sample_rate: int = 8000) -> bytes:
    t = np.linspace(0.0, duration, int(sample_rate * duration), endpoint=False)
    samples = (np.sin(2 * np.pi * 440 * t) * 3000).astype(np.int16)
    buffer = io.BytesIO()
    with sf.SoundFile(
        buffer, mode="w", samplerate=sample_rate, channels=1,
        format="RAW", subtype="ULAW",
    ) as f:
        f.write(samples)
    return buffer.getvalue()


# ---------------------------------------------------------------------------
# Health
# ---------------------------------------------------------------------------


def test_health(client: TestClient) -> None:
    response = client.get("/health")
    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "ok"
    assert payload["stt_loaded"] is True
    assert payload["tts_loaded"] is True
    assert payload["stt_model"] == "gigaam_v3_rnnt"
    assert payload["device"] == "cpu"
    assert payload["available_benchmark_models"] == list(BENCHMARK_MODEL_KEYS)
    assert len(payload["available_benchmark_models"]) == 8


# ---------------------------------------------------------------------------
# Production transcribe
# ---------------------------------------------------------------------------


def test_transcribe_wav(client: TestClient) -> None:
    response = client.post(
        "/api/v1/transcribe",
        files={"audio": ("speech.wav", wav_bytes(), "audio/wav")},
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["text"] == "Мне нужна машина на улицу Ленина"
    assert payload["duration_ms"] > 0
    assert payload["sample_rate"] == 16000
    # Обратная совместимость: старые ключи на месте, новые добавлены.
    assert payload["model"] == "gigaam_v3_rnnt"
    assert isinstance(payload["inference_time_ms"], (int, float))


def test_transcribe_mulaw(client: TestClient) -> None:
    response = client.post(
        "/api/v1/transcribe",
        files={"audio": ("g711.ulaw", ulaw_bytes(), "audio/x-mulaw")},
    )
    assert response.status_code == 200
    assert response.json()["text"] == "Мне нужна машина на улицу Ленина"


def test_transcribe_empty_audio(client: TestClient) -> None:
    response = client.post(
        "/api/v1/transcribe",
        files={"audio": ("empty.wav", b"", "audio/wav")},
    )
    assert response.status_code == 400


def test_transcribe_no_speech_returns_empty(client: TestClient) -> None:
    # VAD видит тишину -> текст пустой, инференс не запускается.
    models = client.app.state.models
    models.vad = FakeVAD(speech=False)
    response = client.post(
        "/api/v1/transcribe",
        files={"audio": ("speech.wav", wav_bytes(), "audio/wav")},
    )
    assert response.status_code == 200
    assert response.json()["text"] == ""


# ---------------------------------------------------------------------------
# Benchmark
# ---------------------------------------------------------------------------


def test_benchmark_transcribe(client: TestClient) -> None:
    response = client.post(
        "/api/v1/benchmark/transcribe",
        files={"audio": ("speech.wav", wav_bytes(), "audio/wav")},
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["speech_detected"] is True
    assert payload["duration_ms"] > 0
    assert payload["sample_rate"] == 16000
    results = payload["results"]
    assert [r["model"] for r in results] == list(BENCHMARK_MODEL_KEYS)
    assert all(r["success"] for r in results)
    for result in results:
        assert result["text"] == f"text {result['model']}"
        assert isinstance(result["load_time_ms"], (int, float))
        assert isinstance(result["inference_time_ms"], (int, float))
        assert isinstance(result["total_time_ms"], (int, float))


def test_benchmark_one_model_failure_reported(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    # Пересобираем lifecycle с фабрикой, у которой падает загрузка одной модели.
    monkeypatch.setattr(
        main_module,
        "_load_stt",
        lambda m: _fake_load_stt(m, broken="gigaam_v3_rnnt"),
    )
    with TestClient(main_module.app) as test_client:
        response = test_client.post(
            "/api/v1/benchmark/transcribe",
            files={"audio": ("speech.wav", wav_bytes(), "audio/wav")},
        )
        assert response.status_code == 200
        results = response.json()["results"]
        assert len(results) == len(BENCHMARK_MODEL_KEYS)
        failed = [r for r in results if not r["success"]]
        assert len(failed) == 1
        assert failed[0]["model"] == "gigaam_v3_rnnt"
        assert "boom" in failed[0]["error"]
        assert "Traceback" not in failed[0]["error"]
        # Остальные модели отработали.
        assert sum(1 for r in results if r["success"]) == len(BENCHMARK_MODEL_KEYS) - 1


def test_benchmark_no_speech_empty_results(client: TestClient) -> None:
    models = client.app.state.models
    models.vad = FakeVAD(speech=False)
    response = client.post(
        "/api/v1/benchmark/transcribe",
        files={"audio": ("speech.wav", wav_bytes(), "audio/wav")},
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["speech_detected"] is False
    assert payload["results"] == []


# ---------------------------------------------------------------------------
# TTS / stream
# ---------------------------------------------------------------------------


def test_synthesize(client: TestClient) -> None:
    response = client.post(
        "/api/v1/synthesize",
        json={"text": "Куда вас подать?", "speaker": "baya"},
    )
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("audio/wav")
    assert len(response.content) > 0


def test_synthesize_empty_text(client: TestClient) -> None:
    response = client.post(
        "/api/v1/synthesize",
        json={"text": "   "},
    )
    assert response.status_code == 400


def test_transcribe_stream(client: TestClient) -> None:
    # Endpoint принимает multipart/form-data (поле audio), как и
    # production-ручка; клиенты шлют сырой PCM16 в поле audio.
    response = client.post(
        "/api/v1/transcribe/stream",
        files={
            "audio": ("speech.pcm", _pcm16(), "application/octet-stream")
        },
    )
    assert response.status_code == 200
    assert response.json()["text"] == "Мне нужна машина на улицу Ленина"
    assert response.json()["is_final"] is True