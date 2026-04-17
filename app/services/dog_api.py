from __future__ import annotations

import httpx

from app.core.config import settings


class DogAPIService:
    """TheDogAPI client for external dog search."""

    base_url = "https://api.thedogapi.com/v1"

    async def search_dogs(self, *, limit: int) -> list[dict]:
        if not settings.dog_api_key:
            return []

        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.get(
                f"{self.base_url}/images/search",
                params={
                    "limit": limit,
                    "has_breeds": True,
                    "include_breeds": True,
                },
                headers={"x-api-key": settings.dog_api_key},
            )
            resp.raise_for_status()
            data = resp.json()

        if isinstance(data, list):
            return data
        return []


dog_api_service = DogAPIService()


def get_dog_api_service() -> DogAPIService:
    return dog_api_service

