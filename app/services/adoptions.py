from __future__ import annotations

from datetime import datetime, time, timedelta, timezone

from bson import ObjectId

from app.core.db import COLLECTIONS, get_db
from app.core.errors import NotFoundError
from app.schemas.adoptions import (
    AdoptRequest,
    AdoptResponse,
    DateRangeRequest,
    GenerateReportResponse,
    GetAdoptionRequestsResponse,
)
from app.services.utils import oid_str


class AdoptionsService:
    async def adopt(self, payload: AdoptRequest) -> AdoptResponse:
        db = get_db()
        customers = db[COLLECTIONS.customers]
        pets = db[COLLECTIONS.pets]
        adoptions = db[COLLECTIONS.adoption_requests]

        try:
            customer_oid = ObjectId(payload.customer_id)
        except Exception:
            raise NotFoundError("customer_id doesn't exist")
        try:
            pet_oid = ObjectId(payload.pet_id)
        except Exception:
            raise NotFoundError("pet_id doesn't exist")

        if await customers.find_one({"_id": customer_oid}, {"_id": 1}) is None:
            raise NotFoundError("customer_id doesn't exist")
        if await pets.find_one({"_id": pet_oid}, {"_id": 1}) is None:
            raise NotFoundError("pet_id doesn't exist")

        res = await adoptions.insert_one(
            {
                "customer_id": customer_oid,
                "pet_id": pet_oid,
                "created_at": datetime.now(timezone.utc),
            }
        )
        return AdoptResponse(adoption_id=oid_str(ObjectId(res.inserted_id)))

    async def get_adoption_requests(
        self, query: DateRangeRequest
    ) -> GetAdoptionRequestsResponse:
        db = get_db()
        adoptions = db[COLLECTIONS.adoption_requests]

        start = datetime.combine(query.from_date, time.min, tzinfo=timezone.utc)
        end = datetime.combine(query.to_date, time.min, tzinfo=timezone.utc) + timedelta(days=1)

        pipeline = [
            {"$match": {"created_at": {"$gte": start, "$lt": end}}},
            # Oldest requests appear at the top (ascending).
            {"$sort": {"created_at": 1}},
            {
                "$lookup": {
                    "from": COLLECTIONS.customers,
                    "localField": "customer_id",
                    "foreignField": "_id",
                    "as": "customer",
                }
            },
            {"$unwind": "$customer"},
            {
                "$lookup": {
                    "from": COLLECTIONS.pets,
                    "localField": "pet_id",
                    "foreignField": "_id",
                    "as": "pet",
                }
            },
            {"$unwind": "$pet"},
            {
                "$project": {
                    "_id": 0,
                    "customer_id": {"$toString": "$customer_id"},
                    "customer_phone": "$customer.phone",
                    "customer_name": "$customer.name",
                    "Pet_id": {"$toString": "$pet_id"},
                    "type": "$pet.type",
                    "gender": "$pet.gender",
                    "size": "$pet.size",
                    "age": "$pet.age",
                    "good_with_children": "$pet.good_with_children",
                }
            },
        ]

        data = await adoptions.aggregate(pipeline).to_list(length=None)
        return GetAdoptionRequestsResponse(data=data)

    async def generate_report(self, payload: DateRangeRequest) -> GenerateReportResponse:
        db = get_db()
        adoptions = db[COLLECTIONS.adoption_requests]

        start = datetime.combine(payload.from_date, time.min, tzinfo=timezone.utc)
        end = datetime.combine(payload.to_date, time.min, tzinfo=timezone.utc) + timedelta(days=1)

        adopted_types_pipeline = [
            {"$match": {"created_at": {"$gte": start, "$lt": end}}},
            {
                "$lookup": {
                    "from": COLLECTIONS.pets,
                    "localField": "pet_id",
                    "foreignField": "_id",
                    "as": "pet",
                }
            },
            {"$unwind": "$pet"},
            {"$group": {"_id": "$pet.type", "count": {"$sum": 1}}},
        ]
        adopted_types = await adoptions.aggregate(adopted_types_pipeline).to_list(length=None)
        adopted_pet_types = {str(r["_id"]): int(r["count"]) for r in adopted_types if r.get("_id") is not None}

        weekly_pipeline = [
            {"$match": {"created_at": {"$gte": start, "$lt": end}}},
            {
                "$group": {
                    "_id": {
                        "$dateTrunc": {
                            "date": "$created_at",
                            "unit": "week",
                            "timezone": "UTC",
                        }
                    },
                    "count": {"$sum": 1},
                }
            },
            {"$sort": {"_id": 1}},
        ]
        weekly = await adoptions.aggregate(weekly_pipeline).to_list(length=None)
        weekly_adoption_requests: dict[str, int] = {}
        for r in weekly:
            dt = r["_id"]
            if isinstance(dt, datetime):
                weekly_adoption_requests[dt.date().isoformat()] = int(r["count"])

        return GenerateReportResponse(
            data={
                "adopted_pet_types": adopted_pet_types,
                "weekly_adoption_requests": weekly_adoption_requests,
            }
        )


adoptions_service = AdoptionsService()


def get_adoptions_service() -> AdoptionsService:
    return adoptions_service

