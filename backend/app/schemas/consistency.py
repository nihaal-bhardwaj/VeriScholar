"""Pydantic models for the consistency check endpoint."""

from pydantic import BaseModel, Field

from app.schemas.paper import PageText, ReferenceEntry


class ConsistencyFlag(BaseModel):
    """A single inconsistency found by a consistency rule."""

    rule: str
    severity: str
    message: str
    evidence: str


class ConsistencyReport(BaseModel):
    """Result of running all consistency rules over an extracted paper."""

    flags: list[ConsistencyFlag] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    passed_checks: list[str] = Field(default_factory=list)
    consistency_score: float


class ConsistencyCheckRequest(BaseModel):
    """Request body for the consistency check endpoint."""

    analysis_id: str
    full_text: str
    authors: list[str] = Field(default_factory=list)
    references: list[ReferenceEntry] = Field(default_factory=list)
    pages: list[PageText] = Field(default_factory=list)