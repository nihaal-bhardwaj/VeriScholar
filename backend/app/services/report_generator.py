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
    if (
        data.citation_results is not None
        and data.citation_results.get("status") != "unavailable"
    ):
        modules.append("citations")
    if (
        data.metadata_results is not None
        or data.paper_metadata is not None
        or data.metadata_verification is not None
    ):
        modules.append("metadata")
    if data.ml_results is not None:
        modules.append("ml")
    return modules
def _confidence(data: ReportInput, modules: list[str]) -> float:
    """Confidence in the report based on modules and extraction quality."""
    if not modules:
        return 0.0
    if modules == ["ml"]:
        base_conf = data.ml_results.confidence if data.ml_results is not None else 0.0
    elif "consistency" in modules and "ml" in modules:
        consistency_conf = (
            data.consistency_report.consistency_score
            if data.consistency_report is not None
            else 0.0
        )
        ml_conf = data.ml_results.confidence if data.ml_results is not None else 0.0
        base_conf = min(0.85, (consistency_conf + ml_conf) / 2)
    else:
        base_conf = min(
            _CONFIDENCE_BASE + _CONFIDENCE_PER_EXTRA_MODULE * (len(modules) - 1),
            _MAX_CONFIDENCE,
        )
        if modules == ["consistency"]:
            base_conf = min(base_conf, _MAX_CONFIDENCE_SINGLE_MODULE)

    # Factor in extraction quality if provided
    if data.extraction_quality is not None:
        q_status = data.extraction_quality.status
        if q_status == "poor":
            base_conf = min(base_conf, 0.30)
        elif q_status == "degraded":
            base_conf = min(base_conf, 0.55)

    # Factor in metadata verification agreement (boosts confidence in identity)
    meta = data.paper_metadata or data.metadata_results
    if meta and meta.get("matched"):
        base_conf = min(_MAX_CONFIDENCE, base_conf + 0.10)

    return round(min(base_conf, _MAX_CONFIDENCE), 2)


def _summary(score: float, level: str, status: str = "evaluated") -> str:
    """Pick the human-readable summary template for the report."""
    if status == "limited_evidence":
        return (
            "The document could not be fully parsed, so some integrity checks were not evaluable. "
            "Available checks did not reveal conclusive integrity issues."
        )
    if status == "undetermined":
        return (
            "Document extraction quality was insufficient to perform reliable integrity screening. "
            "Manual review of the original PDF is recommended."
        )
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


def _signals_from_citations(citation_results: dict | None) -> list[RiskSignal]:
    """Convert citation verification results into explainable risk signals."""
    if not citation_results or citation_results.get("status") == "unavailable":
        return []

    signals: list[RiskSignal] = []
    verified = citation_results.get("verified", 0)
    unresolved = citation_results.get("unresolved", 0)
    total = verified + unresolved

    if total >= 5:
        unresolved_ratio = unresolved / total
        if unresolved_ratio >= 0.70:
            signals.append(
                RiskSignal(
                    source="citations",
                    severity="high",
                    message=(
                        f"High citation non-resolution rate: {unresolved} of {total} "
                        f"({unresolved_ratio * 100:.0f}%) references could not be verified in Crossref or OpenAlex"
                    ),
                    evidence=f"{verified} verified, {unresolved} unresolved out of {total} checked references",
                    weight=1.0,
                )
            )
        elif unresolved_ratio >= 0.40:
            signals.append(
                RiskSignal(
                    source="citations",
                    severity="medium",
                    message=(
                        f"Substantial portion of citations unverified: {unresolved} of {total} "
                        f"({unresolved_ratio * 100:.0f}%) references could not be confirmed"
                    ),
                    evidence=f"{verified} verified, {unresolved} unresolved out of {total} checked references",
                    weight=round(_SEVERITY_WEIGHTS.get("medium", 0.5333), 4),
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

    citation_signals: list[RiskSignal] = []
    if data.citation_results is not None:
        citation_signals = _signals_from_citations(data.citation_results)

    signals = consistency_signals + ml_signals + citation_signals

    score = 0.0
    for signal in consistency_signals + citation_signals:
        score += _SEVERITY_POINTS.get(signal.severity, 0.0)
    if data.ml_results is not None:
        score += data.ml_results.ml_risk_contribution
    score = round(min(score, _MAX_RISK_SCORE), 2)

    level = _risk_level(score)

    # Determine assessment status based on extraction quality and score
    assessment_status = "evaluated"
    if data.extraction_quality is not None:
        if data.extraction_quality.status == "poor":
            assessment_status = "undetermined" if score < 40 else "limited_evidence"
        elif data.extraction_quality.status == "degraded" and score < 40:
            assessment_status = "limited_evidence"

    passed_checks: list[str] = []
    if data.consistency_report is not None:
        passed_checks.extend(data.consistency_report.passed_checks)
    if data.ml_results is not None:
        passed_checks.extend(data.ml_results.passed_rules)
    if data.citation_results is not None and data.citation_results.get("status") != "unavailable":
        v = data.citation_results.get("verified", 0)
        u = data.citation_results.get("unresolved", 0)
        t = v + u
        if t > 0 and (v / t) >= 0.5:
            passed_checks.append(
                f"citation_verification: {v} of {t} ({v/t*100:.0f}%) sampled references verified in public bibliographic indexes"
            )

    meta = data.paper_metadata or data.metadata_verification or data.metadata_results

    return RiskReport(
        analysis_id=data.analysis_id,
        paper_title=data.paper_title,
        paper_authors=list(data.paper_authors),
        risk_score=score,
        risk_level=level,
        confidence=_confidence(data, modules),
        summary=_summary(score, level, assessment_status),
        signals=signals,
        passed_checks=passed_checks,
        modules_used=modules,
        extraction_quality=data.extraction_quality,
        assessment_status=assessment_status,
        paper_metadata=meta,
        metadata_verification=meta,
        citation_results=data.citation_results,
        generated_at=datetime.now(timezone.utc),
    )