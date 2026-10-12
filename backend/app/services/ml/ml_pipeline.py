"""ML analysis pipeline orchestrator.

Chains the Phase 1 feature extractor and the Phase 2 anomaly scorer into
one callable used by the API layer. Any internal failure is caught and
converted into a safe, empty result so the main analysis pipeline never
crashes because the ML stage failed.
"""

import logging
import os
import joblib

from app.core.config import get_settings
from app.schemas.ml import MLAnalysisResult, TextFeatures, MLSignal
from app.services.ml.anomaly_scorer import analyze_text
from app.services.ml.feature_extractor import extract_features

logger = logging.getLogger("mini-project.ml")

_UNAVAILABLE_SUMMARY = "ML analysis unavailable due to an internal error."

_MODEL_PATH = os.path.join(os.path.dirname(__file__), '..', '..', '..', '..', 'ml', 'saved_models', 'rf_baseline.joblib')
try:
    _baseline_clf = joblib.load(_MODEL_PATH)
    logger.info("Successfully loaded ML baseline model.")
except Exception as e:
    logger.info(f"ML baseline model not loaded from {_MODEL_PATH}: {e}")
    _baseline_clf = None

def _fallback_result() -> MLAnalysisResult:
    """A safe empty result returned when the ML analysis cannot run."""
    return MLAnalysisResult(
        signals=[],
        passed_rules=[],
        not_evaluable_rules=[],
        ml_risk_contribution=0.0,
        confidence=0.0,
        features_used=TextFeatures(),
        summary=_UNAVAILABLE_SUMMARY,
    )


def run_ml_analysis(
    full_text: str,
    abstract: str,
    pages: list[dict],
    extraction_quality: dict | None = None,
) -> MLAnalysisResult:
    """Run the full ML text analysis for a paper.

    Empty input is processed normally. Any unexpected exception is logged and
    replaced with a safe empty result — the caller never sees an error.
    """
    try:
        # 1. Run Heuristics
        features = extract_features(full_text, abstract, pages)
        result = analyze_text(features)

        # 2. Add Baseline ML Score
        settings = get_settings()
        if _baseline_clf and full_text.strip():
            probabilities = _baseline_clf.predict_proba([full_text])
            risk_prob = float(probabilities[0][1])

            # Demo override only when explicitly enabled in configuration
            if settings.demo_mode:
                risk_prob = 0.99

            if risk_prob >= 0.40:
                severity = "high" if risk_prob > 0.6 else "medium"
                signal = MLSignal(
                    rule="ml_baseline_classifier",
                    severity=severity,
                    message="The TF-IDF Machine Learning model determined a high probability for suspicious text patterns.",
                    evidence=f"Suspicion Probability: {risk_prob:.2f}",
                    weight=1.0 if severity == "high" else 0.5,
                    status="triggered",
                )
                result.signals.append(signal)

                added_points = 85.0 if severity == "high" else 55.0
                result.ml_risk_contribution = min(100.0, result.ml_risk_contribution + added_points)
                result.summary += f" ML Baseline flagged suspicious pattern ({risk_prob:.0%} confidence)."
            else:
                result.passed_rules.append("ml_baseline_classifier")

        # 3. Extraction Quality Gate: if extraction was degraded, bound confidence
        if extraction_quality is not None:
            q_status = extraction_quality.get("status")
            if q_status == "poor":
                result.confidence = min(result.confidence, 0.25)
            elif q_status == "degraded":
                result.confidence = min(result.confidence, 0.45)

        return result
    except Exception:
        logger.exception("ML analysis failed; returning safe fallback result")
        return _fallback_result()
