"""Response models for paper upload and extraction."""

from typing import Literal

from pydantic import BaseModel, Field


class ReferenceEntry(BaseModel):
    """A single reference entry, numbered or unnumbered."""

    number: int | None = None
    raw_text: str
    doi: str | None = None


class PageText(BaseModel):
    """Text content of a single PDF page."""

    page_number: int
    text: str


class ReferenceValidation(BaseModel):
    """Validation analysis for structured reference numbering and segmentation."""

    reference_count: int = 0
    expected_count: int = 0
    highest_observed_reference: int | None = None
    detected_reference_count: int = 0
    observed_numbers: list[int] = Field(default_factory=list)
    missing_numbers: list[int] = Field(default_factory=list)
    duplicate_numbers: list[int] = Field(default_factory=list)
    unnumbered_entries: int = 0
    malformed_entries: int = 0
    malformed_count: int = 0
    status: Literal["good", "degraded", "poor"] = "good"
    reference_extraction_status: Literal["good", "degraded", "poor"] = "good"
    numbering_certainty: Literal["high", "medium", "low"] = "medium"


class ExtractionQuality(BaseModel):
    """Overall assessment of PDF parsing success and data completeness."""

    quality_score: float = Field(default=1.0, ge=0.0, le=1.0)
    status: Literal["good", "degraded", "poor"] = "good"
    issues: list[str] = Field(default_factory=list)


class PaperExtraction(BaseModel):
    """Structured content extracted from a PDF."""

    filename: str
    file_size_bytes: int
    page_count: int
    doi: str | None = None
    doi_candidates: list[str] = Field(default_factory=list)
    abstract: str | None = None
    abstract_status: Literal["found", "absent", "uncertain"] = "uncertain"
    abstract_confidence: float | None = None
    title: str | None = None
    title_confidence: float | None = None
    title_source: str | None = None
    authors: list[str] = Field(default_factory=list)
    author_confidence: float | None = None
    author_source: str | None = None
    keywords: list[str] = Field(default_factory=list)
    references_text: str | None = None
    references: list[ReferenceEntry] = Field(default_factory=list)
    reference_validation: ReferenceValidation | None = None
    extraction_quality: ExtractionQuality | None = None
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
