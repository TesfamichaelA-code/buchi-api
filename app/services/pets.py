from __future__ import annotations

import base64
import os
import uuid
from pathlib import Path

from bson import ObjectId

from app.core.config import settings
from app.core.db import COLLECTIONS, get_db
from app.schemas.pets import CreatePetRequest, CreatePetResponse, GetPetsRequest, GetPetsResponse, PetOut
from app.services.dog_api import DogAPIService, get_dog_api_service
from app.services.utils import oid_str


class PetsService:
    def __init__(self, dog_api: DogAPIService) -> None:
        self._dog_api = dog_api

    def _photo_url(self, filename: str) -> str:
        return f"{settings.base_url}/photos/{filename}"

    def _ensure_photo_dir(self) -> Path:
        path = Path(settings.photo_dir)
        path.mkdir(parents=True, exist_ok=True)
        return path

    def _store_photo_value(self, value: str) -> str:
        """
        Store a single photo payload and return its stored filename.

        Accepted:
        - Data URL base64 (e.g. "data:image/jpeg;base64,...")
        - Raw base64 (best-effort)
        - Plain string (treated as already-a-filename)
        """

        value = value.strip()
        if not value:
            return ""

        photo_dir = self._ensure_photo_dir()
        filename = f"{uuid.uuid4().hex}.bin"

        payload = value
        if "base64," in value:
            payload = value.split("base64,", 1)[1]

        try:
            data = base64.b64decode(payload, validate=True)
            (photo_dir / filename).write_bytes(data)
            return filename
        except Exception:
            # If it's not base64, treat it as a filename already.
            return os.path.basename(value)

    async def create_pet(self, payload: CreatePetRequest) -> CreatePetResponse:
        db = get_db()
        pets = db[COLLECTIONS.pets]

        stored_files = [f for f in (self._store_photo_value(p) for p in payload.Photo) if f]

        doc = {
            "type": payload.type,
            "gender": payload.gender,
            "size": payload.size,
            "age": payload.age,
            "good_with_children": payload.good_with_children,
            "photos": stored_files,
        }
        res = await pets.insert_one(doc)
        return CreatePetResponse(pet_id=oid_str(ObjectId(res.inserted_id)))

    async def get_pets(self, query: GetPetsRequest) -> GetPetsResponse:
        db = get_db()
        pets_col = db[COLLECTIONS.pets]

        filt: dict[str, object] = {}
        if query.type is not None:
            filt["type"] = query.type
        if query.gender is not None:
            filt["gender"] = query.gender
        if query.size is not None:
            filt["size"] = query.size
        if query.age is not None:
            filt["age"] = query.age
        if query.good_with_children is not None:
            filt["good_with_children"] = query.good_with_children

        local_docs = await pets_col.find(filt).limit(query.limit).to_list(length=query.limit)
        local_out: list[PetOut] = []
        for d in local_docs:
            local_out.append(
                PetOut(
                    pet_id=oid_str(d["_id"]),
                    source="local",
                    type=str(d.get("type", "")),
                    gender=str(d.get("gender", "")),
                    size=str(d.get("size", "")),
                    age=str(d.get("age", "")),
                    good_with_children=bool(d.get("good_with_children", False)),
                    Photos=[self._photo_url(f) for f in (d.get("photos") or [])],
                )
            )

        remaining = query.limit - len(local_out)
        external_out: list[PetOut] = []
        if remaining > 0:
            # TheDogAPI only covers dogs, so non-dog searches remain local-only.
            if query.type in (None, "Dog"):
                animals = await self._dog_api.search_dogs(limit=remaining)
            else:
                animals = []

            for a in animals[:remaining]:
                external_out.append(
                    PetOut(
                        pet_id=str(a.get("id", "")),
                        source="petfinder",
                        type="Dog",
                        gender=query.gender or "",
                        size=query.size or "",
                        age=query.age or "",
                        # TheDogAPI does not expose this field; preserve response shape.
                        good_with_children=query.good_with_children if query.good_with_children is not None else False,
                        Photos=[str(a.get("url"))] if a.get("url") else [],
                    )
                )

        return GetPetsResponse(pets=[*local_out, *external_out][: query.limit])


pets_service = PetsService(get_dog_api_service())


def get_pets_service() -> PetsService:
    return pets_service

