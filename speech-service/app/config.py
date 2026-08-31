"""Конфигурация микросервиса speech-service (pydantic-settings).

Все настройки читаются из переменных окружения или файла ``.env``.
Имена полей совпадают с именами переменных окружения (case-sensitive).
"""

from __future__ import annotations

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Настройки сервиса: STT (GigaAM v2/v3/multilingual), TTS (edge-tts), сеть и логирование."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=True,
    )

    # STT (GigaAM)
    STT_MODEL: str = Field(
        default="gigaam_v3_rnnt",
        description="Канонический ключ модели из реестра, например gigaam_v3_rnnt",
    )
    STT_LANGUAGE: str = Field(
        default="ru",
        description="Язык распознавания (метаданные; gigaam не принимает language в transcribe)",
    )
    STT_DEVICE: str = Field(
        default="cpu",
        description="Устройство для GigaAM: 'cuda:0' на GPU-сервере, 'cpu' на Mac",
    )
    STT_FALLBACK_TO_CPU: bool = Field(
        default=True,
        description="Если CUDA недоступна — загружать GigaAM на CPU",
    )
    STT_BENCHMARK_RELEASES_PRODUCTION: bool = Field(
        default=False,
        description=(
            "Выгружать production-модель STT на время benchmark"
            " (экономия RAM на машинах с 8 GB unified memory;"
            " следующий production-запрос перезагрузит модель лениво)"
        ),
    )

    # TTS (edge-tts, облачный Microsoft)
    TTS_VOICE: str = Field(
        default="ru-RU-DmitryNeural",
        description="Голос edge-tts (например, ru-RU-DmitryNeural или ru-RU-SvetlanaNeural)",
    )

    # Общие настройки сервиса
    MAX_AUDIO_DURATION_SEC: int = Field(
        default=30, description="Максимальная длительность аудио на STT (сек)"
    )
    LOG_LEVEL: str = Field(default="INFO", description="Уровень логирования")
    HOST: str = Field(default="0.0.0.0", description="Адрес для uvicorn")
    PORT: int = Field(default=8001, description="Порт для uvicorn")


settings = Settings()