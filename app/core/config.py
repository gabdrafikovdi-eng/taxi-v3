from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

from app.models.order_state import OrderState


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=True,
    )

    # Настройки DB
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_HOST: str
    POSTGRES_PORT: str
    POSTGRES_DB: str

    @property
    def DATABASE_URL(self) -> str:
        # Формат: postgresql+asyncpg://USER:PASSWORD@HOST:PORT/DB
        return (
            f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
            f"@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )

    # LLM
    OPENAI_API_KEY: str
    OPENAI_BASE_URL: str
    OPENAI_MODEL: str

    # Logger
    LOG_LEVEL: str = Field(default="INFO")

    MAX_ACTIVE_ORDERS: int = 3  # Максимум активных заказов в одном звонке. Зачем: защита от бесконечного создания заказов LLM.
    MAX_WAYPOINTS: int = 5  # Максимум промежуточных остановок в одном заказе. Зачем: защита от слишком длинных маршрутов.
    

config_settings = Settings()
