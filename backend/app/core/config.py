"""Central application configuration using Pydantic settings.

Values can be overridden via environment variables or a `.env` file.
"""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime configuration for the Mini Project backend."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "Mini Project API"
    app_version: str = "0.1.0"
    api_prefix: str = "/api/v1"
    max_upload_size_mb: int = 20
    cors_origins: str = "http://localhost:3000"

    @property
    def max_upload_size_bytes(self) -> int:
        """Maximum accepted upload size in bytes."""
        return self.max_upload_size_mb * 1024 * 1024

    @property
    def cors_origin_list(self) -> list[str]:
        """CORS origins parsed as a list from the comma-separated setting."""
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    """Return a cached Settings instance so `.env` is read once."""
    return Settings()
