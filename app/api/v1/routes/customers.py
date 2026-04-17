from __future__ import annotations

from fastapi import APIRouter, Depends

from app.schemas.customers import AddCustomerRequest, AddCustomerResponse
from app.services.customers import CustomersService, get_customers_service

router = APIRouter()


@router.post("/add_customer", response_model=AddCustomerResponse)
async def add_customer(
    payload: AddCustomerRequest,
    service: CustomersService = Depends(get_customers_service),
) -> AddCustomerResponse:
    return await service.add_customer(payload)

