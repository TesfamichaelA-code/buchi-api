from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(env_prefix="BUCHI_", env_file=".env", extra="ignore")

    mongodb_uri: str = "mongodb://localhost:27017"
    mongodb_db: str = "buchi"

    base_url: str = "http://localhost:8000"
    photo_dir: str = "app/storage/photos"

    dog_api_key: str | None = None


settings = Settings()

