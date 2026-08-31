"""Единый ASR Protocol.

Любая модель распознавания (GigaAM v2/v3/multilingual или будущая замена)
должна реализовывать этот интерфейс. ``STTClient``, фабрика и benchmark
работают только с этим протоколом и не знают внутреннего API конкретной
библиотеки.

Вся работа с аудио идёт через путь к WAV-файлу (16 кГц / mono / PCM16) —
так же, как ожидает ``gigaam``. Напрямую возвращается текст (``str``);
внутренние типы результата (``TranscriptionResult`` в gigaam>=0.2 или
``list[dict]`` в gigaam==0.1) нормализуются адаптером.
"""

from __future__ import annotations

from typing import Protocol


class ASRModel(Protocol):
    """Интерфейс ASR-модели для speech-service."""

    @property
    def name(self) -> str:
        """Канонический ключ модели (например ``gigaam_v3_rnnt``)."""

    def load(self) -> None:
        """Загрузить модель в память. Идемпотентна."""

    def transcribe(self, wav_path: str) -> str:
        """Распознать короткий WAV (до ~25 сек) и вернуть текст."""

    def transcribe_audio(self, wav_path: str, sample_count: int | None = None) -> str:
        """Распознать WAV любой длины, при необходимости через longform."""

    def unload(self) -> None:
        """Освободить модель из памяти (ссылки + подходящая очистка backend)."""