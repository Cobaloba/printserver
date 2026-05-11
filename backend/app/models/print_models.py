from typing import Literal
from pydantic import BaseModel, Field, field_validator


class TodoRequest(BaseModel):
    title: str = "TO DO"
    items: list[str]

    @field_validator('items')
    @classmethod
    def items_not_empty(cls, v):
        if not v:
            raise ValueError('items must not be empty')
        return v


class ReceiptItem(BaseModel):
    name: str
    price: float


class ReceiptRequest(BaseModel):
    store: str
    items: list[ReceiptItem]
    address: str | None = None
    phone: str | None = None
    tax_pct: float = Field(default=0.0, ge=0.0)

    @field_validator('items')
    @classmethod
    def items_not_empty(cls, v):
        if not v:
            raise ValueError('items must not be empty')
        return v


class FreeTextRequest(BaseModel):
    text: str
    font_size: Literal["small", "medium", "large"] = "medium"


class QrRequest(BaseModel):
    url: str = Field(max_length=2048)
