"""ML analysis pipeline orchestrator.

Chains the Phase 1 feature extractor and the Phase 2 anomaly scorer into
one callable used by the API layer. Any internal failure is caught and
converted into a safe, empty result so the main analysis pipeline never
crashes because the ML stage failed.
"""

import logging

from app.schemas.ml import MLAnalysisResult, TextFeatures
from app.services.ml.anomaly_scorer import analyze_text
from app.services.ml.feature_extractor import extract_features

logger = logging.getLogger("mini-project.ml")

_UNAVAILABLE_SUMMARY = "ML analysis unavailable due to an internal error."


def _fallback_result() -> MLAnalysisResult:
    """A safe empty result returned when the ML analysis cannot run."""
    return MLAnalysisResult(
        signals=[],
        passed_rules=[],
        ml_risk_contribution=0.0,
        confidence=0.0,
        features_used=TextFeatures(),
        summary=_UNAVAILABLE_SUMMARY,
    )


def run_ml_analysis(
    full_text: str,
    abstract: str,
    pages: list[dict],
) -> MLAnalysisResult:
    """Run the full ML text analysis for a paper.

    Empty input is processed normally (it yields a low-confidence result
    with a ``short_paper`` signal). Any unexpected exception is logged and
    replaced with a safe empty result — the caller never sees an error.
    """
    try:
        features = extract_features(full_text, abstract, pages)
        return analyze_text(features)
    except Exception:
        logger.exception("ML analysis failed; returning safe fallback result")
        return _fallback_result()