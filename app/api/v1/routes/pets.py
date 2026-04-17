from __future__ import annotations

from fastapi import APIRouter, Depends

from app.schemas.pets import CreatePetRequest, CreatePetResponse, GetPetsRequest, GetPetsResponse
from app.services.pets import PetsService, get_pets_service

router = APIRouter()


@router.post("/create_pet", response_model=CreatePetResponse)
async def create_pet(
    payload: CreatePetRequest,
    service: PetsService = Depends(get_pets_service),
) -> CreatePetResponse:
    return await service.create_pet(payload)


@router.get("/get_pets", response_model=GetPetsResponse)
async def get_pets(
    query: GetPetsRequest = Depends(),
    service: PetsService = Depends(get_pets_service),
) -> GetPetsResponse:
    return await service.get_pets(query)

