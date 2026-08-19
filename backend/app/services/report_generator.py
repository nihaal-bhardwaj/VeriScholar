"""Final report combiner.

Takes outputs from all analysis modules and produces one unified risk
report with a score. The citation, metadata and ML modules are optional
placeholders for now — the generator works when they are `None`.

The report is an explainable screening signal for human review, never a
fake-paper verdict.
"""

from datetime import datetime, timezone

from app.schemas.consistency import ConsistencyReport
from app.schemas.ml import MLAnalysisResult
from app.schemas.report import ReportInput, RiskReport, RiskSignal

_SEVERITY_POINTS = {"high": 15.0, "medium": 8.0, "low": 3.0}
_SEVERITY_WEIGHTS = {"high": 1.0, "medium": 8.0 / 15.0, "low": 3.0 / 15.0}

_MAX_RISK_SCORE = 100.0
_MAX_CONFIDENCE_SINGLE_MODULE = 0.6
_CONFIDENCE_BASE = 0.4
_CONFIDENCE_PER_EXTRA_MODULE = 0.15
_MAX_CONFIDENCE = 0.95

_SUMMARIES = {
    "zero": "No suspicious signals were detected. The paper passed all available checks.",
    "low": "Minor inconsistencies were detected. Human review is recommended but risk is low.",
    "medium": "Several inconsistencies were found. A human reviewer should examine this paper.",
    "high": "Multiple significant issues detected. This paper requires careful human review.",
    "critical": "Serious integrity concerns detected. This paper shows multiple high-severity warning signs.",
}


def _risk_level(score: float) -> str:
    """Map a risk score to a risk level."""
    if score <= 25:
        return "low"
    if score <= 50:
        return "medium"
    if score <= 75:
        return "high"
    return "critical"


def _modules_used(data: ReportInput) -> list[str]:
    """List of modules that contributed to this report."""
    modules: list[str] = []
    if data.consistency_report is not None:
        modules.append("consistency")
    if data.citation_results is not None:
        modules.append("citations")
    if data.metadata_results is not None:
        modules.append("metadata")
    if data.ml_results is not None:
        modules.append("ml")
    return modules


def _confidence(data: ReportInput, modules: list[str]) -> float:
    """Confidence in the report based on which modules contributed.

    When only the ML module runs, the ML module's own confidence is used.
    When both consistency and ML run, the two confidences are averaged and
    capped at 0.85. Other combinations keep the generic module-count based
    confidence.
    """
    if not modules:
        return 0.0
    if modules == ["ml"]:
        return data.ml_results.confidence if data.ml_results is not None else 0.0
    if "consistency" in modules and "ml" in modules:
        consistency_conf = (
            data.consistency_report.consistency_score
            if data.consistency_report is not None
            else 0.0
        )
        ml_conf = data.ml_results.confidence if data.ml_results is not None else 0.0
        return round(min(0.85, (consistency_conf + ml_conf) / 2), 2)
    confidence = min(
        _CONFIDENCE_BASE + _CONFIDENCE_PER_EXTRA_MODULE * (len(modules) - 1),
        _MAX_CONFIDENCE,
    )
    if modules == ["consistency"]:
        confidence = min(confidence, _MAX_CONFIDENCE_SINGLE_MODULE)
    return round(confidence, 2)


def _summary(score: float, level: str) -> str:
    """Pick the human-readable summary template for the report."""
    if score == 0.0:
        return _SUMMARIES["zero"]
    return _SUMMARIES[level]


def _signals_from_consistency(report: ConsistencyReport) -> list[RiskSignal]:
    """Convert consistency flags into risk signals."""
    signals: list[RiskSignal] = []
    for flag in report.flags:
        signals.append(
            RiskSignal(
                source="consistency",
                severity=flag.severity,
                message=flag.message,
                evidence=flag.evidence,
                weight=round(_SEVERITY_WEIGHTS.get(flag.severity, 0.0), 4),
            )
        )
    return signals


def _signals_from_ml(result: MLAnalysisResult) -> list[RiskSignal]:
    """Convert ML anomaly signals into risk signals."""
    signals: list[RiskSignal] = []
    for signal in result.signals:
        signals.append(
            RiskSignal(
                source="ml",
                severity=signal.severity,
                message=signal.message,
                evidence=signal.evidence,
                weight=round(signal.weight, 4),
            )
        )
    return signals


def generate_report(data: ReportInput) -> RiskReport:
    """Combine all module outputs into a single risk report."""
    modules = _modules_used(data)

    consistency_signals: list[RiskSignal] = []
    if data.consistency_report is not None:
        consistency_signals = _signals_from_consistency(data.consistency_report)

    ml_signals: list[RiskSignal] = []
    if data.ml_results is not None:
        ml_signals = _signals_from_ml(data.ml_results)

    signals = consistency_signals + ml_signals

    score = 0.0
    for signal in consistency_signals:
        score += _SEVERITY_POINTS.get(signal.severity, 0.0)
    if data.ml_results is not None:
        score += data.ml_results.ml_risk_contribution
    score = round(min(score, _MAX_RISK_SCORE), 2)

    level = _risk_level(score)
    passed_checks: list[str] = []
    if data.consistency_report is not None:
        passed_checks.extend(data.consistency_report.passed_checks)
    if data.ml_results is not None:
        passed_checks.extend(data.ml_results.passed_rules)

    return RiskReport(
        analysis_id=data.analysis_id,
        paper_title=data.paper_title,
        paper_authors=list(data.paper_authors),
        risk_score=score,
        risk_level=level,
        confidence=_confidence(data, modules),
        summary=_summary(score, level),
        signals=signals,
        passed_checks=passed_checks,
        modules_used=modules,
        generated_at=datetime.now(timezone.utc),
    )