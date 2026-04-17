from __future__ import annotations

import os
from datetime import date

import pytest
from httpx import ASGITransport, AsyncClient
from pydantic import ValidationError


# --- Environment setup (runs before importing app-level modules that read env) ---


@pytest.fixture(scope="session", autouse=True)
def _test_env(tmp_path_factory: pytest.TempPathFactory) -> None:
    photo_dir = tmp_path_factory.mktemp("photos")
    os.environ.setdefault("BUCHI_MONGODB_URI", "mongodb://localhost:27017")
    os.environ.setdefault("BUCHI_MONGODB_DB", "buchi_test")
    os.environ.setdefault("BUCHI_BASE_URL", "http://test")
    os.environ.setdefault("BUCHI_PHOTO_DIR", str(photo_dir))


# --- Helpers ---


async def _mongo_available() -> bool:
    from app.core.db import get_db

    try:
        db = get_db()
        await db.command("ping")
        return True
    except Exception:
        return False


def _make_client() -> AsyncClient:
    from app.main import create_app

    return AsyncClient(transport=ASGITransport(app=create_app()), base_url="http://test")


# --- Pure schema tests (no Mongo required) ---


def test_date_range_rejects_inverted_dates() -> None:
    from app.schemas.adoptions import DateRangeRequest

    with pytest.raises(ValidationError):
        DateRangeRequest(from_date=date(2026, 1, 10), to_date=date(2026, 1, 1))


def test_date_range_accepts_equal_dates() -> None:
    from app.schemas.adoptions import DateRangeRequest

    r = DateRangeRequest(from_date=date(2026, 1, 1), to_date=date(2026, 1, 1))
    assert r.from_date == r.to_date


def test_add_customer_rejects_empty_name() -> None:
    from app.schemas.customers import AddCustomerRequest

    with pytest.raises(ValidationError):
        AddCustomerRequest(name="   ", phone="0922222222")


def test_add_customer_rejects_invalid_phone() -> None:
    from app.schemas.customers import AddCustomerRequest

    with pytest.raises(ValidationError):
        AddCustomerRequest(name="Abebe", phone="not-a-phone!")


def test_get_pets_limit_must_be_positive() -> None:
    from app.schemas.pets import GetPetsRequest

    with pytest.raises(ValidationError):
        GetPetsRequest(limit=0)


# --- Endpoint tests that do not hit Mongo ---


@pytest.mark.asyncio
async def test_health_endpoint() -> None:
    async with _make_client() as ac:
        r = await ac.get("/health")
        assert r.status_code == 200
        assert r.json() == {"status": "ok"}


@pytest.mark.asyncio
async def test_adopt_with_invalid_id_format_returns_404() -> None:
    # Both IDs are not valid ObjectId hex; the handler 404s before touching DB.
    async with _make_client() as ac:
        r = await ac.post(
            "/adopt",
            json={"customer_id": "not-an-id", "pet_id": "also-not"},
        )
        assert r.status_code == 404
        body = r.json()
        assert body["status"] == "error"
        assert "customer_id" in body["message"] or "pet_id" in body["message"]


@pytest.mark.asyncio
async def test_generate_report_rejects_inverted_dates() -> None:
    async with _make_client() as ac:
        r = await ac.post(
            "/generate_report",
            json={"from_date": "2026-12-31", "to_date": "2026-01-01"},
        )
        assert r.status_code == 422


# --- Integration-style tests (require Mongo) ---


@pytest.mark.asyncio
async def test_add_customer_idempotent() -> None:
    if not await _mongo_available():
        pytest.skip("MongoDB not available for integration-style tests.")

    from app.core.db import get_db

    async with _make_client() as ac:
        db = get_db()
        await db.drop_collection("customers")

        payload = {"name": "Abebe Kebede", "phone": "0922222222"}
        r1 = await ac.post("/add_customer", json=payload)
        assert r1.status_code == 200
        cid1 = r1.json()["customer_id"]

        r2 = await ac.post("/add_customer", json=payload)
        assert r2.status_code == 200
        cid2 = r2.json()["customer_id"]

        assert cid1 == cid2


@pytest.mark.asyncio
async def test_create_pet_then_get_pets_local_first() -> None:
    if not await _mongo_available():
        pytest.skip("MongoDB not available for integration-style tests.")

    from app.core.db import get_db

    async with _make_client() as ac:
        db = get_db()
        await db.drop_collection("pets")

        pet_payload = {
            "type": "Dog",
            "gender": "male",
            "size": "small",
            "age": "baby",
            "Photo": [],
            "good_with_children": True,
        }
        r = await ac.post("/create_pet", json=pet_payload)
        assert r.status_code == 200
        pet_id = r.json()["pet_id"]

        rg = await ac.get(
            "/get_pets",
            params={
                "type": "Dog",
                "gender": "male",
                "size": "small",
                "age": "baby",
                "good_with_children": "true",
                "limit": "5",
            },
        )
        assert rg.status_code == 200
        data = rg.json()
        assert data["status"] == "success"
        assert len(data["pets"]) >= 1
        assert data["pets"][0]["source"] == "local"
        assert data["pets"][0]["pet_id"] == pet_id


@pytest.mark.asyncio
async def test_adopt_flow_and_get_adoption_requests() -> None:
    if not await _mongo_available():
        pytest.skip("MongoDB not available for integration-style tests.")

    from app.core.db import get_db

    async with _make_client() as ac:
        db = get_db()
        await db.drop_collection("customers")
        await db.drop_collection("pets")
        await db.drop_collection("adoption_requests")

        rc = await ac.post(
            "/add_customer",
            json={"name": "Kebede Abebe", "phone": "0911111111"},
        )
        customer_id = rc.json()["customer_id"]

        rp = await ac.post(
            "/create_pet",
            json={
                "type": "Cat",
                "gender": "female",
                "size": "small",
                "age": "young",
                "Photo": [],
                "good_with_children": True,
            },
        )
        pet_id = rp.json()["pet_id"]

        ra = await ac.post(
            "/adopt",
            json={"customer_id": customer_id, "pet_id": pet_id},
        )
        assert ra.status_code == 200
        assert "adoption_id" in ra.json()

        today = date.today().isoformat()
        rr = await ac.get(
            "/get_adoption_requests",
            params={"from_date": today, "to_date": today},
        )
        assert rr.status_code == 200
        data = rr.json()
        assert data["status"] == "success"
        assert len(data["data"]) == 1
        row = data["data"][0]
        assert row["customer_id"] == customer_id
        assert row["Pet_id"] == pet_id
        assert row["customer_name"] == "Kebede Abebe"
        assert row["type"] == "Cat"
