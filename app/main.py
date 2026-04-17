from __future__ import annotations

from contextlib import asynccontextmanager
from pathlib import Path
from typing import AsyncIterator

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.api.router import api_router
from app.core.config import settings
from app.core.db import get_client, init_indexes
from app.core.errors import AppError, app_error_handler, unhandled_error_handler


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    await init_indexes()
    yield
    client = get_client()
    client.close()


def create_app() -> FastAPI:
    app = FastAPI(title="Buchi Backend", lifespan=lifespan)

    app.add_exception_handler(AppError, lambda req, exc: app_error_handler(req, exc))  # type: ignore
    app.add_exception_handler(Exception, unhandled_error_handler)

    app.include_router(api_router)

    Path(settings.photo_dir).mkdir(parents=True, exist_ok=True)
    app.mount("/photos", StaticFiles(directory=settings.photo_dir), name="photos")

    @app.get("/health", tags=["health"])
    async def health() -> dict[str, str]:
        return {"status": "ok"}

    return app


app = create_app()
