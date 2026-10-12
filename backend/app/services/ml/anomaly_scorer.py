"""Threshold-based anomaly scoring engine for extracted text features.

Maps the numerical ``TextFeatures`` from Phase 1 to explainable risk
signals using fixed thresholds. Each rule inspects one or more features;
a breached threshold produces an ``MLSignal`` with a human-readable
message and evidence. Signals are screening indicators for human review,
never a fake-paper verdict.

The final ``MLAnalysisResult`` carries the triggered signals, the rules
that passed, a risk contribution (high=15 / medium=8 / low=3 points,
capped at 100) and a confidence based on how much text was available.
"""

from typing import Callable

from app.schemas.ml import MLAnalysisResult, MLSignal, TextFeatures

_MAX_RISK_CONTRIBUTION = 100.0

# Thresholds
_SENTENCE_VARIANCE_THRESHOLD = 5.0
_UNIQUE_WORD_THRESHOLD = 0.80
_ABSTRACT_BODY_THRESHOLD = 0.15
_SECTION_VARIANCE_THRESHOLD = 50.0
_HEDGE_THRESHOLD = 0.002
_CITATION_THRESHOLD = 0.5
_LOW_READABILITY_THRESHOLD = 10.0
_HIGH_READABILITY_THRESHOLD = 80.0
_PASSIVE_THRESHOLD = 0.05
_SHORT_PAPER_THRESHOLD = 1000

# Confidence by text availability
_CONFIDENCE_SHORT = 0.3  # total_words < 500
_CONFIDENCE_MEDIUM = 0.5  # total_words < 1000
_CONFIDENCE_FULL = 0.8  # total_words >= 1000

# Weight per rule (share of the maximum per-signal score)
_WEIGHT_HIGH = 1.0
_WEIGHT_MEDIUM = 0.5
_WEIGHT_LOW = 0.2


def _uniform_sentence_length(features: TextFeatures) -> MLSignal | None:
    value = features.sentence_length_variance
    if value < _SENTENCE_VARIANCE_THRESHOLD:
        return MLSignal(
            rule="uniform_sentence_length",
            severity="medium",
            message="Sentence length variance is unusually low, suggesting AI-generated or templated writing",
            evidence=f"Sentence length variance: {value:.2f} (threshold: {_SENTENCE_VARIANCE_THRESHOLD:.1f})",
            weight=_WEIGHT_MEDIUM,
        )
    return None


def _vocabulary_inflation(features: TextFeatures) -> MLSignal | None:
    value = features.unique_word_ratio
    if value > _UNIQUE_WORD_THRESHOLD:
        return MLSignal(
            rule="vocabulary_inflation",
            severity="medium",
            message="Unusually high unique word ratio suggests text may be aggregated from multiple unrelated sources",
            evidence=f"Unique word ratio: {value:.2f} (threshold: {_UNIQUE_WORD_THRESHOLD:.2f})",
            weight=_WEIGHT_MEDIUM,
        )
    return None


def _abstract_body_mismatch(features: TextFeatures) -> MLSignal | None:
    value = features.abstract_to_body_similarity
    if value is None:
        return MLSignal(
            rule="abstract_body_mismatch",
            severity="low",
            message="Abstract-body similarity could not be evaluated due to missing or unverified abstract",
            evidence="Abstract unavailable",
            weight=0.0,
            status="not_evaluable",
        )
    if value < _ABSTRACT_BODY_THRESHOLD:
        return MLSignal(
            rule="abstract_body_mismatch",
            severity="high",
            message="Abstract content is significantly different from paper body — may indicate a mismatched or fabricated abstract",
            evidence=f"Abstract-body similarity: {value:.2f} (threshold: {_ABSTRACT_BODY_THRESHOLD:.2f})",
            weight=_WEIGHT_HIGH,
            status="triggered",
        )
    return None


def _style_shifting(features: TextFeatures) -> MLSignal | None:
    value = features.section_style_variance
    if value > _SECTION_VARIANCE_THRESHOLD:
        return MLSignal(
            rule="style_shifting",
            severity="high",
            message="High writing style variance between sections suggests content may have been copied from multiple different sources",
            evidence=f"Section style variance: {value:.2f} (threshold: {_SECTION_VARIANCE_THRESHOLD:.1f})",
            weight=_WEIGHT_HIGH,
        )
    return None


def _missing_hedging(features: TextFeatures) -> MLSignal | None:
    value = features.hedge_word_ratio
    if value < _HEDGE_THRESHOLD:
        return MLSignal(
            rule="missing_hedging",
            severity="low",
            message="Very few hedging words found — academic papers typically qualify their claims with words like 'may', 'suggests', 'appears'",
            evidence=f"Hedge word ratio: {value:.4f} (threshold: {_HEDGE_THRESHOLD:.3f})",
            weight=_WEIGHT_LOW,
        )
    return None


def _missing_citations(features: TextFeatures) -> MLSignal | None:
    value = features.citation_density
    if value < _CITATION_THRESHOLD:
        return MLSignal(
            rule="missing_citations",
            severity="medium",
            message="Low citation density — fewer than 0.5 citations per 1000 words, which is unusually low for an academic paper",
            evidence=f"Citation density: {value:.2f} per 1000 words (threshold: {_CITATION_THRESHOLD:.1f})",
            weight=_WEIGHT_MEDIUM,
        )
    return None


def _low_readability(features: TextFeatures) -> MLSignal | None:
    value = features.flesch_reading_ease
    if value < _LOW_READABILITY_THRESHOLD:
        return MLSignal(
            rule="low_readability",
            severity="low",
            message="Extremely low readability score may indicate incoherent or machine-generated content",
            evidence=f"Flesch reading ease: {value:.2f} (threshold: {_LOW_READABILITY_THRESHOLD:.1f})",
            weight=_WEIGHT_LOW,
        )
    return None


def _high_readability(features: TextFeatures) -> MLSignal | None:
    value = features.flesch_reading_ease
    if value > _HIGH_READABILITY_THRESHOLD:
        return MLSignal(
            rule="high_readability",
            severity="low",
            message="Unusually high readability for an academic paper — writing may be too simplistic or non-technical",
            evidence=f"Flesch reading ease: {value:.2f} (threshold: {_HIGH_READABILITY_THRESHOLD:.1f})",
            weight=_WEIGHT_LOW,
        )
    return None


def _passive_voice_absent(features: TextFeatures) -> MLSignal | None:
    value = features.passive_voice_ratio
    if value < _PASSIVE_THRESHOLD:
        return MLSignal(
            rule="passive_voice_absent",
            severity="low",
            message="Very low passive voice usage — academic papers typically use passive constructions extensively",
            evidence=f"Passive voice ratio: {value:.2f} (threshold: {_PASSIVE_THRESHOLD:.2f})",
            weight=_WEIGHT_LOW,
        )
    return None


def _short_paper(features: TextFeatures) -> MLSignal | None:
    value = features.total_words
    if value < _SHORT_PAPER_THRESHOLD:
        return MLSignal(
            rule="short_paper",
            severity="high",
            message="Paper contains fewer than 1000 words — insufficient content for a legitimate academic paper",
            evidence=f"Total words: {value} (threshold: {_SHORT_PAPER_THRESHOLD})",
            weight=_WEIGHT_HIGH,
        )
    return None


_RULES: list[tuple[str, Callable[[TextFeatures], MLSignal | None]]] = [
    ("uniform_sentence_length", _uniform_sentence_length),
    ("vocabulary_inflation", _vocabulary_inflation),
    ("abstract_body_mismatch", _abstract_body_mismatch),
    ("style_shifting", _style_shifting),
    ("missing_hedging", _missing_hedging),
    ("missing_citations", _missing_citations),
    ("low_readability", _low_readability),
    ("high_readability", _high_readability),
    ("passive_voice_absent", _passive_voice_absent),
    ("short_paper", _short_paper),
]

_SEVERITY_POINTS = {"high": 15.0, "medium": 8.0, "low": 3.0}

_SUMMARIES = {
    0: "No suspicious writing patterns detected.",
    1: "Minor writing anomalies detected. Low concern.",
    2: "Minor writing anomalies detected. Low concern.",
    3: "Several writing pattern anomalies found.",
    4: "Several writing pattern anomalies found.",
    5: "Multiple significant writing anomalies detected.",
}


def _confidence(total_words: int) -> float:
    """Confidence based on how much text was available to analyze."""
    if total_words < 500:
        return _CONFIDENCE_SHORT
    if total_words < 1000:
        return _CONFIDENCE_MEDIUM
    return _CONFIDENCE_FULL


def _summary(signal_count: int) -> str:
    """Pick the summary template for the number of triggered signals."""
    if signal_count >= 5:
        return _SUMMARIES[5]
    return _SUMMARIES[signal_count]


def analyze_text(features: TextFeatures) -> MLAnalysisResult:
    """Run every rule over the given features and return the analysis."""
    signals: list[MLSignal] = []
    passed_rules: list[str] = []
    not_evaluable_rules: list[str] = []
    for name, check in _RULES:
        signal = check(features)
        if signal is not None:
            if signal.status == "not_evaluable":
                not_evaluable_rules.append(name)
            else:
                signals.append(signal)
        else:
            passed_rules.append(name)

    contribution = sum(s.points for s in signals)
    contribution = round(min(contribution, _MAX_RISK_CONTRIBUTION), 2)

    return MLAnalysisResult(
        signals=signals,
        passed_rules=passed_rules,
        not_evaluable_rules=not_evaluable_rules,
        ml_risk_contribution=contribution,
        confidence=_confidence(features.total_words),
        features_used=features,
        summary=_summary(len(signals)),
    )