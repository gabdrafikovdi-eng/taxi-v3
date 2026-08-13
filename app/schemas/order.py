from uuid import UUID

from pydantic.fields import Field
from pydantic.main import BaseModel


class OrderIdInput(BaseModel):
    id: UUID


class SetPassengerNameInput(BaseModel):
    order_id: UUID = Field(..., description="")
    name: str = Field(..., max_length=50, description="")


class SetCommentInput(BaseModel):
    order_id: UUID = Field(..., description="")
    comment: str = Field(..., description="")
