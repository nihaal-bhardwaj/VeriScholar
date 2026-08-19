"""Tests for the final report generator and its endpoints."""

from datetime import datetime

from app.schemas.consistency import ConsistencyFlag, ConsistencyReport
from app.schemas.report import ReportInput
from app.services.report_generator import generate_report
from tests.conftest import SAMPLE_PAPER_PAGE_1, SAMPLE_PAPER_PAGE_2, build_pdf


def _flag(severity: str, rule: str = "date_consistency") -> ConsistencyFlag:
    return ConsistencyFlag(rule=rule, severity=severity, message="msg", evidence="ev")


def _consistency(
    flags: list[ConsistencyFlag] | None = None,
    passed: list[str] | None = None,
) -> ConsistencyReport:
    return ConsistencyReport(
        flags=flags or [],
        warnings=[],
        passed_checks=passed or [],
        consistency_score=1.0,
    )


def _input(consistency: ConsistencyReport | None = None) -> ReportInput:
    return ReportInput(
        analysis_id="test-id",
        paper_title="Test Paper",
        paper_authors=["Jane Doe"],
        abstract="Abstract text.",
        keywords=["radar"],
        consistency_report=consistency,
    )


# Scoring


def test_no_modules_run_returns_zero_score_and_confidence():
    report = generate_report(_input())

    assert report.risk_score == 0.0
    assert report.confidence == 0.0
    assert report.risk_level == "low"
    assert report.modules_used == []


def test_one_high_severity_flag_scores_15():
    report = generate_report(_input(_consistency(flags=[_flag("high")])))

    assert report.risk_score == 15.0
    assert report.risk_level == "low"


def test_three_high_severity_flags_scores_45():
    report = generate_report(_input(_consistency(flags=[_flag("high")] * 3)))

    assert report.risk_score == 45.0
    assert report.risk_level == "medium"


def test_six_high_severity_flags_scores_90():
    report = generate_report(_input(_consistency(flags=[_flag("high")] * 6)))

    assert report.risk_score == 90.0
    assert report.risk_level == "critical"


def test_score_never_exceeds_100():
    report = generate_report(_input(_consistency(flags=[_flag("high")] * 10)))

    assert report.risk_score == 100.0


def test_risk_level_thresholds():
    cases = [
        (["medium"] * 2 + ["low"] * 3, "low"),  # 25
        (["high", "medium", "low"], "medium"),  # 26
        (["high"] + ["medium"] * 4 + ["low"], "medium"),  # 50
        (["high"] * 3 + ["low"] * 2, "high"),  # 51
        (["high"] * 5, "high"),  # 75
        (["high"] * 4 + ["medium"] * 2, "critical"),  # 76
    ]
    for severities, expected in cases:
        report = generate_report(
            _input(_consistency(flags=[_flag(s) for s in severities]))
        )
        assert report.risk_level == expected


# Confidence and module bookkeeping


def test_confidence_capped_at_06_when_only_consistency_runs():
    report = generate_report(_input(_consistency(flags=[_flag("medium")])))

    assert report.modules_used == ["consistency"]
    assert report.confidence <= 0.6
    assert report.confidence > 0.0


def test_passed_checks_carried_into_risk_report():
    passed = ["date_consistency: ok", "figure_reference_consistency: ok"]
    report = generate_report(_input(_consistency(passed=passed)))

    assert report.passed_checks == passed


def test_modules_used_contains_consistency_when_report_provided():
    report = generate_report(_input(_consistency()))

    assert report.modules_used == ["consistency"]


def test_modules_used_empty_when_no_modules_provided():
    report = generate_report(_input())

    assert report.modules_used == []


# Summary and metadata


def test_summary_matches_template_for_each_risk_level():
    zero = generate_report(_input())
    assert (
        zero.summary
        == "No suspicious signals were detected. The paper passed all available checks."
    )

    low = generate_report(_input(_consistency(flags=[_flag("low")])))
    assert (
        low.summary
        == "Minor inconsistencies were detected. Human review is recommended but risk is low."
    )

    medium = generate_report(
        _input(_consistency(flags=[_flag("high"), _flag("medium"), _flag("low")]))
    )
    assert (
        medium.summary
        == "Several inconsistencies were found. A human reviewer should examine this paper."
    )

    high = generate_report(
        _input(_consistency(flags=[_flag("high")] * 3 + [_flag("low")] * 2))
    )
    assert (
        high.summary
        == "Multiple significant issues detected. This paper requires careful human review."
    )

    critical = generate_report(
        _input(_consistency(flags=[_flag("high")] * 4 + [_flag("medium")] * 2))
    )
    assert (
        critical.summary
        == "Serious integrity concerns detected. This paper shows multiple high-severity warning signs."
    )


def test_generated_at_is_valid_datetime():
    report = generate_report(_input())

    assert isinstance(report.generated_at, datetime)
    assert report.generated_at.tzinfo is not None


# Endpoints


def test_report_generate_endpoint_returns_200(client):
    payload = {
        "analysis_id": "00000000-0000-0000-0000-000000000000",
        "paper_title": "Test Paper",
        "paper_authors": ["Jane Doe"],
        "abstract": "Abstract text.",
        "keywords": ["radar"],
        "consistency_report": {
            "flags": [
                {
                    "rule": "date_consistency",
                    "severity": "high",
                    "message": "Reference [1] cites a paper from 2024 which is after this paper's year 2021",
                    "evidence": "A. Author, Journal, 2024.",
                }
            ],
            "warnings": [],
            "passed_checks": ["date_consistency: ok"],
            "consistency_score": 0.5,
        },
        "citation_results": None,
        "metadata_results": None,
        "ml_results": None,
    }
    response = client.post("/api/v1/report/generate", json=payload)

    assert response.status_code == 200
    body = response.json()
    assert body["risk_score"] == 15.0
    assert body["risk_level"] == "low"
    assert body["signals"][0]["source"] == "consistency"
    assert body["signals"][0]["weight"] == 1.0
    assert body["modules_used"] == ["consistency"]
    assert body["passed_checks"] == ["date_consistency: ok"]


def test_analyze_full_endpoint_accepts_pdf(client):
    data = build_pdf("", pages=[SAMPLE_PAPER_PAGE_1, SAMPLE_PAPER_PAGE_2])
    response = client.post(
        "/api/v1/analyze/full",
        files={"file": ("sample.pdf", data, "application/pdf")},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["analysis_id"]
    assert body["paper_title"] == "Deep Learning for Iceberg Detection"
    assert body["risk_score"] >= 0.0
    assert body["risk_level"] in {"low", "medium", "high", "critical"}
    assert "consistency" in body["modules_used"]
    assert "ml" in body["modules_used"]
    assert isinstance(body["generated_at"], str)


def test_analyze_full_endpoint_rejects_non_pdf(client):
    response = client.post(
        "/api/v1/analyze/full",
        files={"file": ("notes.txt", b"hello", "text/plain")},
    )

    assert response.status_code == 415
    assert "error" in response.json()
    assert "detail" in response.json()


def test_analyze_full_endpoint_rejects_missing_file(client):
    response = client.post("/api/v1/analyze/full")

    assert response.status_code == 400
    assert "error" in response.json()