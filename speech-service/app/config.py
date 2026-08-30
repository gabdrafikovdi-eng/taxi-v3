"""Конфигурация микросервиса speech-service (pydantic-settings).

Все настройки читаются из переменных окружения или файла ``.env``.
Имена полей совпадают с именами переменных окружения (case-sensitive).
"""

from __future__ import annotations

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Настройки сервиса: STT (GigaAM), TTS (Silero), сеть и логирование."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=True,
    )

    # STT (GigaAM)
    STT_MODEL: str = Field(
        default="gigaam-v3-rnnt",
        description="Имя модели GigaAM, например gigaam-v3-rnnt",
    )
    STT_DEVICE: str = Field(
        default="cuda:0",
        description="Устройство для GigaAM: 'cuda:0' на GPU-сервере, 'cpu' на Mac",
    )
    STT_FALLBACK_TO_CPU: bool = Field(
        default=True,
        description="Если CUDA недоступна — загружать GigaAM на CPU",
    )

    # TTS (Silero)
    TTS_SPEAKER: str = Field(default="baya", description="Голос Silero TTS")
    TTS_SAMPLE_RATE: int = Field(
        default=48000,
        description="Частота дискретизации TTS (8000, 24000 или 48000)",
    )

    # Общие настройки сервиса
    MAX_AUDIO_DURATION_SEC: int = Field(
        default=30, description="Максимальная длительность аудио на STT (сек)"
    )
    LOG_LEVEL: str = Field(default="INFO", description="Уровень логирования")
    HOST: str = Field(default="0.0.0.0", description="Адрес для uvicorn")
    PORT: int = Field(default=8001, description="Порт для uvicorn")


settings = Settings()