from __future__ import annotations

from datetime import date

from pydantic import BaseModel, Field, model_validator

from app.schemas.common import SuccessResponse


class AdoptRequest(BaseModel):
    customer_id: str = Field(..., min_length=1)
    pet_id: str = Field(..., min_length=1)


class AdoptResponse(SuccessResponse):
    adoption_id: str


class DateRangeRequest(BaseModel):
    from_date: date = Field(..., description="YYYY-MM-DD")
    to_date: date = Field(..., description="YYYY-MM-DD")

    @model_validator(mode="after")
    def _check_range(self) -> "DateRangeRequest":
        if self.to_date < self.from_date:
            raise ValueError("to_date must be on or after from_date")
        return self


class AdoptionRequestOut(BaseModel):
    customer_id: str
    customer_phone: str
    customer_name: str
    Pet_id: str
    type: str
    gender: str
    size: str
    age: str
    good_with_children: bool


class GetAdoptionRequestsResponse(SuccessResponse):
    data: list[AdoptionRequestOut]


class GenerateReportResponse(SuccessResponse):
    data: dict
