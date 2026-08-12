"""Tests for the PDF parser service."""

import pytest

from app.services.pdf_parser import (
    AUTHOR_UNCERTAIN_WARNING,
    AUTHOR_YEAR_FALLBACK_WARNING,
    LOW_CONFIDENCE_AUTHOR_YEAR_WARNING,
    NUMBERING_GAP_WARNING,
    PDFCorruptError,
    PDFParseError,
    PDFPasswordProtectedError,
    TITLE_UNCERTAIN_WARNING,
    UNRELIABLE_WARNING,
    _detect_title,
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


class TestTitleDetection:
    def test_clean_title_is_extracted(self):
        page = (
            "Deep Learning for Iceberg Detection\n"
            "Abstract\n"
            "We study convolutional models for iceberg detection.\n"
        )
        parsed = parse_pdf_bytes(build_pdf(page), "title.pdf")

        assert parsed.title == "Deep Learning for Iceberg Detection"
        assert not any("title" in warning.lower() for warning in parsed.warnings)

    def test_metadata_before_title_is_skipped(self):
        page = (
            "Research Article\n"
            "Vol. 9, No. 5\n"
            "REAL PAPER TITLE\n"
            "Abstract\n"
            "Body text here.\n"
        )
        parsed = parse_pdf_bytes(build_pdf(page), "metadata-before-title.pdf")

        assert parsed.title == "REAL PAPER TITLE"

    def test_wrapped_title_continuation_is_joined(self):
        page = (
            "A Study of Research\n"
            "integrity in modern science\n"
            "Abstract\n"
            "Body text here.\n"
        )
        parsed = parse_pdf_bytes(build_pdf(page), "wrapped-title.pdf")

        assert parsed.title == "A Study of Research integrity in modern science"

    def test_metadata_only_front_matter_returns_none_with_warning(self):
        page = (
            "Received: 12 March 2020\n"
            "Accepted: 5 March 2020\n"
            "Abstract\n"
            "Body text here.\n"
        )
        parsed = parse_pdf_bytes(build_pdf(page), "metadata-only.pdf")

        assert parsed.title is None
        assert TITLE_UNCERTAIN_WARNING in parsed.warnings

    def test_doi_url_and_email_lines_are_never_titles(self):
        page = (
            "https://doi.org/10.1234/example.2026\n"
            "jane.doe@example.com\n"
            "DOI: 10.5678/other\n"
            "Iceberg Detection Survey\n"
            "Abstract\n"
            "Body text here.\n"
        )
        parsed = parse_pdf_bytes(build_pdf(page), "identifiers.pdf")

        assert parsed.title == "Iceberg Detection Survey"

    def test_unicode_title_text_is_preserved(self):
        title, warnings = _detect_title(
            ["Détection Automatique des Icebergs par Imagerie Radar"]
        )

        assert title == "Détection Automatique des Icebergs par Imagerie Radar"
        assert warnings == []

    def test_prose_sentence_before_abstract_is_not_a_title(self):
        page = (
            "In recent years, deep learning has transformed many areas of research.\n"
            "Abstract\n"
            "Body text here.\n"
        )
        parsed = parse_pdf_bytes(build_pdf(page), "prose.pdf")

        assert parsed.title is None
        assert TITLE_UNCERTAIN_WARNING in parsed.warnings

    def test_no_abstract_heading_never_guesses_a_title(self):
        parsed = parse_pdf_bytes(
            build_pdf("Just some plain text without sections."), "plain.pdf"
        )

        assert parsed.title is None
        assert not any("title" in warning.lower() for warning in parsed.warnings)

    def test_empty_front_matter_returns_none_without_warning(self):
        parsed = parse_pdf_bytes(build_pdf("Abstract\nBody text here.\n"), "empty-front.pdf")

        assert parsed.title is None
        assert not any("title" in warning.lower() for warning in parsed.warnings)


class TestAuthorExtraction:
    def test_single_clean_author(self):
        page = (
            "Iceberg Radar Survey\n"
            "John Doe\n"
            "Abstract\n"
            "Body text here.\n"
        )
        parsed = parse_pdf_bytes(build_pdf(page), "single-author.pdf")

        assert parsed.authors == ["John Doe"]
        assert not any("author" in warning.lower() for warning in parsed.warnings)

    def test_comma_separated_authors(self):
        page = (
            "Iceberg Radar Survey\n"
            "John Doe, Jane Smith\n"
            "Abstract\n"
            "Body text here.\n"
        )
        parsed = parse_pdf_bytes(build_pdf(page), "comma-authors.pdf")

        assert parsed.authors == ["John Doe", "Jane Smith"]

    def test_and_separated_authors(self):
        page = (
            "Iceberg Radar Survey\n"
            "John Doe and Jane Smith\n"
            "Abstract\n"
            "Body text here.\n"
        )
        parsed = parse_pdf_bytes(build_pdf(page), "and-authors.pdf")

        assert parsed.authors == ["John Doe", "Jane Smith"]

    def test_ampersand_separated_authors(self):
        page = (
            "Iceberg Radar Survey\n"
            "John Doe & Jane Smith\n"
            "Abstract\n"
            "Body text here.\n"
        )
        parsed = parse_pdf_bytes(build_pdf(page), "ampersand-authors.pdf")

        assert parsed.authors == ["John Doe", "Jane Smith"]

    def test_authors_across_multiple_lines(self):
        page = (
            "Iceberg Radar Survey\n"
            "John Doe\n"
            "Jane Smith\n"
            "Abstract\n"
            "Body text here.\n"
        )
        parsed = parse_pdf_bytes(build_pdf(page), "multi-line-authors.pdf")

        assert parsed.authors == ["John Doe", "Jane Smith"]

    def test_surname_initials_form(self):
        page = (
            "Iceberg Radar Survey\n"
            "Doe, J. R.\n"
            "Abstract\n"
            "Body text here.\n"
        )
        parsed = parse_pdf_bytes(build_pdf(page), "initials-author.pdf")

        assert parsed.authors == ["Doe, J. R."]

    def test_affiliations_and_identifiers_ignored(self):
        page = (
            "Iceberg Radar Survey\n"
            "John Doe\n"
            "jane.doe@example.com\n"
            "https://orcid.org/0000-0001-2345-6789\n"
            "10.1234/example\n"
            "1 Department of Neurology, University of Berlin\n"
            "2 Center for Artificial Intelligence, MIT\n"
            "Received: 12 March 2020\n"
            "Abstract\n"
            "Body text here.\n"
        )
        parsed = parse_pdf_bytes(build_pdf(page), "affiliations.pdf")

        assert parsed.authors == ["John Doe"]
        assert not any("author" in warning.lower() for warning in parsed.warnings)

    def test_superscript_markers_stripped(self):
        page = (
            "Iceberg Radar Survey\n"
            "John Doe1,2 and Jane Smith1\n"
            "Abstract\n"
            "Body text here.\n"
        )
        parsed = parse_pdf_bytes(build_pdf(page), "superscripts.pdf")

        assert parsed.authors == ["John Doe", "Jane Smith"]

    def test_superscript_marker_on_initials_form(self):
        page = (
            "Iceberg Radar Survey\n"
            "Doe, J. R.1\n"
            "Abstract\n"
            "Body text here.\n"
        )
        parsed = parse_pdf_bytes(build_pdf(page), "initials-superscript.pdf")

        assert parsed.authors == ["Doe, J. R."]

    def test_ambiguous_author_region_returns_empty_with_warning(self):
        page = (
            "Iceberg Radar Survey\n"
            "Funding: National Science Foundation\n"
            "Vol. 9, No. 5; 2026\n"
            "Abstract\n"
            "Body text here.\n"
        )
        parsed = parse_pdf_bytes(build_pdf(page), "ambiguous-authors.pdf")

        assert parsed.authors == []
        assert AUTHOR_UNCERTAIN_WARNING in parsed.warnings

    def test_no_author_region_returns_empty_without_warning(self):
        parsed = parse_pdf_bytes(build_pdf("Abstract\nBody text here.\n"), "no-authors.pdf")

        assert parsed.authors == []
        assert AUTHOR_UNCERTAIN_WARNING not in parsed.warnings

    def test_title_only_front_matter_has_no_author_region(self):
        page = (
            "Iceberg Radar Survey\n"
            "Abstract\n"
            "Body text here.\n"
        )
        parsed = parse_pdf_bytes(build_pdf(page), "title-only.pdf")

        assert parsed.authors == []
        assert AUTHOR_UNCERTAIN_WARNING not in parsed.warnings

    def test_order_is_preserved_and_duplicates_removed_case_insensitively(self):
        page = (
            "Iceberg Radar Survey\n"
            "John Doe\n"
            "Jane Smith\n"
            "John van Doorn\n"
            "John Van Doorn\n"
            "Abstract\n"
            "Body text here.\n"
        )
        parsed = parse_pdf_bytes(build_pdf(page), "order-dedupe.pdf")

        assert parsed.authors == ["John Doe", "Jane Smith", "John van Doorn"]


class TestAbstractBoundaryCleanup:
    STOP_LABELS = [
        ("Keywords", "iceberg, radar, remote sensing"),
        ("Index Terms", "neural networks, deep learning"),
        ("Funding", "National Science Foundation"),
        ("Citation", "Doe J, Smith J. 2026"),
        ("Received", "12 March 2020"),
        ("Accepted", "5 April 2020"),
    ]

    def _parse_with_header(self, header: str) -> object:
        page = (
            "Abstract\n"
            "We study radar imagery for iceberg detection.\n"
            f"{header}\n"
            "1. Introduction\n"
            "Body text here.\n"
        )
        return parse_pdf_bytes(build_pdf(page), "abstract-boundary.pdf")

    @pytest.mark.parametrize("label,value", STOP_LABELS)
    def test_colon_label_stops_abstract(self, label, value):
        parsed = self._parse_with_header(f"{label}: {value}")

        assert parsed.abstract == "We study radar imagery for iceberg detection."

    @pytest.mark.parametrize("label", [case[0] for case in STOP_LABELS])
    def test_bare_heading_stops_abstract(self, label):
        parsed = self._parse_with_header(label)

        assert parsed.abstract == "We study radar imagery for iceberg detection."

    def test_whitespace_tolerant_colon_stops_abstract(self):
        parsed = self._parse_with_header("Funding  :  National Science Foundation")

        assert parsed.abstract == "We study radar imagery for iceberg detection."

    def test_case_insensitive_label_stops_abstract(self):
        parsed = self._parse_with_header("keywords: iceberg, radar, remote sensing")

        assert parsed.abstract == "We study radar imagery for iceberg detection."

    def test_received_wisdom_prose_does_not_stop_abstract(self):
        page = (
            "Abstract\n"
            "Received wisdom suggests that icebergs drift slowly.\n"
            "1. Introduction\n"
            "Body text here.\n"
        )
        parsed = parse_pdf_bytes(build_pdf(page), "received-wisdom.pdf")

        assert parsed.abstract == "Received wisdom suggests that icebergs drift slowly."
