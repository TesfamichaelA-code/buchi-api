from __future__ import annotations

from fastapi import APIRouter

from app.api.v1.routes import adoptions, customers, pets

api_router = APIRouter()
api_router.include_router(pets.router, tags=["pets"])
api_router.include_router(customers.router, tags=["customers"])
api_router.include_router(adoptions.router, tags=["adoptions"])

