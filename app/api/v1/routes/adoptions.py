from __future__ import annotations

from fastapi import APIRouter, Depends

from app.schemas.adoptions import (
    AdoptRequest,
    AdoptResponse,
    DateRangeRequest,
    GenerateReportResponse,
    GetAdoptionRequestsResponse,
)
from app.services.adoptions import AdoptionsService, get_adoptions_service

router = APIRouter()


@router.post("/adopt", response_model=AdoptResponse)
async def adopt(
    payload: AdoptRequest,
    service: AdoptionsService = Depends(get_adoptions_service),
) -> AdoptResponse:
    return await service.adopt(payload)


@router.get("/get_adoption_requests", response_model=GetAdoptionRequestsResponse)
async def get_adoption_requests(
    query: DateRangeRequest = Depends(),
    service: AdoptionsService = Depends(get_adoptions_service),
) -> GetAdoptionRequestsResponse:
    return await service.get_adoption_requests(query)


@router.post("/generate_report", response_model=GenerateReportResponse)
async def generate_report(
    payload: DateRangeRequest,
    service: AdoptionsService = Depends(get_adoptions_service),
) -> GenerateReportResponse:
    return await service.generate_report(payload)

