"""Тесты последовательного benchmark: падение одной модели не останавливает прогон."""

from __future__ import annotations

from app.stt.benchmark import BenchmarkResult, BenchmarkRunner


class FakeAdapter:
    """Фейковый адаптер ASR (имитирует ASRModel)."""

    def __init__(
        self,
        key: str,
        fail_load: bool = False,
        fail_transcribe: bool = False,
    ) -> None:
        self.name = key
        self.fail_load = fail_load
        self.fail_transcribe = fail_transcribe
        self.unloaded = False

    def load(self) -> None:
        if self.fail_load:
            raise RuntimeError(f"load boom {self.name}")

    def transcribe(self, wav_path: str) -> str:
        if self.fail_transcribe:
            raise ValueError(f"transcribe boom {self.name}")
        return f"text {self.name}"

    def transcribe_audio(self, wav_path: str, sample_count: int | None = None) -> str:
        return self.transcribe(wav_path)

    def unload(self) -> None:
        self.unloaded = True


class FakeFactory:
    def __init__(self, specs: dict[str, dict]) -> None:
        self._specs = specs
        self.adapters: list[FakeAdapter] = []

    def build(self, key: str) -> FakeAdapter:
        spec = self._specs[key]
        adapter = FakeAdapter(key, **spec)
        self.adapters.append(adapter)
        return adapter


def _run(keys: tuple[str, ...], specs: dict[str, dict]) -> tuple[list[BenchmarkResult], FakeFactory]:
    factory = FakeFactory(specs)
    runner = BenchmarkRunner(factory=factory, model_keys=keys)
    results = runner.run(wav_path="fake.wav", sample_count=16000)
    return results, factory


def test_run_ok_all_models() -> None:
    keys = ("m1", "m2", "m3")
    results, factory = _run(keys, {k: {} for k in keys})

    assert [r.model for r in results] == list(keys)
    assert all(r.success for r in results)
    assert all(r.text == f"text {k}" for r, k in zip(results, keys))
    assert all(r.load_time_ms >= 0 for r in results)
    assert all(r.inference_time_ms >= 0 for r in results)
    assert all(r.total_time_ms == r.load_time_ms + r.inference_time_ms for r in results)
    # Каждая модель после прогона выгружена.
    assert all(a.unloaded for a in factory.adapters)


def test_one_model_failure_does_not_stop_benchmark() -> None:
    keys = ("ok1", "bad_load", "ok2", "bad_transcribe", "ok3")
    specs = {
        "ok1": {},
        "bad_load": {"fail_load": True},
        "ok2": {},
        "bad_transcribe": {"fail_transcribe": True},
        "ok3": {},
    }
    results, factory = _run(keys, specs)

    assert [r.model for r in results] == list(keys)
    assert [r.success for r in results] == [True, False, True, False, True]
    assert results[1].error == "load boom bad_load"
    assert results[3].error == "transcribe boom bad_transcribe"
    # Ошибки без stack trace.
    assert all("Traceback" not in (r.error or "") for r in results if not r.success)
    # Даже упавшие модели выгружаются.
    assert all(a.unloaded for a in factory.adapters)


def test_result_schema() -> None:
    ok = BenchmarkResult(
        model="gigaam_v3_rnnt",
        text="привет",
        load_time_ms=100.0,
        inference_time_ms=50.0,
        total_time_ms=150.0,
        success=True,
    )
    payload = ok.to_dict()
    assert payload["model"] == "gigaam_v3_rnnt"
    assert payload["text"] == "привет"
    assert payload["load_time_ms"] == 100.0
    assert payload["inference_time_ms"] == 50.0
    assert payload["total_time_ms"] == 150.0
    assert payload["success"] is True
    assert "error" not in payload

    bad = BenchmarkResult(model="x", success=False, error="boom")
    bad_payload = bad.to_dict()
    assert bad_payload["success"] is False
    assert bad_payload["error"] == "boom"
    assert bad_payload["text"] == ""


def test_deterministic_order_matches_registry() -> None:
    from app.stt.registry import BENCHMARK_MODEL_KEYS

    keys = BENCHMARK_MODEL_KEYS
    results, _ = _run(keys, {k: {} for k in keys})
    assert [r.model for r in results] == list(keys)