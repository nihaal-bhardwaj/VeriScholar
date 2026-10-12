"""Pydantic schemas for the Fake Review Detector module."""

from datetime import datetime, timezone
from typing import Optional
from pydantic import BaseModel, Field


class ScrapedReview(BaseModel):
    """An individual scraped or submitted product review."""

    review_text: str
    reviewer_name: Optional[str] = None
    rating: Optional[int] = None
    review_date: Optional[str] = None
    verified_purchase: Optional[bool] = None


class ScrapedReviewData(BaseModel):
    """Raw scraped review data and product metadata."""

    product_url: str
    product_title: Optional[str] = None
    source_site: Optional[str] = None
    reviews: list[ScrapedReview] = Field(default_factory=list)
    total_reviews_found: int = 0
    scrape_successful: bool = True
    warning: Optional[str] = None


class ReviewSignal(BaseModel):
    """An explainable signal or rule trigger for review authenticity."""

    rule: str
    severity: str  # "high", "medium", "low"
    message: str


class BatchAnalysisResult(BaseModel):
    """Cross-review batch pattern analysis result."""

    product_level_signals: list[ReviewSignal] = Field(default_factory=list)
    duplicate_pairs: list[tuple[int, int]] = Field(default_factory=list)
    reviews_flagged_as_duplicate: int = 0


class LLMSignal(BaseModel):
    """An explainable signal or observation from the LLM review evaluation."""

    type: str
    is_suspicious: bool
    description: str


class LLMReviewAnalysis(BaseModel):
    """Structured response from the LLM review authenticity analyzer."""

    authenticity_score: int = 50  # 0-100
    classification: str = "uncertain"  # "likely_genuine", "uncertain", "likely_fake"
    confidence: str = "low"  # "high", "medium", "low"
    reasoning: str = ""
    signals: list[LLMSignal] = Field(default_factory=list)
    llm_available: bool = True
    fallback_reason: Optional[str] = None  # why LLM was skipped


class ReviewAnalysisResult(BaseModel):
    """Analyzed single review with authenticity score and triggered signals."""

    review_text: str
    reviewer_name: Optional[str] = None
    rating: Optional[int] = None
    review_date: Optional[str] = None
    verified_purchase: Optional[bool] = None
    authenticity_score: float = Field(ge=0.0, le=100.0)
    classification: str  # "likely_genuine", "uncertain", "likely_fake"
    signals: list[ReviewSignal] = Field(default_factory=list)
    analyzed_by: str = "heuristics"  # "llm", "heuristics", or "llm+heuristics"
    reasoning: Optional[str] = None


class ProductReviewReport(BaseModel):
    """Unified report assessing the authenticity and trust of product reviews."""

    product_url: str
    product_title: Optional[str] = None
    source_site: Optional[str] = None
    total_reviews_analyzed: int = 0
    overall_trust_score: float = Field(ge=0.0, le=100.0)
    trust_level: str  # "low_trust_concern", "moderate_concern", "high_concern", "critical_concern", "insufficient_data"
    reviews: list[ReviewAnalysisResult] = Field(default_factory=list)
    batch_signals: list[ReviewSignal] = Field(default_factory=list)
    duplicate_review_count: int = 0
    summary: str
    generated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class AnalyzeProductRequest(BaseModel):
    """Request payload for analyzing reviews by product URL."""

    product_url: str


class ManualReviewItem(BaseModel):
    """Input review item for manual review batch analysis."""

    review_text: str
    reviewer_name: Optional[str] = None
    rating: Optional[int] = None
    review_date: Optional[str] = None
    verified_purchase: Optional[bool] = None


class AnalyzeManualRequest(BaseModel):
    """Request payload for manual review submission."""

    reviews: list[ManualReviewItem] = Field(default_factory=list)
