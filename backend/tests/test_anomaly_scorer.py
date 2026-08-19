"""Tests for the threshold-based anomaly scoring engine and its
integration with the report generator.

All tests are purely local — no network calls and no files are read.
"""

from app.schemas.consistency import ConsistencyFlag, ConsistencyReport
from app.schemas.ml import MLAnalysisResult, MLSignal, TextFeatures
from app.schemas.report import ReportInput
from app.services.ml.anomaly_scorer import analyze_text
from app.services.report_generator import generate_report

_ALL_RULES = [
    "uniform_sentence_length",
    "vocabulary_inflation",
    "abstract_body_mismatch",
    "style_shifting",
    "missing_hedging",
    "missing_citations",
    "low_readability",
    "high_readability",
    "passive_voice_absent",
    "short_paper",
]


def _features(**overrides: float | int) -> TextFeatures:
    """A 'normal' paper with no rule breached, unless overridden."""
    defaults: dict = {
        "flesch_reading_ease": 40.0,
        "flesch_kincaid_grade": 10.0,
        "gunning_fog_index": 12.0,
        "automated_readability_index": 11.0,
        "unique_word_ratio": 0.6,
        "avg_word_length": 5.5,
        "rare_word_ratio": 0.05,
        "avg_sentence_length": 18.0,
        "sentence_length_variance": 10.0,
        "total_sentences": 80,
        "total_words": 1500,
        "total_paragraphs": 10,
        "abstract_to_body_similarity": 0.5,
        "section_style_variance": 10.0,
        "citation_density": 3.0,
        "passive_voice_ratio": 0.3,
        "hedge_word_ratio": 0.01,
    }
    defaults.update(overrides)
    return TextFeatures(**defaults)


def _triggered(features: TextFeatures) -> set[str]:
    return {signal.rule for signal in analyze_text(features).signals}


# Individual rules


def test_uniform_sentence_length_triggers_below_threshold():
    features = _features(sentence_length_variance=2.0)

    assert "uniform_sentence_length" in _triggered(features)


def test_uniform_sentence_length_does_not_trigger_at_threshold():
    features = _features(sentence_length_variance=5.0)

    assert "uniform_sentence_length" not in _triggered(features)


def test_vocabulary_inflation_triggers_above_threshold():
    features = _features(unique_word_ratio=0.9)

    assert "vocabulary_inflation" in _triggered(features)


def test_abstract_body_mismatch_triggers_below_threshold():
    features = _features(abstract_to_body_similarity=0.05)

    assert "abstract_body_mismatch" in _triggered(features)


def test_style_shifting_triggers_above_threshold():
    features = _features(section_style_variance=60.0)

    assert "style_shifting" in _triggered(features)


def test_missing_hedging_triggers_below_threshold():
    features = _features(hedge_word_ratio=0.0)

    assert "missing_hedging" in _triggered(features)


def test_missing_citations_triggers_below_threshold():
    features = _features(citation_density=0.2)

    assert "missing_citations" in _triggered(features)


def test_low_readability_triggers_below_threshold():
    features = _features(flesch_reading_ease=5.0)

    assert "low_readability" in _triggered(features)


def test_high_readability_triggers_above_threshold():
    features = _features(flesch_reading_ease=85.0)

    assert "high_readability" in _triggered(features)


def test_passive_voice_absent_triggers_below_threshold():
    features = _features(passive_voice_ratio=0.01)

    assert "passive_voice_absent" in _triggered(features)


def test_short_paper_triggers_below_threshold():
    features = _features(total_words=500)

    assert "short_paper" in _triggered(features)


# Normal input


def test_normal_features_produce_no_signals():
    result = analyze_text(_features())

    assert result.signals == []
    assert result.passed_rules == _ALL_RULES


def test_all_zero_features_run_normally_and_do_not_crash():
    result = analyze_text(TextFeatures())

    assert isinstance(result.signals, list)
    assert result.passed_rules == [
        "vocabulary_inflation",
        "style_shifting",
        "high_readability",
    ]


# Risk contribution


def test_ml_risk_contribution_one_high_signal():
    result = analyze_text(_features(abstract_to_body_similarity=0.05))

    assert result.ml_risk_contribution == 15.0


def test_ml_risk_contribution_one_medium_signal():
    result = analyze_text(_features(citation_density=0.2))

    assert result.ml_risk_contribution == 8.0


def test_ml_risk_contribution_one_low_signal():
    result = analyze_text(_features(hedge_word_ratio=0.0))

    assert result.ml_risk_contribution == 3.0


def test_ml_risk_contribution_never_exceeds_cap():
    features = _features(
        sentence_length_variance=1.0,
        unique_word_ratio=0.9,
        abstract_to_body_similarity=0.05,
        section_style_variance=60.0,
        hedge_word_ratio=0.0,
        citation_density=0.2,
        flesch_reading_ease=5.0,
        passive_voice_ratio=0.01,
        total_words=500,
    )
    result = analyze_text(features)

    assert len(result.signals) == 9
    assert result.ml_risk_contribution == 78.0
    assert result.ml_risk_contribution <= 100.0


# Confidence


def test_confidence_low_below_500_words():
    result = analyze_text(_features(total_words=400))

    assert result.confidence == 0.3


def test_confidence_medium_between_500_and_1000_words():
    result = analyze_text(_features(total_words=700))

    assert result.confidence == 0.5


def test_confidence_full_at_1000_words_or_more():
    result = analyze_text(_features(total_words=1500))

    assert result.confidence == 0.8


# Summary templates


def test_summary_matches_template_for_zero_signals():
    result = analyze_text(_features())

    assert result.summary == "No suspicious writing patterns detected."


def test_summary_matches_template_for_one_signal():
    result = analyze_text(_features(citation_density=0.2))

    assert result.summary == "Minor writing anomalies detected. Low concern."


def test_summary_matches_template_for_three_signals():
    features = _features(
        sentence_length_variance=2.0,
        hedge_word_ratio=0.001,
        citation_density=0.2,
    )
    result = analyze_text(features)

    assert len(result.signals) == 3
    assert result.summary == "Several writing pattern anomalies found."


def test_summary_matches_template_for_five_signals():
    features = _features(
        sentence_length_variance=2.0,
        unique_word_ratio=0.9,
        abstract_to_body_similarity=0.05,
        hedge_word_ratio=0.001,
        citation_density=0.2,
    )
    result = analyze_text(features)

    assert len(result.signals) == 5
    assert result.summary == "Multiple significant writing anomalies detected."


# Result completeness


def test_ml_analysis_result_has_all_required_fields():
    result = analyze_text(_features())

    dumped = result.model_dump()
    for value in dumped.values():
        assert value is not None
    assert result.features_used == _features()
    assert 0.0 <= result.confidence <= 1.0


# Report generator integration


def _signal(rule: str = "uniform_sentence_length", severity: str = "medium") -> MLSignal:
    return MLSignal(rule=rule, severity=severity, message="msg", evidence="ev", weight=0.5)


def _ml_result(signals=None, passed=None, contribution=0.0, confidence=0.8) -> MLAnalysisResult:
    return MLAnalysisResult(
        signals=signals or [],
        passed_rules=passed or [],
        ml_risk_contribution=contribution,
        confidence=confidence,
        features_used=_features(),
        summary="summary",
    )


def _input(consistency=None, ml=None) -> ReportInput:
    return ReportInput(
        analysis_id="test-id",
        paper_title="Test Paper",
        paper_authors=["Jane Doe"],
        consistency_report=consistency,
        ml_results=ml,
    )


def test_ml_results_none_excludes_ml_from_modules_used():
    report = generate_report(_input())

    assert "ml" not in report.modules_used


def test_ml_results_provided_adds_ml_to_modules_used():
    report = generate_report(_input(ml=_ml_result()))

    assert "ml" in report.modules_used


def test_ml_signals_converted_to_risk_signals_with_source_ml():
    report = generate_report(_input(ml=_ml_result(signals=[_signal()])))

    assert len(report.signals) == 1
    assert report.signals[0].source == "ml"
    assert report.signals[0].severity == "medium"
    assert report.signals[0].message == "msg"
    assert report.signals[0].evidence == "ev"
    assert report.signals[0].weight == 0.5


def test_ml_contribution_added_to_total_score():
    consistency = ConsistencyReport(
        flags=[ConsistencyFlag(rule="date_consistency", severity="high", message="m", evidence="e")],
        warnings=[],
        passed_checks=[],
        consistency_score=1.0,
    )
    ml = _ml_result(signals=[_signal(severity="high")], contribution=15.0)
    report = generate_report(_input(consistency=consistency, ml=ml))

    assert report.risk_score == 30.0


def test_ml_passed_rules_added_to_passed_checks():
    ml = _ml_result(passed=["uniform_sentence_length", "vocabulary_inflation"])
    report = generate_report(_input(ml=ml))

    assert report.passed_checks == ["uniform_sentence_length", "vocabulary_inflation"]


def test_confidence_capped_at_085_when_consistency_and_ml_run():
    consistency = ConsistencyReport(
        flags=[],
        warnings=[],
        passed_checks=[],
        consistency_score=1.0,
    )
    ml = _ml_result(confidence=0.8)
    report = generate_report(_input(consistency=consistency, ml=ml))

    assert report.confidence == 0.85


def test_confidence_averaged_when_consistency_and_ml_run():
    consistency = ConsistencyReport(
        flags=[],
        warnings=[],
        passed_checks=[],
        consistency_score=0.6,
    )
    ml = _ml_result(confidence=0.8)
    report = generate_report(_input(consistency=consistency, ml=ml))

    assert report.confidence == 0.7


def test_only_ml_uses_ml_confidence():
    ml = _ml_result(confidence=0.8)
    report = generate_report(_input(ml=ml))

    assert report.confidence == 0.8
    assert report.modules_used == ["ml"]