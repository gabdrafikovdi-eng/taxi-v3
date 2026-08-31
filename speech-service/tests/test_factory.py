"""Тесты фабрики STT-моделей: selection через registry, версия gigaam, device."""

from __future__ import annotations

import sys
import tempfile

import pytest
import torch

from app.stt.factory import STTModelFactory, pick_stt_device
from app.stt.models.gigaam_v2 import GigaAMV2Adapter
from app.stt.models.gigaam_v3 import GigaAMV3Adapter
from app.stt.models.gigaam_multilingual import GigaAMMultilingualAdapter
from app.stt.registry import canonical_model_key, get_model_spec


class FakeGigaAMModel:
    """Фейковая gigaam-модель (имитирует API gigaam 0.2.0)."""

    def __init__(self, name: str) -> None:
        self.name = name

    def transcribe(self, wav_path: str) -> str:
        return f"текст {self.name}"


class FakeGigaAM:
    """Фейковый модуль gigaam (подставляется в sys.modules)."""

    def __init__(self) -> None:
        self.loaded: list[str] = []

    def load_model(self, name: str, **kwargs: object) -> FakeGigaAMModel:
        self.loaded.append(name)
        return FakeGigaAMModel(name)


def _install_fake_gigaam(monkeypatch: pytest.MonkeyPatch) -> FakeGigaAM:
    fake = FakeGigaAM()
    monkeypatch.setitem(sys.modules, "gigaam", fake)
    # База читает версию через importlib.metadata — подменяем напрямую.
    monkeypatch.setattr(
        "app.stt.models.base.gigaam_dist_version", lambda: (0, 2)
    )
    return fake


def test_adapter_classes_for_families() -> None:
    assert GigaAMV2Adapter.family == "v2"
    assert GigaAMV3Adapter.family == "v3"
    assert GigaAMMultilingualAdapter.family == "multilingual"


def test_factory_builds_correct_adapter() -> None:
    factory = STTModelFactory(model_key="gigaam_v2_ctc", device="cpu")
    adapter = factory.build()
    assert isinstance(adapter, GigaAMV2Adapter)
    assert adapter.spec == get_model_spec("gigaam_v2_ctc")

    factory_v3 = STTModelFactory(model_key="gigaam_v3_rnnt", device="cpu")
    assert isinstance(factory_v3.build(), GigaAMV3Adapter)

    factory_ml = STTModelFactory(model_key="gigaam_multilingual_large_ctc", device="cpu")
    assert isinstance(factory_ml.build(), GigaAMMultilingualAdapter)


def test_factory_load_returns_loaded_adapter(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fake = _install_fake_gigaam(monkeypatch)
    factory = STTModelFactory(model_key="gigaam_v3_rnnt", device="cpu")
    adapter, load_time_ms = factory.load()

    assert adapter.loaded
    assert load_time_ms >= 0
    assert fake.loaded == ["v3_rnnt"]
    assert adapter.name == "gigaam_v3_rnnt"

    with tempfile.NamedTemporaryFile(suffix=".wav") as tmp:
        text = adapter.transcribe_audio(tmp.name, sample_count=16000)
        assert text == "текст v3_rnnt"


def test_factory_version_gate_rejects_old_gigaam(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _install_fake_gigaam(monkeypatch)
    # v3/multilingual требуют gigaam>=0.2, а у нас "старая" 0.1.
    monkeypatch.setattr(
        "app.stt.models.base.gigaam_dist_version", lambda: (0, 1)
    )
    factory = STTModelFactory(model_key="gigaam_v3_rnnt", device="cpu")
    with pytest.raises(RuntimeError, match="gigaam"):
        factory.load()

    # v2 работает и на gigaam 0.1.
    factory_v2 = STTModelFactory(model_key="gigaam_v2_ctc", device="cpu")
    adapter, _ = factory_v2.load()
    assert adapter.loaded


def test_factory_rejects_unknown_key() -> None:
    with pytest.raises(ValueError):
        STTModelFactory(model_key="not-a-model", device="cpu")


def test_pick_stt_device(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(torch.cuda, "is_available", lambda: False)
    assert pick_stt_device("cpu", True) == "cpu"
    assert pick_stt_device(" mps ", True) == "mps"
    # CUDA нет -> fallback на CPU
    assert pick_stt_device("cuda:0", True) == "cpu"
    with pytest.raises(RuntimeError):
        pick_stt_device("cuda:0", False)


def test_pick_stt_device_cuda(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(torch.cuda, "is_available", lambda: True)
    assert pick_stt_device("cuda:0", True) == "cuda:0"
    assert pick_stt_device("cuda:0", False) == "cuda:0"


def test_canonical_key_via_factory() -> None:
    factory = STTModelFactory(model_key="gigaam-v3-rnnt", device="cpu")
    assert factory.model_key == "gigaam_v3_rnnt"
    assert canonical_model_key("gigaam-v3-rnnt") == "gigaam_v3_rnnt"