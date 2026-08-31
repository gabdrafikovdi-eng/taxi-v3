"""Пакет STT: распознавание речи (GigaAM v2/v3/multilingual) + VAD (Silero)."""

from app.stt.benchmark import BenchmarkResult, BenchmarkRunner
from app.stt.client import STTClient
from app.stt.factory import STTModelFactory
from app.stt.registry import (
    BENCHMARK_MODEL_KEYS,
    MODEL_REGISTRY,
    ModelSpec,
)
from app.stt.vad import VAD

__all__ = [
    "BENCHMARK_MODEL_KEYS",
    "MODEL_REGISTRY",
    "BenchmarkResult",
    "BenchmarkRunner",
    "ModelSpec",
    "STTClient",
    "STTModelFactory",
    "VAD",
]