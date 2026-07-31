"""Tests for the PDF parser service."""

import pytest

from app.services.pdf_parser import (
    PDFCorruptError,
    PDFParseError,
    PDFPasswordProtectedError,
    extract_doi_candidates,
    parse_pdf_bytes,
    split_references,
)
from tests.conftest import SAMPLE_PAPER_PAGE_1, SAMPLE_PAPER_PAGE_2, build_pdf


class TestDOIExtraction:
    def test_extracts_doi_from_sample_text(self):
        text = "See https://doi.org/10.1234/example.2026 for details."
        assert extract_doi_candidates(text) == ["10.1234/example.2026"]

    def test_trailing_punctuation_is_removed(self):
        text = "DOI: 10.1000/abc-123."
        assert extract_doi_candidates(text) == ["10.1000/abc-123"]

    def test_deduplicates_case_insensitively(self):
        text = "10.1234/Example.1 and 10.1234/example.1"
        assert extract_doi_candidates(text) == ["10.1234/Example.1"]

    def test_no_doi_returns_empty(self):
        assert extract_doi_candidates("no identifiers here") == []


class TestReferenceSplitting:
    def test_bracketed_references_are_separated(self):
        text = "[1] First author, Title, Journal 2024.\n[2] Second author, Title, Journal 2025."
        entries, warnings = split_references(text)
        assert warnings == []
        assert [entry["number"] for entry in entries] == [1, 2]
        assert entries[1]["raw_text"].startswith("Second author")

    def test_numeral_references_are_separated(self):
        text = "1. First reference text\n2. Second reference text"
        entries, warnings = split_references(text)
        assert warnings == []
        assert [entry["number"] for entry in entries] == [1, 2]

    def test_doi_extracted_from_reference_entry(self):
        text = "[1] A. Author, Title, 2024. https://doi.org/10.5678/iceberg.v2"
        entries, warnings = split_references(text)
        assert warnings == []
        assert entries[0]["doi"] == "10.5678/iceberg.v2"

    def test_unreliable_style_returns_warning_not_fabrication(self):
        text = "Some free-form bibliography without numbering."
        entries, warnings = split_references(text)
        assert entries == []
        assert warnings, "expected a warning for unreliable splitting"


class TestFullParsing:
    def test_parses_sample_paper(self):
        data = build_pdf("", pages=[SAMPLE_PAPER_PAGE_1, SAMPLE_PAPER_PAGE_2])
        parsed = parse_pdf_bytes(data, "sample.pdf")

        assert parsed.page_count == 2
        assert parsed.best_doi == "10.1234/example.2026"
        assert parsed.doi_candidates[0] == "10.1234/example.2026"
        assert "10.5678/iceberg.v2" in parsed.doi_candidates
        assert parsed.abstract and "iceberg" in parsed.abstract.lower()
        assert "94% accuracy" in parsed.abstract
        assert parsed.references_text and parsed.references_text.startswith("[1]")
        assert len(parsed.references) == 2
        assert parsed.references[1]["doi"] == "10.5678/iceberg.v2"
        assert len(parsed.pages) == 2
        assert parsed.pages[0]["page_number"] == 1

    def test_missing_abstract_and_references_does_not_crash(self):
        data = build_pdf("Just some plain text without sections.")
        parsed = parse_pdf_bytes(data, "plain.pdf")

        assert parsed.abstract is None
        assert parsed.references_text is None
        assert parsed.references == []
        assert any("abstract" in warning.lower() for warning in parsed.warnings)
        assert any("references" in warning.lower() for warning in parsed.warnings)

    def test_password_protected_pdf_raises(self):
        import fitz

        protected = fitz.open()
        page = protected.new_page()
        page.insert_text((72, 72), "secret content")
        data = protected.tobytes(encryption=fitz.PDF_ENCRYPT_AES_256, user_pw="secret", owner_pw="owner")
        protected.close()

        with pytest.raises(PDFPasswordProtectedError):
            parse_pdf_bytes(data, "locked.pdf")

    def test_corrupt_pdf_raises(self):
        with pytest.raises(PDFCorruptError):
            parse_pdf_bytes(b"%PDF-1.7 this is not a real pdf", "broken.pdf")

    def test_empty_text_pdf_raises(self):
        import io

        import fitz

        buffer = io.BytesIO()
        document = fitz.open()
        document.new_page()
        document.save(buffer)
        document.close()
        with pytest.raises(PDFParseError):
            parse_pdf_bytes(buffer.getvalue(), "blank.pdf")
