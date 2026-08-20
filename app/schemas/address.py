from pydantic.config import ConfigDict
from pydantic.fields import Field
from pydantic import BaseModel
from pydantic.functional_validators import field_validator
from app.models.address import Street
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
    suggestions: list[AddressCandidate] = Field(default_factory=list)
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


class AddressContext(BaseModel):
    town_id: int
    district_ids: list[int]


class StreetMatch(BaseModel):
    """Совпадение по улице (результат этапа StreetResolver)."""

    # `street` — это ORM-объект SQLAlchemy (app.models.address.Street),
    # а не Pydantic-модель, поэтому нужен arbitrary_types_allowed.
    model_config = ConfigDict(arbitrary_types_allowed=True)

    street: Street
    score: float
    match_type: MatchType


class HouseNumberType(StrEnum):
    PLAIN = "plain"
    LETTER = "letter"
    CORPUS = "corpus"
    FRACTION = "fraction"


class HouseNumberParts(BaseModel):
    model_config = ConfigDict(frozen=True)
    base: str
    type: HouseNumberType
    suffix: str | None = None


class PassengerName(BaseModel):
    first_name: str = Field(
        ...,
        description="Имя пассажира",
        min_length=1,
        max_length=100,
    )

    @field_validator("first_name")
    @classmethod
    def normalize_name(cls, value: str) -> str:
        value = " ".join(value.split()).title()

        if not value:
            raise ValueError("Имя пассажира не может быть пустым")

        return value


class OrderComment(BaseModel):
    comment: str = Field(
        ..., description="Комментарий к заказу", min_length=1, max_length=300
    )

    @field_validator("comment")
    @classmethod
    def normazile_comment(cls, value: str) -> str:
        value = " ".join(value.split())

        if not value:
            raise ValueError("Коментарий к заказу не может быть пустым")

        return value
