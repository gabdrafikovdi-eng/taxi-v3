"""Тесты единого реестра ASR-моделей."""

from __future__ import annotations

import pytest

from app.stt.registry import (
    BENCHMARK_MODEL_KEYS,
    LEGACY_ALIASES,
    MODEL_REGISTRY,
    canonical_model_key,
    get_model_spec,
    is_ssl_spec,
)

EXPECTED_ORDER = [
    "gigaam_v2_ctc",
    "gigaam_v2_rnnt",
    "gigaam_v3_ctc",
    "gigaam_v3_rnnt",
    "gigaam_v3_e2e_ctc",
    "gigaam_v3_e2e_rnnt",
    "gigaam_multilingual_ctc",
    "gigaam_multilingual_large_ctc",
]


def test_registry_has_expected_models_in_deterministic_order() -> None:
    assert list(MODEL_REGISTRY) == EXPECTED_ORDER
    assert BENCHMARK_MODEL_KEYS == tuple(EXPECTED_ORDER)


def test_registry_has_no_ssl_or_emo() -> None:
    # SSL/Emo-модели не являются ASR и не должны попадать в транскрипцию.
    for spec in MODEL_REGISTRY.values():
        assert spec.arch not in {"ssl", "emo"}
        assert not is_ssl_spec(spec)


def test_spec_fields_are_consistent() -> None:
    for key, spec in MODEL_REGISTRY.items():
        assert spec.key == key
        assert spec.gigaam_model
        assert spec.family in {"v2", "v3", "multilingual"}
        assert spec.min_gigaam_version >= (0, 1)


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("gigaam_v3_rnnt", "gigaam_v3_rnnt"),
        ("gigaam-v3-rnnt", "gigaam_v3_rnnt"),
        ("GIGAAM_V3_RNNT", "gigaam_v3_rnnt"),
        ("gigaam-v2-ctc", "gigaam_v2_ctc"),
        ("rnnt", "gigaam_v2_rnnt"),
        ("ctc", "gigaam_v2_ctc"),
        ("v3_ctc", "gigaam_v3_ctc"),
        ("v3_e2e_ctc", "gigaam_v3_e2e_ctc"),
        ("v3_e2e_rnnt", "gigaam_v3_e2e_rnnt"),
        ("e2e_ctc", "gigaam_v3_e2e_ctc"),
        ("multilingual_ctc", "gigaam_multilingual_ctc"),
        ("multilingual_large_ctc", "gigaam_multilingual_large_ctc"),
    ],
)
def test_canonical_model_key_normalization(raw: str, expected: str) -> None:
    assert canonical_model_key(raw) == expected


def test_legacy_aliases_resolve() -> None:
    for alias, canonical in LEGACY_ALIASES.items():
        assert canonical_model_key(alias) == canonical


@pytest.mark.parametrize("bad", ["ssl", "emo", "v1_ctc", "unknown", ""])
def test_unknown_model_raises(bad: str) -> None:
    with pytest.raises(ValueError):
        canonical_model_key(bad)


def test_get_model_spec() -> None:
    spec = get_model_spec("gigaam-v3-rnnt")
    assert spec.gigaam_model == "v3_rnnt"
    assert spec.name == "GigaAM v3 RNNT"


def test_ssl_spec_detection() -> None:
    # ssl-спека не существует в реестре, но утилита корректно помечает её.
    assert is_ssl_spec(get_model_spec("gigaam_v2_ctc")) is False
    assert is_ssl_spec(MODEL_REGISTRY["gigaam_v2_ctc"]) is False