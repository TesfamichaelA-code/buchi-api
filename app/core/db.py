from __future__ import annotations

import asyncio
from dataclasses import dataclass

from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase

from app.core.config import settings


@dataclass(frozen=True, slots=True)
class Collections:
    pets: str = "pets"
    customers: str = "customers"
    adoption_requests: str = "adoption_requests"


COLLECTIONS = Collections()

_client: AsyncIOMotorClient | None = None
_client_loop_id: int | None = None


def get_client() -> AsyncIOMotorClient:
    global _client, _client_loop_id

    try:
        current_loop_id = id(asyncio.get_running_loop())
    except RuntimeError:
        current_loop_id = None

    if _client is None or (_client_loop_id is not None and current_loop_id is not None and _client_loop_id != current_loop_id):
        if _client is not None:
            _client.close()
        _client = AsyncIOMotorClient(settings.mongodb_uri)
        _client_loop_id = current_loop_id
    return _client


def close_client() -> None:
    global _client, _client_loop_id
    if _client is not None:
        _client.close()
        _client = None
        _client_loop_id = None


def get_db() -> AsyncIOMotorDatabase:
    client = get_client()
    return client[settings.mongodb_db]


async def init_indexes() -> None:
    """Create required indexes (idempotent)."""

    db = get_db()

    # Prevent duplicate customers by phone number.
    await db[COLLECTIONS.customers].create_index("phone", unique=True)

    # Speed up local pet searches.
    await db[COLLECTIONS.pets].create_index([("type", 1), ("age", 1)])
    await db[COLLECTIONS.pets].create_index("good_with_children")
    await db[COLLECTIONS.pets].create_index("gender")
    await db[COLLECTIONS.pets].create_index("size")

    # Date range query + ordering for adoption requests.
    await db[COLLECTIONS.adoption_requests].create_index("created_at")
    await db[COLLECTIONS.adoption_requests].create_index("customer_id")
    await db[COLLECTIONS.adoption_requests].create_index("pet_id")

