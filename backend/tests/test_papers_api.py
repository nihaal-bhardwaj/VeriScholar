"""Tests for the paper extraction endpoint."""

from app.core.config import get_settings
from tests.conftest import SAMPLE_PAPER_PAGE_1, SAMPLE_PAPER_PAGE_2, build_pdf


def test_extract_endpoint_succeeds_with_valid_pdf(client):
    data = build_pdf("", pages=[SAMPLE_PAPER_PAGE_1, SAMPLE_PAPER_PAGE_2])
    response = client.post(
        "/api/v1/papers/extract",
        files={"file": ("sample.pdf", data, "application/pdf")},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "completed"
    assert body["analysis_id"]
    assert body["paper"]["filename"] == "sample.pdf"
    assert body["paper"]["page_count"] == 2
    assert body["paper"]["doi"] == "10.1234/example.2026"
    assert len(body["paper"]["references"]) == 2


def test_non_pdf_file_is_rejected(client):
    response = client.post(
        "/api/v1/papers/extract",
        files={"file": ("notes.txt", b"hello", "text/plain")},
    )

    assert response.status_code == 415
    assert "error" in response.json()
    assert "detail" in response.json()


def test_missing_file_is_rejected(client):
    response = client.post("/api/v1/papers/extract")

    assert response.status_code == 400
    assert "error" in response.json()


def test_empty_pdf_file_is_rejected(client):
    response = client.post(
        "/api/v1/papers/extract",
        files={"file": ("empty.pdf", b"", "application/pdf")},
    )

    assert response.status_code == 400


def test_oversized_file_is_rejected(client):
    settings = get_settings()
    oversized = b"x" * (settings.max_upload_size_bytes + 1)
    response = client.post(
        "/api/v1/papers/extract",
        files={"file": ("big.pdf", oversized, "application/pdf")},
    )

    assert response.status_code == 413


def test_wrong_mime_type_is_rejected(client):
    data = build_pdf("some content")
    response = client.post(
        "/api/v1/papers/extract",
        files={"file": ("paper.pdf", data, "image/png")},
    )

    assert response.status_code == 415


def test_corrupt_pdf_returns_422(client):
    response = client.post(
        "/api/v1/papers/extract",
        files={"file": ("broken.pdf", b"%PDF-1.7 not really a pdf", "application/pdf")},
    )

    assert response.status_code == 422
    body = response.json()
    assert "detail" in body
