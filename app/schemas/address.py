from pydantic.config import ConfigDict
from pydantic.fields import Field
from pydantic import BaseModel

from enum import StrEnum


class AddressInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    town: str | None = Field(default=None, description="")
    district: str | None = Field(default=None, description="")
    street: str | None = Field(default=None, description="")
    house: str | None = Field(default=None, description="")
    landmark: str | None = Field(default=None, description="")


class NormalizedAddressInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    town: str | None = Field(default=None, description="")
    district: str | None = Field(default=None, description="")
    street: str | None = Field(default=None, description="")
    house: str | None = Field(default=None, description="")
    landmark: str | None = Field(default=None, description="")


class AddressStatus(StrEnum):
    RESOLVED = "resolved"  # Нашли 1 уверенный вариант -> оформляем
    AMBIGUOUS = "ambiguous"  # Нашли 2-3 варианта -> LLM задает уточняющий вопрос
    NOT_FOUND = "not_found"  # Ничего не нашли -> просим переназват
    INCOMPLETE = "incomplete"  # Не заполнен address + house or landmark


class AddressCandidate(BaseModel):
    model_config = ConfigDict(from_attributes=True, frozen=True)

    town_id: int
    town_name: str
    district_id: int
    district_name: str
    street_id: int
    street_name: str
    house_id: int | None = None
    house_number: str | None = None
    landmark_id: int | None = None
    landmark_name: str | None = None

    full_address: str

    score: float = Field(ge=0.0, le=1.0)
    diff_feature: str | None = None

    @property
    def fulladdress(self) -> str:
        """Алиас старого имени поля: ``fulladdress`` == ``full_address``.

        Сохранён для обратной совместимости: тесты/клиенты, которые обращались
        к полю как ``fulladdress`` (без подчёркивания), продолжают работать.
        """
        return self.full_address


class AddressMatchResult(BaseModel):
    model_config = ConfigDict(frozen=True)

    status: AddressStatus
    candidates: list[AddressCandidate] = Field(default_factory=list)
    reason: str | None = None


class MatchType(StrEnum):
    EXACT = "exact"
    SYNONYM = "synonym"
    FUZZY = "fuzzy"
    LANDMARK = "landmark"


class PricingAddress(BaseModel):
    town_base_price: int | None = None
    district_price: int | None = None
    street_price: int | None = None
    house_price: int | None = None
