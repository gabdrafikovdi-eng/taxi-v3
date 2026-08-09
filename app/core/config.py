from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

from app.services.state_service import OrderState


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

    MAX_ACTIVE_ORDERS = 3  # Максимум активных заказов в одном звонке. Зачем: защита от бесконечного создания заказов LLM.
    MAX_WAYPOINTS = 5  # Максимум промежуточных остановок в одном заказе. Зачем: защита от слишком длинных маршрутов.
    ACTIVE_ORDER_STATES = (
        OrderState.DRAFT,
        OrderState.CONFIRMED,
        OrderState.SEARCHING,
        OrderState.ASSIGNED,
        OrderState.IN_PROGRESS,
    )  # Состояния, в которых заказ считается активным. Зачем: репозиторий использует для поиска активных заказов.


config_settings = Settings()
