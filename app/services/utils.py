from __future__ import annotations

from bson import ObjectId


def oid_str(oid: ObjectId) -> str:
    return str(oid)

