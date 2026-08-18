"""Tests for the paper extraction endpoint."""

from app.core.config import get_settings
from app.services.pdf_parser import parse_pdf_bytes
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


def test_reference_schema_fields_are_unchanged(client):
    data = build_pdf("", pages=[SAMPLE_PAPER_PAGE_1, SAMPLE_PAPER_PAGE_2])
    response = client.post(
        "/api/v1/papers/extract",
        files={"file": ("sample.pdf", data, "application/pdf")},
    )

    assert response.status_code == 200
    references = response.json()["paper"]["references"]
    assert references
    for entry in references:
        assert set(entry.keys()) == {"number", "raw_text", "doi"}
        assert isinstance(entry["number"], int)
        assert isinstance(entry["raw_text"], str) and entry["raw_text"]
        assert entry["doi"] is None or isinstance(entry["doi"], str)


def test_title_and_authors_are_exposed_in_response(client):
    page_1 = (
        "Iceberg Radar Survey\n"
        "John Doe, Jane Smith\n"
        "Abstract\n"
        "We study radar imagery for iceberg detection.\n"
        "Keywords: iceberg, radar\n"
        "1. Introduction\n"
        "Body text here.\n"
    )
    page_2 = "2. Method\nMore content here.\n"
    data = build_pdf("", pages=[page_1, page_2])

    response = client.post(
        "/api/v1/papers/extract",
        files={"file": ("titled.pdf", data, "application/pdf")},
    )

    assert response.status_code == 200
    paper = response.json()["paper"]
    parsed = parse_pdf_bytes(data, "titled.pdf")
    assert paper["title"] == parsed.title == "Iceberg Radar Survey"
    assert paper["authors"] == parsed.authors == ["John Doe", "Jane Smith"]


def test_sample_paper_title_and_authors_flow_through_response(client):
    data = build_pdf("", pages=[SAMPLE_PAPER_PAGE_1, SAMPLE_PAPER_PAGE_2])
    response = client.post(
        "/api/v1/papers/extract",
        files={"file": ("sample.pdf", data, "application/pdf")},
    )

    assert response.status_code == 200
    paper = response.json()["paper"]
    assert paper["title"] == "Deep Learning for Iceberg Detection"
    assert paper["authors"] == []


def test_default_title_and_authors_when_front_matter_empty(client):
    data = build_pdf("Abstract\nBody text here.\n")
    response = client.post(
        "/api/v1/papers/extract",
        files={"file": ("plain.pdf", data, "application/pdf")},
    )

    assert response.status_code == 200
    paper = response.json()["paper"]
    assert paper["title"] is None
    assert paper["authors"] == []


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


# Keywords extraction tests


def test_keywords_comma_separated_are_extracted(client):
    """Test that comma-separated keywords are correctly extracted and split."""
    page = (
        "Sample Paper\n"
        "Abstract\n"
        "This is abstract text.\n"
        "Keywords: machine learning, neural networks, classification\n"
        "1. Introduction\n"
        "Body text.\n"
    )
    data = build_pdf("", pages=[page])

    response = client.post(
        "/api/v1/papers/extract",
        files={"file": ("keywords.pdf", data, "application/pdf")},
    )

    assert response.status_code == 200
    paper = response.json()["paper"]
    assert paper["keywords"] == ["machine learning", "neural networks", "classification"]


def test_keywords_semicolon_separated_are_extracted(client):
    """Test that semicolon-separated keywords are correctly extracted and split."""
    page = (
        "Sample Paper\n"
        "Abstract\n"
        "This is abstract text.\n"
        "Keywords: deep learning; computer vision; object detection\n"
        "1. Introduction\n"
        "Body text.\n"
    )
    data = build_pdf("", pages=[page])

    response = client.post(
        "/api/v1/papers/extract",
        files={"file": ("keywords.pdf", data, "application/pdf")},
    )

    assert response.status_code == 200
    paper = response.json()["paper"]
    assert paper["keywords"] == ["deep learning", "computer vision", "object detection"]


def test_keywords_spanning_multiple_lines_are_extracted(client):
    """Test that keywords spanning multiple lines are correctly extracted."""
    page = (
        "Sample Paper\n"
        "Abstract\n"
        "This is abstract text.\n"
        "Keywords: machine learning,\n"
        "neural networks,\n"
        "deep learning,\n"
        "classification algorithms\n"
        "1. Introduction\n"
        "Body text.\n"
    )
    data = build_pdf("", pages=[page])

    response = client.post(
        "/api/v1/papers/extract",
        files={"file": ("keywords.pdf", data, "application/pdf")},
    )

    assert response.status_code == 200
    paper = response.json()["paper"]
    assert paper["keywords"] == [
        "machine learning",
        "neural networks",
        "deep learning",
        "classification algorithms",
    ]


def test_keywords_empty_list_when_no_keywords_section(client):
    """Test that an empty list is returned when no keywords section exists."""
    page = (
        "Sample Paper\n"
        "Abstract\n"
        "This is abstract text without keywords section.\n"
        "1. Introduction\n"
        "Body text.\n"
    )
    data = build_pdf("", pages=[page])

    response = client.post(
        "/api/v1/papers/extract",
        files={"file": ("no_keywords.pdf", data, "application/pdf")},
    )

    assert response.status_code == 200
    paper = response.json()["paper"]
    assert paper["keywords"] == []


def test_keywords_empty_list_when_section_is_empty(client):
    """Test that an empty list is returned when keywords section exists but is empty."""
    page = (
        "Sample Paper\n"
        "Abstract\n"
        "This is abstract text.\n"
        "Keywords:\n"
        "1. Introduction\n"
        "Body text.\n"
    )
    data = build_pdf("", pages=[page])

    response = client.post(
        "/api/v1/papers/extract",
        files={"file": ("empty_keywords.pdf", data, "application/pdf")},
    )

    assert response.status_code == 200
    paper = response.json()["paper"]
    assert paper["keywords"] == []


def test_index_terms_variant_is_extracted(client):
    """Test that 'Index Terms:' variant also extracts keywords correctly."""
    page = (
        "Sample Paper\n"
        "Abstract\n"
        "This is abstract text.\n"
        "Index Terms: distributed systems, fault tolerance, consensus algorithms\n"
        "1. Introduction\n"
        "Body text.\n"
    )
    data = build_pdf("", pages=[page])

    response = client.post(
        "/api/v1/papers/extract",
        files={"file": ("index_terms.pdf", data, "application/pdf")},
    )

    assert response.status_code == 200
    paper = response.json()["paper"]
    assert paper["keywords"] == ["distributed systems", "fault tolerance", "consensus algorithms"]


def test_keywords_stops_at_numbered_section_heading(client):
    """Test that keyword extraction stops at numbered section headings."""
    page = (
        "Sample Paper\n"
        "Abstract\n"
        "This is abstract text.\n"
        "Keywords: machine learning, neural networks\n"
        "1. Introduction\n"
        "This text should not be extracted as keywords.\n"
    )
    data = build_pdf("", pages=[page])

    response = client.post(
        "/api/v1/papers/extract",
        files={"file": ("keywords_stop.pdf", data, "application/pdf")},
    )

    assert response.status_code == 200
    paper = response.json()["paper"]
    assert paper["keywords"] == ["machine learning", "neural networks"]


def test_keywords_field_is_present_in_schema(client):
    """Test that keywords field is present and properly typed in response."""
    page = (
        "Sample Paper\n"
        "Abstract\n"
        "Text here.\n"
        "Keywords: test keyword\n"
        "1. Introduction\n"
        "Body text.\n"
    )
    data = build_pdf("", pages=[page])

    response = client.post(
        "/api/v1/papers/extract",
        files={"file": ("schema_test.pdf", data, "application/pdf")},
    )

    assert response.status_code == 200
    paper = response.json()["paper"]
    assert "keywords" in paper
    assert isinstance(paper["keywords"], list)
    assert all(isinstance(k, str) for k in paper["keywords"])


def test_sample_paper_keywords_are_extracted(client):
    """Test that keywords from the sample paper are correctly extracted."""
    data = build_pdf("", pages=[SAMPLE_PAPER_PAGE_1, SAMPLE_PAPER_PAGE_2])
    response = client.post(
        "/api/v1/papers/extract",
        files={"file": ("sample.pdf", data, "application/pdf")},
    )

    assert response.status_code == 200
    paper = response.json()["paper"]
    # SAMPLE_PAPER_PAGE_1 has: "Keywords: iceberg, radar, deep learning\n"
    assert paper["keywords"] == ["iceberg", "radar", "deep learning"]


def test_keywords_mixed_separators_comma_and_semicolon(client):
    """Test keyword extraction with mixed comma and semicolon separators."""
    page = (
        "Sample Paper\n"
        "Abstract\n"
        "This is abstract text.\n"
        "Keywords: machine learning, neural networks; deep learning; classification\n"
        "1. Introduction\n"
        "Body text.\n"
    )
    data = build_pdf("", pages=[page])

    response = client.post(
        "/api/v1/papers/extract",
        files={"file": ("mixed_sep.pdf", data, "application/pdf")},
    )

    assert response.status_code == 200
    paper = response.json()["paper"]
    # Both commas and semicolons should split the keywords
    assert paper["keywords"] == [
        "machine learning",
        "neural networks",
        "deep learning",
        "classification",
    ]


def test_keywords_with_whitespace_are_cleaned(client):
    """Test that extra whitespace in keywords is properly cleaned."""
    page = (
        "Sample Paper\n"
        "Abstract\n"
        "This is abstract text.\n"
        "Keywords:   machine learning  ,  neural networks  ;  deep learning  \n"
        "1. Introduction\n"
        "Body text.\n"
    )
    data = build_pdf("", pages=[page])

    response = client.post(
        "/api/v1/papers/extract",
        files={"file": ("whitespace.pdf", data, "application/pdf")},
    )

    assert response.status_code == 200
    paper = response.json()["paper"]
    # Each keyword should have whitespace stripped
    assert paper["keywords"] == ["machine learning", "neural networks", "deep learning"]
