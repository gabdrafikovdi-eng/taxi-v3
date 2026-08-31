#!/usr/bin/env python3
"""Контрольный эксперимент: production-path vs benchmark-path на ОДНОМ WAV.

Воспроизводит на серверном коде оба пути один-в-один:

* production  — ``STTClient.transcribe(pcm, 16000)`` после ``_decode_pcm16``
  (ровно то, что делает ``POST /api/v1/transcribe`` после VAD);
* benchmark   — ``BenchmarkRunner.run(tmp_wav, sample_count)`` после
  ``_decode_pcm16`` (ровно то, что делает ``POST /api/v1/benchmark/transcribe``).

Фазы (по умолчанию все):

  1. fixture   — декодирование исходного WAV ровно как на сервере
                 (``_wav_to_pcm16``) + диагностика WAV (Этап 2);
  2. prod      — изолированный production-прогон каждой модели
                 (load → STTClient.transcribe → unload);
  3. bench     — полный benchmark-прогон всех моделей (Вариант B,
                 production-модель не загружена);
  4. bench2    — повторный benchmark-прогон (дрейф после других моделей,
                 Этап 6);
  5. bench-prod-loaded — benchmark при загруженной production-модели
                 (Вариант A, Этап 7);

Пример:
    .venv/bin/python experiments/prod_vs_benchmark.py \
        --wav debug_last_record.wav --out experiments/result.json
"""

from __future__ import annotations

import argparse
import hashlib
import io
import json
import sys
import tempfile
import time
import wave
from pathlib import Path

import numpy as np
import soundfile as sf

from app.audio import converter
from app.stt.benchmark import BenchmarkRunner
from app.stt.client import STTClient
from app.stt.factory import STTModelFactory
from app.stt.registry import BENCHMARK_MODEL_KEYS

BASE_DIR = Path(__file__).resolve().parent.parent


def log(msg: str) -> None:
    print(f"[{time.strftime('%H:%M:%S')}] {msg}", flush=True)


# ---------------------------------------------------------------------------
# Точная копия серверного декодирования (app.main._wav_to_pcm16)
# ---------------------------------------------------------------------------


def decode_like_server(wav_bytes: bytes) -> tuple[bytes, int]:
    with io.BytesIO(wav_bytes) as sock:
        data, sample_rate = sf.read(sock, dtype="int16", always_2d=False)
    if data.ndim > 1:
        data = np.mean(data, axis=1).astype(np.int16)
    pcm = data.astype(np.int16).tobytes()
    if sample_rate != converter.TARGET_SAMPLE_RATE:
        pcm = converter.resample(pcm, sample_rate, converter.TARGET_SAMPLE_RATE)
        sample_rate = converter.TARGET_SAMPLE_RATE
    return pcm, int(sample_rate)


def wav_info(wav_bytes: bytes) -> dict:
    with wave.open(io.BytesIO(wav_bytes)) as w:
        return {
            "framerate": w.getframerate(),
            "channels": w.getnchannels(),
            "sampwidth": w.getsampwidth(),
            "nframes": w.getnframes(),
            "duration_ms": round(w.getnframes() / w.getframerate() * 1000, 1),
        }


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()[:16]


# ---------------------------------------------------------------------------
# Два пути инференса
# ---------------------------------------------------------------------------


def production_run(
    key: str, pcm_bytes: bytes, sample_rate: int, device: str
) -> str:
    """Production-путь: load → STTClient.transcribe → unload (как endpoint)."""
    factory = STTModelFactory(model_key=key, device=device)
    adapter = factory.build(key)
    adapter.load()
    try:
        stt = STTClient(adapter)
        text, _ms = stt.transcribe(pcm_bytes, sample_rate)
        return text
    finally:
        adapter.unload()


def benchmark_run(
    keys: tuple[str, ...], pcm_bytes: bytes, device: str
) -> dict[str, str]:
    """Benchmark-путь: temp wav → BenchmarkRunner.run (как endpoint)."""
    factory = STTModelFactory(model_key=keys[0], device=device)
    wav_bytes = converter.to_wav(pcm_bytes, converter.TARGET_SAMPLE_RATE)
    sample_count = len(pcm_bytes) // 2
    runner = BenchmarkRunner(factory, model_keys=keys)
    with tempfile.NamedTemporaryFile(suffix=".wav", prefix="bench_") as tmp:
        tmp.write(wav_bytes)
        tmp.flush()
        results = runner.run(tmp.name, sample_count)
    return {r.model: (r.text if r.success else f"<FAIL: {r.error}>") for r in results}



# ---------------------------------------------------------------------------
# Фазы
# ---------------------------------------------------------------------------


def phase_fixture(wav_path: Path) -> tuple[bytes, bytes]:
    """Этап 2: доказать, что production input == benchmark input."""
    raw = wav_path.read_bytes()
    info_src = wav_info(raw)
    log(f"исходный WAV: {info_src}, sha256={sha256(raw)}")

    pcm, sample_rate = decode_like_server(raw)
    prod_wav = converter.to_wav(pcm, converter.TARGET_SAMPLE_RATE)  # путь STTClient
    bench_wav = converter.to_wav(pcm, converter.TARGET_SAMPLE_RATE)  # путь benchmark

    log(f"production wav: {wav_info(prod_wav)} sha256={sha256(prod_wav)}")
    log(f"benchmark  wav: {wav_info(bench_wav)} sha256={sha256(bench_wav)}")
    assert prod_wav == bench_wav, "WAV production != WAV benchmark!"
    log("OK: production input == benchmark input (байт в байт)")
    assert sample_rate == converter.TARGET_SAMPLE_RATE
    peak = int(np.abs(np.frombuffer(pcm, dtype=np.int16)).max())
    log(f"pcm: {len(pcm) // 2} samples, peak={peak} (STTClient._SILENCE_PEAK=200)")
    return pcm, bench_wav


# ---------------------------------------------------------------------------
# µ-law сценарий: точная реплика обоих endpoint'ов для телефонного входа
# ---------------------------------------------------------------------------


def make_ulaw_like_client(wav_path: Path) -> bytes:
    """Точная копия client.convert_to_telephony_format (без отладочных файлов)."""
    with io.BytesIO(wav_path.read_bytes()) as f:
        data, sr = sf.read(f, dtype="int16", always_2d=False)
    if data.ndim > 1:
        data = np.mean(data, axis=1).astype(np.int16)
    target_len = max(1, round(len(data) * 8000 / sr))
    x_old = np.linspace(0.0, 1.0, num=len(data), endpoint=False)
    x_new = np.linspace(0.0, 1.0, num=target_len, endpoint=False)
    audio_8k = np.interp(x_new, x_old, data.astype(np.float32))
    audio_8k = np.clip(audio_8k, -32768, 32767).astype(np.int16)
    buf = io.BytesIO()
    with sf.SoundFile(
        buf, mode="w", samplerate=8000, channels=1, format="RAW", subtype="ULAW"
    ) as f:
        f.write(audio_8k)
    return buf.getvalue()


def phase_ulaw(wav_path: Path, keys: tuple[str, ...], device: str) -> dict[str, object]:
    """µ-law вход (режим клиента по умолчанию): production vs benchmark.

    Benchmark прогоняется через НАСТОЯЩИЙ endpoint (TestClient с реальным
    lifespan: production-модель + Silero VAD + TTS). Production-бейзлайн —
    тот же код, что выполняет ``POST /api/v1/transcribe`` после VAD.
    """
    from fastapi.testclient import TestClient

    import app.main as main_module

    ulaw = make_ulaw_like_client(wav_path)
    log(f"ulaw bytes: {len(ulaw)} (как отправляет test_telephony_mic.py по умолчанию)")

    # Точно как в endpoint'ах: _decode_pcm16 для µ-law → (pcm_8k, 8000).
    from app.main import _decode_pcm16

    pcm_bytes, sample_rate = _decode_pcm16(ulaw, "audio/x-mulaw")
    log(f"endpoint decode: sample_rate={sample_rate}, samples={len(pcm_bytes) // 2}")

    report: dict[str, object] = {"ulaw_sample_rate_in": sample_rate}

    # Production-бейзлайн: изолированный прогон каждой модели через STTClient.
    prod_texts: dict[str, str] = {}
    for key in keys:
        log(f"ULAW-PROD {key}: load → transcribe → unload")
        prod_texts[key] = production_run(key, pcm_bytes, sample_rate, device)
        log(f"ULAW-PROD {key}: '{prod_texts[key]}'")
    report["ulaw_prod"] = prod_texts

    def post_benchmark(tc: TestClient) -> dict[str, str]:
        response = tc.post(
            "/api/v1/benchmark/transcribe",
            files={"audio": ("g711.ulaw", ulaw, "audio/x-mulaw")},
        )
        assert response.status_code == 200, response.text
        payload = response.json()
        assert payload["speech_detected"] is True
        out: dict[str, str] = {}
        for r in payload["results"]:
            assert r["success"], f"{r['model']}: {r.get('error')}"
            out[r["model"]] = r["text"]
        return out

    with TestClient(main_module.app) as tc:
        report["health_start"] = tc.get("/health").json()
        log(f"health: {report['health_start']}")

        # Вариант A: production-модель загружена и НЕ выгружается (Этап 7).
        main_module.settings.STT_BENCHMARK_RELEASES_PRODUCTION = False
        log("Вариант A: benchmark при загруженной production-модели")
        texts_a = post_benchmark(tc)
        for key, text in texts_a.items():
            log(f"BENCH-A {key}: '{text}'")
        report["ulaw_bench_prod_loaded"] = texts_a

        # Вариант B: benchmark выгружает production-модель перед прогоном.
        main_module.settings.STT_BENCHMARK_RELEASES_PRODUCTION = True
        log("Вариант B: benchmark с выгрузкой production-модели")
        texts_b = post_benchmark(tc)
        for key, text in texts_b.items():
            log(f"BENCH-B {key}: '{text}'")
        report["ulaw_bench_released"] = texts_b

        # Повторный прогон: дрейф после других моделей (Этап 6).
        log("Повторный benchmark (дрейф?)")
        texts_b2 = post_benchmark(tc)
        report["ulaw_bench_repeat"] = texts_b2

        # Production-ручка после benchmark: ленивая перезагрузка работает.
        main_module.settings.STT_BENCHMARK_RELEASES_PRODUCTION = True
        prod_resp = tc.post(
            "/api/v1/transcribe",
            files={"audio": ("g711.ulaw", ulaw, "audio/x-mulaw")},
        )
        assert prod_resp.status_code == 200
        report["ulaw_prod_endpoint_after_bench"] = prod_resp.json()["text"]
        log(f"PROD endpoint после benchmark: '{report['ulaw_prod_endpoint_after_bench']}'")
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--wav", type=Path, default=BASE_DIR / "debug_last_record.wav")
    parser.add_argument(
        "--out", type=Path, default=BASE_DIR / "experiments" / "result.json"
    )
    parser.add_argument("--device", default="cpu")
    parser.add_argument(
        "--models",
        default=",".join(BENCHMARK_MODEL_KEYS),
        help="Подмножество моделей для быстрого прогона",
    )
    parser.add_argument("--skip-prod", action="store_true")
    parser.add_argument("--skip-bench2", action="store_true")
    parser.add_argument(
        "--with-prod-loaded",
        action="store_true",
        help="Вариант A (Этап 7): benchmark при загруженной production-модели",
    )
    parser.add_argument(
        "--ulaw",
        action="store_true",
        help="Только µ-law сценарий: реплика обоих endpoint'ов для телефонного входа",
    )
    args = parser.parse_args()

    keys = tuple(k.strip() for k in args.models.split(",") if k.strip())

    if args.ulaw:
        ulaw_report = phase_ulaw(args.wav, keys, args.device)
        prod = ulaw_report["ulaw_prod"]
        bench_a = ulaw_report["ulaw_bench_prod_loaded"]
        bench_b = ulaw_report["ulaw_bench_released"]
        bench_b2 = ulaw_report["ulaw_bench_repeat"]
        print("\n" + "=" * 76)
        print("µ-LAW СЦЕНАРИЙ (вход как у test_telephony_mic.py по умолчанию)")
        print("=" * 76)
        mismatches = 0
        for key in keys:
            p, ba, bb, bb2 = prod[key], bench_a[key], bench_b[key], bench_b2[key]
            ok = p == ba == bb == bb2
            if not ok:
                mismatches += 1
            mark = "OK " if ok else "DIFF"
            print(f"{mark} prod='{p}' | benchA='{ba}' | benchB='{bb}' | repeat='{bb2}'")
        print(
            f"production endpoint после benchmark: "
            f"'{ulaw_report['ulaw_prod_endpoint_after_bench']}'"
        )
        print("=" * 76)
        print(f"Несовпадений prod vs benchmark: {mismatches} из {len(keys)}")
        out = args.out.with_name("ulaw_" + args.out.name)
        out.write_text(json.dumps(ulaw_report, ensure_ascii=False, indent=2))
        log(f"отчёт сохранён: {out}")
        return 1 if mismatches else 0

    log(f"модели: {keys}")

    pcm, _bench_wav = phase_fixture(args.wav)
    report: dict[str, object] = {"models": list(keys)}

    # Фаза prod: изолированный production-прогон каждой модели.
    if not args.skip_prod:
        prod_texts: dict[str, str] = {}
        for key in keys:
            log(f"PROD {key}: load → transcribe → unload")
            started = time.perf_counter()
            prod_texts[key] = production_run(key, pcm, args.device)
            log(f"PROD {key}: '{prod_texts[key]}' ({time.perf_counter() - started:.1f}s)")
        report["prod"] = prod_texts

    # Фаза bench (Вариант B: production-модель не загружена).
    log("BENCH: полный последовательный прогон (Вариант B)")
    started = time.perf_counter()
    bench_texts = benchmark_run(keys, pcm, args.device)
    log(f"BENCH занял {time.perf_counter() - started:.1f}s")
    for key, text in bench_texts.items():
        log(f"BENCH {key}: '{text}'")
    report["bench"] = bench_texts

    # Фаза bench2: повторный прогон (дрейф после других моделей, Этап 6).
    if not args.skip_bench2:
        log("BENCH2: повторный последовательный прогон (дрейф?)")
        bench2_texts = benchmark_run(keys, pcm, args.device)
        for key, text in bench2_texts.items():
            log(f"BENCH2 {key}: '{text}'")
        report["bench2"] = bench2_texts

    # Фаза Вариант A: benchmark при загруженной production-модели (Этап 7).
    if args.with_prod_loaded:
        env_model = "gigaam_v3_e2e_rnnt"
        log(f"Вариант A: держим загруженной production-модель {env_model}")
        factory = STTModelFactory(model_key=env_model, device=args.device)
        prod_adapter = factory.build(env_model)
        prod_adapter.load()
        try:
            bench_a_texts = benchmark_run(keys, pcm, args.device)
            for key, text in bench_a_texts.items():
                log(f"BENCH-A {key}: '{text}'")
            report["bench_prod_loaded"] = bench_a_texts
        finally:
            prod_adapter.unload()

    # Сводка.
    print("\n" + "=" * 76)
    print("СВОДКА (ОДИН И ТОТ ЖЕ WAV)")
    print("=" * 76)
    prod = report.get("prod")
    bench = report.get("bench", {})
    bench2 = report.get("bench2")
    bench_a = report.get("bench_prod_loaded")
    mismatches = 0
    for key in keys:
        p = (prod or {}).get(key, "?")
        b = bench.get(key, "?")
        line = f"{'OK ' if p == b else 'DIFF'} prod='{p}' bench='{b}'"
        if bench2 is not None:
            line += f" bench2='{bench2.get(key, '?')}'"
        if bench_a is not None:
            line += f" benchA='{bench_a.get(key, '?')}'"
        if p != b:
            mismatches += 1
        print(line)
    print("=" * 76)
    print(f"Несовпадений prod vs bench: {mismatches} из {len(keys)}")

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, ensure_ascii=False, indent=2))
    log(f"отчёт сохранён: {args.out}")
    return 1 if mismatches else 0


if __name__ == "__main__":
    sys.exit(main())
