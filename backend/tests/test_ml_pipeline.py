"""Tests for the ML pipeline orchestrator (feature extraction + scoring).

All tests are purely local — no network calls and no files are read.
"""

from app.schemas.ml import MLAnalysisResult
from app.services.ml import ml_pipeline
from app.services.ml.ml_pipeline import run_ml_analysis

_NORMAL_TEXT = (
    "The results are consistent with prior work [1]. Our method was evaluated "
    "on a benchmark dataset [2] and the findings may suggest a relationship "
    "which could possibly be explained by the framework described in [3]. "
    "These observations were measured carefully and are reported in Table 1. "
    "The approach appears robust and generally applicable. "
) * 40


def test_run_ml_analysis_returns_ml_analysis_result_for_normal_text():
    result = run_ml_analysis(_NORMAL_TEXT, "The results are consistent with prior work.", [])

    assert isinstance(result, MLAnalysisResult)
    assert isinstance(result.signals, list)
    assert isinstance(result.passed_rules, list)
    assert 0.0 <= result.confidence <= 1.0
    assert 0.0 <= result.ml_risk_contribution <= 100.0


def test_run_ml_analysis_empty_text_returns_safe_low_confidence_result():
    result = run_ml_analysis("", "", [])

    assert isinstance(result, MLAnalysisResult)
    assert result.confidence == 0.3
    assert any(signal.rule == "short_paper" for signal in result.signals)


def test_run_ml_analysis_returns_correct_type():
    result = run_ml_analysis(_NORMAL_TEXT, "", [])

    assert isinstance(result, MLAnalysisResult)


def test_fallback_result_returned_when_feature_extractor_raises(monkeypatch):
    def _boom(*args, **kwargs):
        raise RuntimeError("extractor exploded")

    monkeypatch.setattr(ml_pipeline, "extract_features", _boom)
    result = run_ml_analysis("some text", "", [])

    assert isinstance(result, MLAnalysisResult)
    assert "unavailable" in result.summary


def test_fallback_result_has_zero_risk_contribution(monkeypatch):
    def _boom(*args, **kwargs):
        raise RuntimeError("extractor exploded")

    monkeypatch.setattr(ml_pipeline, "extract_features", _boom)
    result = run_ml_analysis("some text", "", [])

    assert result.ml_risk_contribution == 0.0


def test_fallback_result_has_zero_confidence(monkeypatch):
    def _boom(*args, **kwargs):
        raise RuntimeError("extractor exploded")

    monkeypatch.setattr(ml_pipeline, "extract_features", _boom)
    result = run_ml_analysis("some text", "", [])

    assert result.confidence == 0.0
    assert result.signals == []
    assert result.passed_rules == []