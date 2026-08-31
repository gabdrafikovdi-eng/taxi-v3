"""Опциональный parity-тест на РЕАЛЬНЫХ моделях GigaAM (Этап 5/12).

Проверяет главный критерий готовности:

    ОДИН И ТОТ ЖЕ WAV
        → production-путь (STTClient.transcribe)
        → benchmark-путь (BenchmarkRunner)
    = одинаковый текст для каждой модели.

Запускается только при ``SPEECH_SERVICE_REAL_MODELS=1`` (нужны чекпоинты
в ~/.cache/gigaam и ffmpeg): обычный ``pytest tests -q`` остаётся быстрым.

    SPEECH_SERVICE_REAL_MODELS=1 pytest tests/test_real_models_parity.py -q
"""

from __future__ import annotations

import os
from pathlib import Path

import pytest

from app.audio import converter
from app.stt.benchmark import BenchmarkRunner
from app.stt.client import STTClient
from app.stt.factory import STTModelFactory

# Минимальный набор из Этапа 5 (расширяется через env, полностью — "all").
REAL_MODELS = os.environ.get("SPEECH_SERVICE_REAL_MODEL_KEYS", ",".join([
    "gigaam_v2_ctc",
    "gigaam_v2_rnnt",
    "gigaam_v3_ctc",
    "gigaam_v3_rnnt",
]))
if REAL_MODELS.strip().lower() == "all":
    from app.stt.registry import BENCHMARK_MODEL_KEYS

    REAL_MODELS = ",".join(BENCHMARK_MODEL_KEYS)

#: Детерминированная фикстура: реальная запись клиента (48 кГц, фраза).
FIXTURE_WAV = Path(__file__).resolve().parent.parent / "debug_last_record.wav"


def _decode_fixture() -> bytes:
    """PCM16 16 кГц из фикстуры — ровно серверный путь _wav_to_pcm16."""
    import io

    import numpy as np
    import soundfile as sf

    with io.BytesIO(FIXTURE_WAV.read_bytes()) as f:
        data, sample_rate = sf.read(f, dtype="int16", always_2d=False)
    if data.ndim > 1:
        data = np.mean(data, axis=1).astype(np.int16)
    pcm = data.astype(np.int16).tobytes()
    if sample_rate != converter.TARGET_SAMPLE_RATE:
        pcm = converter.resample(pcm, sample_rate, converter.TARGET_SAMPLE_RATE)
    return pcm


def _production_text(key: str, pcm: bytes, device: str) -> str:
    """Production-путь: load → STTClient.transcribe → unload."""
    factory = STTModelFactory(model_key=key, device=device)
    adapter = factory.build(key)
    adapter.load()
    try:
        stt = STTClient(adapter)
        text, _ = stt.transcribe(pcm, converter.TARGET_SAMPLE_RATE)
        return text
    finally:
        adapter.unload()


def _benchmark_texts(keys: tuple[str, ...], pcm: bytes, device: str) -> dict[str, str]:
    """Benchmark-путь: temp WAV → BenchmarkRunner (как endpoint)."""
    import tempfile

    factory = STTModelFactory(model_key=keys[0], device=device)
    wav_bytes = converter.to_wav(pcm, converter.TARGET_SAMPLE_RATE)
    runner = BenchmarkRunner(factory, model_keys=keys)
    with tempfile.NamedTemporaryFile(suffix=".wav", prefix="parity_") as tmp:
        tmp.write(wav_bytes)
        tmp.flush()
        results = runner.run(tmp.name, len(pcm) // 2)
    out: dict[str, str] = {}
    for r in results:
        assert r.success, f"модель {r.model} упала: {r.error}"
        out[r.model] = r.text
    return out


@pytest.mark.skipif(
    os.environ.get("SPEECH_SERVICE_REAL_MODELS") != "1",
    reason="Реальные веса GigaAM: включается SPEECH_SERVICE_REAL_MODELS=1",
)
@pytest.mark.skipif(not FIXTURE_WAV.exists(), reason="Нет фикстуры debug_last_record.wav")
def test_production_and_benchmark_same_text_on_real_models() -> None:
    device = "cpu"
    pcm = _decode_fixture()
    assert len(pcm) > 0

    # Production: каждая модель ИЗОЛИРОВАННО (load → infer → unload).
    prod = {
        key: _production_text(key, pcm, device)
        for key in REAL_MODELS.split(",") if key.strip()
    }

    # Benchmark: последовательный прогон тех же моделей на том же PCM.
    bench = _benchmark_texts(tuple(k for k in REAL_MODELS.split(",") if k.strip()), pcm, device)

    for key, text in prod.items():
        assert bench[key] == text, (
            f"production и benchmark дали разный текст для {key}: "
            f"prod='{text}' bench='{bench[key]}'"
        )
