"""Tests for ML integration into the all-in-one /analyze/full endpoint."""

from tests.conftest import SAMPLE_PAPER_PAGE_1, SAMPLE_PAPER_PAGE_2, build_pdf


def test_analyze_full_includes_ml_in_modules_used(client):
    data = build_pdf("", pages=[SAMPLE_PAPER_PAGE_1, SAMPLE_PAPER_PAGE_2])
    response = client.post(
        "/api/v1/analyze/full",
        files={"file": ("sample.pdf", data, "application/pdf")},
    )

    assert response.status_code == 200
    body = response.json()
    assert "ml" in body["modules_used"]
    assert "consistency" in body["modules_used"]


def test_analyze_full_can_return_ml_signals(client):
    data = build_pdf("", pages=[SAMPLE_PAPER_PAGE_1, SAMPLE_PAPER_PAGE_2])
    response = client.post(
        "/api/v1/analyze/full",
        files={"file": ("sample.pdf", data, "application/pdf")},
    )

    assert response.status_code == 200
    body = response.json()
    ml_signals = [s for s in body["signals"] if s["source"] == "ml"]
    assert ml_signals
    assert all(s["severity"] in {"high", "medium", "low"} for s in ml_signals)


def test_analyze_full_confidence_is_positive(client):
    data = build_pdf("", pages=[SAMPLE_PAPER_PAGE_1, SAMPLE_PAPER_PAGE_2])
    response = client.post(
        "/api/v1/analyze/full",
        files={"file": ("sample.pdf", data, "application/pdf")},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["confidence"] is not None
    assert body["confidence"] > 0.0