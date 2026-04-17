from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

from app.schemas.common import SuccessResponse


PetType = Literal["Cat", "Dog"]
PetGender = Literal["male", "female"]
PetSize = Literal["small", "medium", "large", "xlarge"]
PetAge = Literal["baby", "young", "adult", "senior"]


class CreatePetRequest(BaseModel):
    type: PetType
    gender: PetGender
    size: PetSize
    age: PetAge
    Photo: list[str] = Field(default_factory=list)
    good_with_children: bool


class CreatePetResponse(SuccessResponse):
    pet_id: str


class GetPetsRequest(BaseModel):
    type: PetType | None = None
    gender: PetGender | None = None
    size: PetSize | None = None
    age: PetAge | None = None
    good_with_children: bool | None = None
    limit: int = Field(..., gt=0, le=100)


class PetOut(BaseModel):
    pet_id: str
    source: Literal["local", "petfinder"]
    type: str
    gender: str
    size: str
    age: str
    good_with_children: bool
    Photos: list[str] = Field(default_factory=list)


class GetPetsResponse(SuccessResponse):
    pets: list[PetOut]

