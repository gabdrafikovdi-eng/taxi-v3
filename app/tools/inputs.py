from pydantic import BaseModel, Field
from pydantic.config import ConfigDict
from app.schemas.address import AddressInput


class BaseToolInput(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class CreateOrderInput(BaseToolInput): ...


class OrderNumberInput(BaseToolInput):
    order_number: int = Field(
        ...,
        ge=1,
        description="Номер заказа в текущем звонке. Например: 1, 2, 3.",
    )


class SetAddressInput(BaseToolInput):
    order_number: int = Field(
        ...,
        ge=1,
        description="Номер заказа, для которого нужно установить адрес.",
    )
    address: AddressInput = Field(
        ...,
        description="Адрес: город, район, улица, дом или ориентир.",
    )


class SetPassengerNameInput(BaseToolInput):
    order_number: int = Field(
        ...,
        ge=1,
        description="Номер заказа, для которого нужно сохранить имя пассажира.",
    )
    name: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="Имя пассажира.",
    )


class SetCommentInput(BaseToolInput):
    order_number: int = Field(
        ...,
        ge=1,
        description="Номер заказа, для которого нужно сохранить комментарий.",
    )
    comment: str = Field(
        ...,
        min_length=1,
        max_length=300,
        description="Комментарий к заказу.",
    )


class AddWaypointInput(BaseToolInput):
    order_number: int = Field(
        ...,
        ge=1,
        description="Номер заказа, для которого нужно добавить остановку.",
    )
    address: AddressInput = Field(
        ...,
        description="Адрес промежуточной остановки.",
    )


class UpdateWaypointInput(BaseToolInput):
    order_number: int = Field(
        ...,
        ge=1,
        description="Номер заказа.",
    )
    sequence_number: int = Field(
        ...,
        ge=1,
        description="Порядковый номер остановки для изменения.",
    )
    address: AddressInput = Field(
        ...,
        description="Новый адрес остановки.",
    )


class RemoveWaypointInput(BaseToolInput):
    order_number: int = Field(
        ...,
        ge=1,
        description="Номер заказа.",
    )
    sequence_number: int = Field(
        ...,
        ge=1,
        description="Порядковый номер остановки для удаления.",
    )
