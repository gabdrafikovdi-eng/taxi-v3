"""Единый реестр ASR-моделей speech-service.

Здесь определяется ВЕСЬ список доступных для распознавания моделей и
порядок их запуска в benchmark. Нигде в FastAPI endpoints / factory /
benchmark не должно быть ``if/elif`` по отдельным моделям — только этот
реестр.

Типы моделей (по факту API библиотеки gigaam v0.2.0, см. также README):

* GigaAM v2   — ``v2_ctc``, ``v2_rnnt`` (работают и в gigaam 0.1.0, и 0.2.0);
* GigaAM v3   — ``v3_ctc``, ``v3_rnnt``, ``v3_e2e_ctc``, ``v3_e2e_rnnt``;
* Multilingual — ``multilingual_ctc``, ``multilingual_large_ctc``.

SSL/Emo-модели НЕ являются ASR (у них нет ``transcribe``), поэтому в
реестр транскрипции они не включаются.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Final

_AVAILABLE_KEYS_HINT = (
    "gigaam_v2_ctc, gigaam_v2_rnnt, gigaam_v3_ctc, gigaam_v3_rnnt, "
    "gigaam_v3_e2e_ctc, gigaam_v3_e2e_rnnt, gigaam_multilingual_ctc, "
    "gigaam_multilingual_large_ctc"
)


@dataclass(frozen=True)
class ModelSpec:
    """Описание одной ASR-модели реестра.

    ``key`` — канонический ключ (используется в ``STT_MODEL`` и в ответах API).
    ``gigaam_model`` — идентификатор, который понимает ``gigaam.load_model``.
    ``min_gigaam_version`` — минимальная версия библиотеки gigaam, в которой
    появляется модель (v2 есть в 0.1.0, v3/multilingual — только в 0.2.0+).
    """

    key: str
    name: str
    family: str
    arch: str
    gigaam_model: str
    min_gigaam_version: tuple[int, int]


# Порядок словаря = детерминированный порядок прогона в benchmark.
MODEL_REGISTRY: dict[str, ModelSpec] = {
    "gigaam_v2_ctc": ModelSpec(
        key="gigaam_v2_ctc",
        name="GigaAM v2 CTC",
        family="v2",
        arch="ctc",
        gigaam_model="v2_ctc",
        min_gigaam_version=(0, 1),
    ),
    "gigaam_v2_rnnt": ModelSpec(
        key="gigaam_v2_rnnt",
        name="GigaAM v2 RNNT",
        family="v2",
        arch="rnnt",
        gigaam_model="v2_rnnt",
        min_gigaam_version=(0, 1),
    ),
    "gigaam_v3_ctc": ModelSpec(
        key="gigaam_v3_ctc",
        name="GigaAM v3 CTC",
        family="v3",
        arch="ctc",
        gigaam_model="v3_ctc",
        min_gigaam_version=(0, 2),
    ),
    "gigaam_v3_rnnt": ModelSpec(
        key="gigaam_v3_rnnt",
        name="GigaAM v3 RNNT",
        family="v3",
        arch="rnnt",
        gigaam_model="v3_rnnt",
        min_gigaam_version=(0, 2),
    ),
    "gigaam_v3_e2e_ctc": ModelSpec(
        key="gigaam_v3_e2e_ctc",
        name="GigaAM v3 E2E CTC",
        family="v3",
        arch="e2e_ctc",
        gigaam_model="v3_e2e_ctc",
        min_gigaam_version=(0, 2),
    ),
    "gigaam_v3_e2e_rnnt": ModelSpec(
        key="gigaam_v3_e2e_rnnt",
        name="GigaAM v3 E2E RNNT",
        family="v3",
        arch="e2e_rnnt",
        gigaam_model="v3_e2e_rnnt",
        min_gigaam_version=(0, 2),
    ),
    "gigaam_multilingual_ctc": ModelSpec(
        key="gigaam_multilingual_ctc",
        name="GigaAM Multilingual CTC",
        family="multilingual",
        arch="ctc",
        gigaam_model="multilingual_ctc",
        min_gigaam_version=(0, 2),
    ),
    "gigaam_multilingual_large_ctc": ModelSpec(
        key="gigaam_multilingual_large_ctc",
        name="GigaAM Multilingual Large CTC",
        family="multilingual",
        arch="ctc",
        gigaam_model="multilingual_large_ctc",
        min_gigaam_version=(0, 2),
    ),
}

#: Детерминированный порядок моделей для benchmark (порядок объявления выше).
BENCHMARK_MODEL_KEYS: Final[tuple[str, ...]] = tuple(MODEL_REGISTRY)

#: Устаревшие алиасы (обратная совместимость со старыми значениями STT_MODEL
#: вида ``rnnt`` / ``ctc`` / ``v3_rnnt`` / ``gigaam-v2-ctc`` и т.п.).
LEGACY_ALIASES: dict[str, str] = {
    "ctc": "gigaam_v2_ctc",
    "rnnt": "gigaam_v2_rnnt",
    "v2_ctc": "gigaam_v2_ctc",
    "v2_rnnt": "gigaam_v2_rnnt",
    "v3_ctc": "gigaam_v3_ctc",
    "v3_rnnt": "gigaam_v3_rnnt",
    "e2e_ctc": "gigaam_v3_e2e_ctc",
    "e2e_rnnt": "gigaam_v3_e2e_rnnt",
    "v3_e2e_ctc": "gigaam_v3_e2e_ctc",
    "v3_e2e_rnnt": "gigaam_v3_e2e_rnnt",
    "multilingual_ctc": "gigaam_multilingual_ctc",
    "multilingual_large_ctc": "gigaam_multilingual_large_ctc",
}


def canonical_model_key(raw: str) -> str:
    """Привести любое имя модели к каноническому ключу реестра.

    Принимает ``gigaam_v3_rnnt``, ``gigaam-v3-rnnt``, ``v3_rnnt``,
    ``rnnt`` и т.п. Для неизвестного имени бросает ``ValueError``.
    """
    key = raw.strip().lower().replace("-", "_")
    if key.startswith("gigaam_"):
        key = key[len("gigaam_") :]
    if key in MODEL_REGISTRY:
        return key
    canonical = LEGACY_ALIASES.get(key)
    if canonical is not None and canonical in MODEL_REGISTRY:
        return canonical
    raise ValueError(
        f"Неизвестная STT-модель '{raw}'. Доступные модели: {_AVAILABLE_KEYS_HINT}"
    )


def get_model_spec(model_key: str) -> ModelSpec:
    """Вернуть ModelSpec по каноническому ключу (с нормализацией имени)."""
    return MODEL_REGISTRY[canonical_model_key(model_key)]


def is_ssl_spec(spec: ModelSpec) -> bool:
    """SSL/Emo-модели не являются ASR и не участвуют в транскрипции."""
    return spec.arch in {"ssl", "emo"}