"""Tests for the PDF parser service."""

import pytest

from app.services.pdf_parser import (
    AUTHOR_YEAR_FALLBACK_WARNING,
    LOW_CONFIDENCE_AUTHOR_YEAR_WARNING,
    NUMBERING_GAP_WARNING,
    PDFCorruptError,
    PDFParseError,
    PDFPasswordProtectedError,
    UNRELIABLE_WARNING,
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
        text = (
            "[1] A. Author, Title, 2024. https://doi.org/10.5678/iceberg.v2\n"
            "[2] B. Author, Title, 2025."
        )
        entries, warnings = split_references(text)
        assert warnings == []
        assert entries[0]["doi"] == "10.5678/iceberg.v2"

    def test_unreliable_style_returns_warning_not_fabrication(self):
        text = "Some free-form bibliography without numbering."
        entries, warnings = split_references(text)
        assert entries == []
        assert warnings, "expected a warning for unreliable splitting"

    def test_hanging_numeral_markers_are_split(self):
        text = (
            "1.\nFirst author, Title, Journal of Polar Research, 2024.\n"
            "2.\nSecond author, Title, Journal of Polar Research, 2025."
        )
        entries, warnings = split_references(text)
        assert warnings == []
        assert [entry["number"] for entry in entries] == [1, 2]
        assert entries[0]["raw_text"].startswith("First author")

    def test_bare_number_markers_are_split(self):
        text = (
            "1\nFirst author, Title, Journal of Polar Research, 2024.\n"
            "2\nSecond author, Title, Journal of Polar Research, 2025."
        )
        entries, warnings = split_references(text)
        assert warnings == []
        assert [entry["number"] for entry in entries] == [1, 2]

    def test_paren_numeral_style_is_split(self):
        text = "1) First reference text here.\n2) Second reference text here."
        entries, warnings = split_references(text)
        assert warnings == []
        assert [entry["number"] for entry in entries] == [1, 2]

    def test_numbering_gap_adds_warning(self):
        text = "[1] Alpha entry one here.\n[2] Beta entry two here.\n[4] Delta entry four here."
        entries, warnings = split_references(text)
        assert [entry["number"] for entry in entries] == [1, 2, 4]
        assert NUMBERING_GAP_WARNING in warnings

    def test_numbered_multiline_bodies_are_merged(self):
        text = (
            "1.\nBody line one of the first entry.\nBody line two of the first entry.\n"
            "2.\nBody line one of the second entry.\nBody line two of the second entry."
        )
        entries, warnings = split_references(text)
        assert warnings == []
        assert [entry["number"] for entry in entries] == [1, 2]
        assert entries[0]["raw_text"] == (
            "Body line one of the first entry. Body line two of the first entry."
        )
        assert entries[1]["raw_text"] == (
            "Body line one of the second entry. Body line two of the second entry."
        )

    def test_marker_only_fragment_is_dropped(self):
        text = "[1] Alpha entry one here.\n[2]\n[3] Gamma entry three here."
        entries, warnings = split_references(text)
        assert [entry["number"] for entry in entries] == [1, 3]
        assert NUMBERING_GAP_WARNING in warnings

    def test_single_numbered_entry_is_not_reliable(self):
        entries, warnings = split_references("1. Only one reference text here.")
        assert entries == []
        assert UNRELIABLE_WARNING in warnings

    def test_single_bracket_entry_is_not_reliable(self):
        entries, warnings = split_references("[1] A. Author, Title, 2024. Journal.")
        assert entries == []
        assert UNRELIABLE_WARNING in warnings

    def test_empty_references_text_returns_nothing(self):
        assert split_references("") == ([], [])
        assert split_references("   \n\n  ") == ([], [])

    def test_blank_lines_between_entries_are_ignored(self):
        text = "[1] First reference text here.\n\n[2] Second reference text here.\n\n"
        entries, warnings = split_references(text)
        assert warnings == []
        assert [entry["number"] for entry in entries] == [1, 2]

    def test_author_year_bracket_style_is_split(self):
        text = (
            "Smith, J. (2018). Title of the paper here. Journal One, 12(3), 45-67.\n"
            "Jones, A. B. (2019). Another title here. Journal Two, 9(1), 10-20."
        )
        entries, warnings = split_references(text)
        assert warnings == [AUTHOR_YEAR_FALLBACK_WARNING]
        assert [entry["number"] for entry in entries] == [1, 2]
        assert entries[0]["raw_text"].startswith("Smith, J.")

    def test_author_year_period_style_is_split(self):
        text = (
            "Smith, J. 2018. Title of the paper here. Journal One, 12(3), 45-67.\n"
            "Jones, A. 2019. Another title here. Journal Two, 9(1), 10-20."
        )
        entries, warnings = split_references(text)
        assert warnings == [AUTHOR_YEAR_FALLBACK_WARNING]
        assert [entry["number"] for entry in entries] == [1, 2]

    def test_author_year_paren_year_without_period_is_split(self):
        text = (
            "Smith, J. and Jones, A. (2018) Title of the paper here. Journal One.\n"
            "Doe, J. (2019) Another title here. Journal Two."
        )
        entries, warnings = split_references(text)
        assert warnings == [AUTHOR_YEAR_FALLBACK_WARNING]
        assert [entry["number"] for entry in entries] == [1, 2]

    def test_author_year_doi_is_extracted(self):
        text = (
            "Smith, J. (2018). Title of the paper here. Journal One, 12(3), 45-67.\n"
            "https://doi.org/10.5678/iceberg.v2\n"
            "Jones, A. (2019). Another title here. Journal Two, 9(1), 10-20."
        )
        entries, warnings = split_references(text)
        assert warnings == [AUTHOR_YEAR_FALLBACK_WARNING]
        assert entries[0]["doi"] == "10.5678/iceberg.v2"
        assert entries[0]["raw_text"].endswith("https://doi.org/10.5678/iceberg.v2")

    def test_author_year_wrapped_year_continuation_is_joined(self):
        text = (
            "Dowle, M., Short, T., Lianoglou, S. and Srinivasan, A.\n"
            "(2018). data.table: Extension of data.frame. R Journal, 6(1), 1-10.\n"
            "R Core Team (2020). R: A language and environment for statistical computing. Vienna, Austria."
        )
        entries, warnings = split_references(text)
        assert warnings == [AUTHOR_YEAR_FALLBACK_WARNING]
        assert [entry["number"] for entry in entries] == [1, 2]
        assert entries[0]["raw_text"].startswith("Dowle, M.")
        assert "(2018)." in entries[0]["raw_text"]

    def test_author_year_corporate_unicode_and_suffix_years(self):
        text = (
            "World Health Organization. (2019). Global health report 2019. Geneva: WHO.\n"
            "Martín-Martín, A., Orduna-Malea, E. (2018). Google Scholar as a data source. Scientometrics, 102(1), 45-67.\n"
            "Smith, J. (2018a). First study here. Journal One, 1(1), 1-10."
        )
        entries, warnings = split_references(text)
        assert warnings == [AUTHOR_YEAR_FALLBACK_WARNING]
        assert [entry["number"] for entry in entries] == [1, 2, 3]
        assert entries[1]["raw_text"].startswith("Martín-Martín")

    def test_bare_year_lines_are_not_markers(self):
        entries, warnings = split_references("2018\n2019")
        assert entries == []
        assert UNRELIABLE_WARNING in warnings

    def test_bare_year_inside_author_year_entry_stays_content(self):
        text = (
            "Smith, J. (2018). Title of the paper here. Journal One.\n"
            "2019\n"
            "Jones, A. (2019). Another title here. Journal Two."
        )
        entries, warnings = split_references(text)
        assert warnings == [AUTHOR_YEAR_FALLBACK_WARNING]
        assert len(entries) == 2
        assert "2019" in entries[0]["raw_text"]

    def test_false_positive_prose_is_not_split(self):
        text = "In this paper we cite Smith (2018) and Jones (2019) extensively."
        entries, warnings = split_references(text)
        assert entries == []
        assert UNRELIABLE_WARNING in warnings

    def test_header_footer_lines_are_not_boundaries(self):
        text = (
            "Smith, J. (2018). Title one here. Journal One.\n"
            "Vol. 9, No. 5; 2013\n"
            "Jones, A. (2019). Title two here. Journal Two."
        )
        entries, warnings = split_references(text)
        assert warnings == [AUTHOR_YEAR_FALLBACK_WARNING]
        assert len(entries) == 2
        assert "Vol. 9, No. 5; 2013" in entries[0]["raw_text"]

    def test_author_year_tiny_fragments_are_rejected(self):
        text = "A(2018)X\nB(2019)Y"
        entries, warnings = split_references(text)
        assert entries == []
        assert UNRELIABLE_WARNING in warnings

    def test_author_year_low_confidence_warning(self):
        text = (
            "Smith, J. (2018). Title one here. Journal One.\n"
            "Doe(2019)\n"
            "Jones, A. (2019). Title two here. Journal Two."
        )
        entries, warnings = split_references(text)
        assert len(entries) == 3
        assert entries[1]["raw_text"] == "Doe(2019)"
        assert AUTHOR_YEAR_FALLBACK_WARNING in warnings
        assert LOW_CONFIDENCE_AUTHOR_YEAR_WARNING in warnings

    def test_single_author_sentence_is_not_reliable(self):
        text = "Smith (2018) found that the method improved accuracy by a large margin."
        entries, warnings = split_references(text)
        assert entries == []
        assert UNRELIABLE_WARNING in warnings


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

    def test_parses_author_year_references_full_pdf(self):
        page_1 = (
            "Author-Year Sample Paper\n"
            "Abstract\n"
            "A short abstract about citation formats.\n"
            "Keywords: citation, references\n"
            "1. Introduction\n"
            "Content here.\n"
        )
        page_2 = (
            "2. Discussion\n"
            "More content here.\n"
            "References\n"
            "Smith, J. (2018). Title of the paper here. Journal One, 12(3), 45-67.\n"
            "Jones, A. (2019). Another title here. Journal Two, 9(1), 10-20."
        )
        data = build_pdf("", pages=[page_1, page_2])
        parsed = parse_pdf_bytes(data, "author-year.pdf")

        assert parsed.references_text and parsed.references_text.startswith("Smith, J.")
        assert len(parsed.references) == 2
        assert [entry["number"] for entry in parsed.references] == [1, 2]
        assert all(
            "References" not in entry["raw_text"] for entry in parsed.references
        )
        assert any("author-year" in warning.lower() for warning in parsed.warnings)

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
