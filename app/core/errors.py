from __future__ import annotations

from fastapi import Request
from fastapi.responses import JSONResponse


class AppError(Exception):
    """Base app exception for consistent error responses."""

    def __init__(self, message: str, status_code: int = 400) -> None:
        super().__init__(message)
        self.message = message
        self.status_code = status_code


class NotFoundError(AppError):
    """Raised when a resource is not found."""

    def __init__(self, message: str = "Not found") -> None:
        super().__init__(message=message, status_code=404)


class ConflictError(AppError):
    """Raised when a resource conflicts with existing data."""

    def __init__(self, message: str = "Conflict") -> None:
        super().__init__(message=message, status_code=409)


def app_error_handler(_: Request, exc: AppError) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content={"status": "error", "message": exc.message},
    )


def unhandled_error_handler(_: Request, exc: Exception) -> JSONResponse:
    # Avoid leaking internals; keep consistent shape.
    return JSONResponse(
        status_code=500,
        content={"status": "error", "message": "Internal server error"},
    )

