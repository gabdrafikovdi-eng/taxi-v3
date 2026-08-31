"""Конфигурация telephony-service (pydantic-settings).

Все настройки читаются из переменных окружения или ``.env``
(образец: ``.env.example``). Имена полей = имена переменных окружения.
"""

from __future__ import annotations

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=True,
    )

    # ----- Asterisk ARI -------------------------------------------------------
    ASTERISK_ARI_URL: str = Field(
        default="http://asterisk:8088",
        description="Базовый URL ARI (из compose-сети — имя сервиса asterisk)",
    )
    ASTERISK_ARI_USERNAME: str = Field(default="taxi", description="Пользователь ARI")
    ASTERISK_ARI_PASSWORD: str = Field(default="change-me-strong", description="Пароль ARI")
    ASTERISK_ARI_APP: str = Field(default="taxi", description="Имя Stasis-приложения")
    ARI_RECONNECT_MIN_SEC: float = Field(
        default=1.0, description="Начальная задержка реконнекта WebSocket ARI"
    )
    ARI_RECONNECT_MAX_SEC: float = Field(
        default=30.0, description="Максимальная задержка реконнекта WebSocket ARI"
    )

    # ----- Media pipeline -----------------------------------------------------
    MEDIA_FORMAT: str = Field(
        default="ulaw",
        description="Кодек телефонии: ulaw (G.711 µ-law) или alaw (G.711 A-law)",
    )
    TELEPHONY_EXTERNAL_HOST: str = Field(
        default="taxi-telephony",
        description="Хост/имя, по которому Asterisk отправляет RTP в telephony-service",
    )
    RTP_SERVICE_PORT_START: int = Field(
        default=18000, description="Начало диапазона UDP-портов external media"
    )
    RTP_SERVICE_PORT_END: int = Field(
        default=18050, description="Конец диапазона UDP-портов external media"
    )

    # ----- speech-service -----------------------------------------------------
    SPEECH_SERVICE_URL: str = Field(
        default="http://host.docker.internal:8001",
        description="Базовый URL существующего speech-service",
    )
    STT_TIMEOUT_SEC: float = Field(default=10.0, description="Таймаут STT-запроса")
    TTS_TIMEOUT_SEC: float = Field(default=20.0, description="Таймаут TTS-запроса")

    # ----- backend ------------------------------------------------------------
    BACKEND_MODE: str = Field(
        default="mock",
        description="Режим интеграции с backend: mock | http",
    )
    BACKEND_URL: str = Field(default="http://backend:8000", description="Базовый URL backend")
    BACKEND_TIMEOUT_SEC: float = Field(default=30.0, description="Таймаут запросов к backend")

    # ----- Turn-taking (сегментация фраз) -------------------------------------
    ENERGY_SPEECH_THRESHOLD: float = Field(
        default=900.0, description="RMS (int16) выше порога — речь"
    )
    SILENCE_MS: int = Field(default=700, description="Тишина, завершающая фразу")
    MIN_SPEECH_MS: int = Field(default=300, description="Минимальная длительность речи")
    MAX_UTTERANCE_MS: int = Field(default=15000, description="Максимальная длина реплики")
    PREROLL_MS: int = Field(default=200, description="Аудио до начала речи в реплике")

    # ----- Лимиты звонка -------------------------------------------------------
    MAX_CALL_DURATION_SEC: int = Field(default=600, description="Максимальная длительность звонка")
    PLAY_GREETING: bool = Field(default=True, description="Приветствие при ответе")

    # ----- Health / logging ----------------------------------------------------
    HEALTH_HOST: str = Field(default="0.0.0.0", description="Адрес health-сервера")
    HEALTH_PORT: int = Field(default=8090, description="Порт health-сервера")
    LOG_LEVEL: str = Field(default="INFO", description="Уровень логирования")

    # --------------------------------------------------------------------------

    @property
    def rtp_payload_type(self) -> int:
        """Статический payload type: 0 = PCMU (ulaw), 8 = PCMA (alaw)."""
        return 0 if self.MEDIA_FORMAT == "ulaw" else 8

    @property
    def stt_content_type(self) -> str:
        """Content-Type для STT: speech-service декодирует G.711 по content-type."""
        return "audio/x-mulaw" if self.MEDIA_FORMAT == "ulaw" else "audio/x-alaw"


settings = Settings()
