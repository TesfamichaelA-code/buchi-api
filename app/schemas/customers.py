from __future__ import annotations

from pydantic import BaseModel, Field, field_validator

from app.schemas.common import SuccessResponse


class AddCustomerRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=120)
    phone: str = Field(..., min_length=5, max_length=20)

    @field_validator("name")
    @classmethod
    def _strip_name(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("name must not be empty")
        return v

    @field_validator("phone")
    @classmethod
    def _validate_phone(cls, v: str) -> str:
        v = v.strip()
        allowed = set("0123456789+-() ")
        if not v or any(c not in allowed for c in v):
            raise ValueError("phone contains invalid characters")
        digits = sum(c.isdigit() for c in v)
        if digits < 5:
            raise ValueError("phone must contain at least 5 digits")
        return v


class AddCustomerResponse(SuccessResponse):
    customer_id: str
