"""Mini Project API entry point.

Run from the backend directory with:
    uvicorn app.main:app --reload
"""

import logging

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.routes import health, papers
from app.core.config import get_settings

logger = logging.getLogger("mini-project")

settings = get_settings()

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description=(
        "Mini Project research-paper integrity screening. "
        "Extracts structure from uploaded PDFs and returns explainable "
        "screening signals - never a definitive 'fake paper' verdict."
    ),
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    """Return uniform `{"error", "detail"}` bodies for HTTP errors."""
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": exc.detail, "detail": exc.detail},
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    """Return a readable 422 body for request validation failures."""
    return JSONResponse(
        status_code=422,
        content={"error": "Invalid request", "detail": str(exc.errors())},
    )


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Never expose stack traces; log them server-side instead."""
    logger.exception("Unhandled error on %s %s", request.method, request.url.path)
    return JSONResponse(
        status_code=500,
        content={"error": "Internal server error", "detail": "An unexpected error occurred."},
    )


app.include_router(health.router, prefix=settings.api_prefix)
app.include_router(papers.router, prefix=settings.api_prefix)


@app.get("/", tags=["system"])
def root() -> dict[str, str]:
    """Minimal root response pointing to the API docs."""
    return {"service": settings.app_name, "version": settings.app_version, "docs": "/docs"}
