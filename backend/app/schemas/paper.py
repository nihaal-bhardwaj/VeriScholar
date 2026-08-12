"""Response models for paper upload and extraction."""

from typing import Literal

from pydantic import BaseModel, Field


class ReferenceEntry(BaseModel):
    """A single numbered reference entry."""

    number: int
    raw_text: str
    doi: str | None = None


class PageText(BaseModel):
    """Text content of a single PDF page."""

    page_number: int
    text: str


class PaperExtraction(BaseModel):
    """Structured content extracted from a PDF."""

    filename: str
    file_size_bytes: int
    page_count: int
    doi: str | None = None
    doi_candidates: list[str] = Field(default_factory=list)
    abstract: str | None = None
    title: str | None = None
    authors: list[str] = Field(default_factory=list)
    references_text: str | None = None
    references: list[ReferenceEntry] = Field(default_factory=list)
    pages: list[PageText] = Field(default_factory=list)


class ExtractionResponse(BaseModel):
    """Top-level response of the extraction endpoint."""

    analysis_id: str
    status: Literal["completed", "failed"]
    paper: PaperExtraction
    warnings: list[str] = Field(default_factory=list)


class HealthResponse(BaseModel):
    """Response of the health endpoint."""

    status: str
    service: str
    version: str


class ErrorResponse(BaseModel):
    """Uniform JSON error body returned by the API."""

    error: str
    detail: str
