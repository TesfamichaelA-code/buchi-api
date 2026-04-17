from __future__ import annotations

from typing import Literal

from pydantic import BaseModel


class SuccessResponse(BaseModel):
    status: Literal["success"] = "success"


class ErrorResponse(BaseModel):
    status: Literal["error"] = "error"
    message: str

