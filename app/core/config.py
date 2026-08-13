from pydantic import Field
from pydantic import BaseModel
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


class AddressConfig(BaseModel):
    default_town_name: str = "аскарово"
    fuzzy_threshold: float = 0.4
    max_candidates: int = 5
    min_resolve_score: float = 0.9
    max_exact_variants: int = 3


    weights: dict[str, float] = {
        "exact": 1.0,
        "synonym": 0.9,
        "fuzzy": 0.6,
        "landmark": 0.7,
        "district_match_bonus": 0.1,
        "house_match_bonus": 0.2,
        "landmark_house_bonus": 0.15,
    }

address_config = AddressConfig()
