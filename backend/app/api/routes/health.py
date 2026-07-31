"""Health check endpoint."""

from fastapi import APIRouter

from app.core.config import get_settings
from app.schemas.paper import HealthResponse

router = APIRouter()


@router.get("/health", response_model=HealthResponse, tags=["system"])
def health_check() -> HealthResponse:
    """Return service liveness information."""
    settings = get_settings()
    return HealthResponse(
        status="healthy",
        service="verischolar-api",
        version=settings.app_version,
    )
