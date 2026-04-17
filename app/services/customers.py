from __future__ import annotations

from bson import ObjectId
from pymongo.errors import DuplicateKeyError

from app.core.db import COLLECTIONS, get_db
from app.schemas.customers import AddCustomerRequest, AddCustomerResponse
from app.services.utils import oid_str


class CustomersService:
    async def add_customer(self, payload: AddCustomerRequest) -> AddCustomerResponse:
        db = get_db()
        customers = db[COLLECTIONS.customers]

        existing = await customers.find_one({"phone": payload.phone}, {"_id": 1})
        if existing is not None:
            return AddCustomerResponse(customer_id=oid_str(existing["_id"]))

        try:
            res = await customers.insert_one(
                {"name": payload.name, "phone": payload.phone}
            )
        except DuplicateKeyError:
            existing = await customers.find_one({"phone": payload.phone}, {"_id": 1})
            if existing is not None:
                return AddCustomerResponse(customer_id=oid_str(existing["_id"]))
            raise

        return AddCustomerResponse(customer_id=oid_str(res.inserted_id))


customers_service = CustomersService()


def get_customers_service() -> CustomersService:
    return customers_service

