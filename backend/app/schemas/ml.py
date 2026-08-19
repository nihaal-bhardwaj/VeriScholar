"""Pydantic models for the rule-based ML text feature extractor."""

from pydantic import BaseModel, Field

_SEVERITY_POINTS = {"high": 15.0, "medium": 8.0, "low": 3.0}


class TextFeatures(BaseModel):
    """Numerical writing-quality and style features extracted from paper text.

    Every field is computed by explainable rule-based heuristics; a value of
    zero simply means the underlying signal could not be measured, never a
    fake-paper verdict.
    """

    # GROUP 1 — readability
    flesch_reading_ease: float = Field(default=0.0, description="Flesch reading ease, 0-100, higher = easier")
    flesch_kincaid_grade: float = Field(default=0.0, description="Flesch-Kincaid grade level")
    gunning_fog_index: float = Field(default=0.0, description="Gunning fog index")
    automated_readability_index: float = Field(default=0.0, description="Automated readability index")

    # GROUP 2 — vocabulary
    unique_word_ratio: float = Field(default=0.0, description="Unique words / total words, 0.0-1.0")
    avg_word_length: float = Field(default=0.0, description="Average characters per word")
    rare_word_ratio: float = Field(default=0.0, description="Words longer than 10 chars / total words")

    # GROUP 3 — sentence structure
    avg_sentence_length: float = Field(default=0.0, description="Average words per sentence")
    sentence_length_variance: float = Field(default=0.0, description="Variance in sentence word lengths")
    total_sentences: int = Field(default=0, description="Total sentence count")
    total_words: int = Field(default=0, description="Total word count")
    total_paragraphs: int = Field(default=0, description="Total paragraph count")

    # GROUP 4 — section consistency
    abstract_to_body_similarity: float = Field(default=0.0, description="Jaccard word overlap between abstract and body")
    section_style_variance: float = Field(default=0.0, description="Variance of sentence length across 4 text chunks")

    # GROUP 5 — academic writing
    citation_density: float = Field(default=0.0, description="[N] style citations per 1000 words")
    passive_voice_ratio: float = Field(default=0.0, description="Sentences using passive voice / total sentences")
    hedge_word_ratio: float = Field(default=0.0, description="Hedge word occurrences / total words")


class MLSignal(BaseModel):
    """A single threshold-based writing-anomaly signal.

    Produced by the anomaly scorer from the extracted ``TextFeatures``.
    Severity is one of ``high``/``medium``/``low``; the signal is an
    explainable screening indicator for human review, never a verdict.
    """

    rule: str = Field(description="Rule name, e.g. uniform_sentence_length")
    severity: str = Field(description="high, medium or low")
    message: str = Field(description="Human-readable explanation of the finding")
    evidence: str = Field(description="Feature value and threshold that triggered the rule")
    weight: float = Field(description="Share of the maximum per-signal score")

    @property
    def points(self) -> float:
        """Risk points contributed by this signal's severity."""
        return _SEVERITY_POINTS.get(self.severity, 0.0)


class MLAnalysisResult(BaseModel):
    """Result of the anomaly-scoring stage over a paper's text features.

    Maps the numerical features into explainable signals and a risk
    contribution. The score is a screening signal, never proof of fraud.
    """

    signals: list[MLSignal] = Field(default_factory=list, description="All triggered rules")
    passed_rules: list[str] = Field(default_factory=list, description="Rule names that did not trigger")
    ml_risk_contribution: float = Field(default=0.0, description="Points contributed to the final risk score, 0-100")
    confidence: float = Field(default=0.0, description="Confidence in the analysis based on text availability, 0-1")
    features_used: TextFeatures = Field(description="The raw features that were analyzed")
    summary: str = Field(default="", description="Human-readable summary of the detected patterns")


class MLAnalysisRequest(BaseModel):
    """Request body for the standalone ML analysis endpoint.

    ``full_text`` is required; ``pages`` uses the same shape as the PDF
    parser's page output (a list of dicts with ``page_number`` and ``text``).
    """

    full_text: str
    abstract: str = Field(default="", description="The paper's abstract, may be empty")
    pages: list[dict] = Field(default_factory=list, description="Page-wise text from pdf_parser output")