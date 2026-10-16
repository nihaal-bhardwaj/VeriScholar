"""Pydantic models for the combined risk report."""

from datetime import datetime

from pydantic import BaseModel, Field

from app.schemas.consistency import ConsistencyReport
from app.schemas.ml import MLAnalysisResult
from app.schemas.paper import ExtractionQuality


class RiskSignal(BaseModel):
    """A single warning sign contributing to the risk score."""

    source: str
    severity: str
    message: str
    evidence: str
    weight: float


class ReportInput(BaseModel):
    """Outputs of every analysis module, combined for the final report.

    Citation, metadata and ML modules are optional placeholders for now —
    the generator must work when they are `None`.
    """

    analysis_id: str
    paper_title: str = ""
    paper_authors: list[str] = Field(default_factory=list)
    abstract: str = ""
    keywords: list[str] = Field(default_factory=list)
    consistency_report: ConsistencyReport | None = None
    citation_results: dict | None = None
    metadata_results: dict | None = None
    ml_results: MLAnalysisResult | None = None
    extraction_quality: ExtractionQuality | None = None
    paper_metadata: dict | None = None
    metadata_verification: dict | None = None


class RiskReport(BaseModel):
    """Unified risk report produced by the final combiner."""

    analysis_id: str
    paper_title: str
    paper_authors: list[str]
    risk_score: float
    risk_level: str
    confidence: float
    summary: str
    signals: list[RiskSignal] = Field(default_factory=list)
    passed_checks: list[str] = Field(default_factory=list)
    modules_used: list[str] = Field(default_factory=list)
    extraction_quality: ExtractionQuality | None = None
    assessment_status: str = Field(default="evaluated", description="'evaluated', 'limited_evidence', or 'undetermined'")
    paper_metadata: dict | None = None
    metadata_verification: dict | None = None
    citation_results: dict | None = None
    generated_at: datetime