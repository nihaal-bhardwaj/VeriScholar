"""Tests for the local consistency rules engine."""

from app.schemas.paper import ReferenceEntry
from app.services.consistency_checker import check_consistency


def _refs(*items: tuple[int, str]) -> list[ReferenceEntry]:
    return [ReferenceEntry(number=number, raw_text=text, doi=None) for number, text in items]


# RULE 2 — figure reference consistency


def test_figure_referenced_but_not_defined_is_flagged():
    text = (
        "Abstract\nWe study radar imagery.\n"
        "1. Introduction\nResults are shown in Figure 1: example output.\n"
        "As explained later, Figure 2 shows the full map.\n"
    )
    report = check_consistency(full_text=text, authors=[], references=[])

    figure_flags = [f for f in report.flags if f.rule == "figure_reference_consistency"]
    assert len(figure_flags) == 1
    assert figure_flags[0].message == "Figure 2 is referenced in text but never defined"
    assert figure_flags[0].severity == "medium"
    assert figure_flags[0].evidence


def test_figure_defined_and_referenced_passes():
    text = (
        "Abstract\nWe study radar imagery.\n"
        "1. Introduction\nFigure 1: Detected icebergs.\n"
        "As shown in Figure 1, the method works.\n"
    )
    report = check_consistency(full_text=text, authors=[], references=[])

    assert [f for f in report.flags if f.rule == "figure_reference_consistency"] == []
    assert any(
        "figure_reference_consistency" in check for check in report.passed_checks
    )


# RULE 5 — reference number continuity


def test_cited_reference_missing_from_reference_list_is_flagged():
    text = "We build on prior work [1, 3, 5] and extend it."
    references = _refs((1, "Ref one"), (2, "Ref two"), (3, "Ref three"), (4, "Ref four"))
    report = check_consistency(full_text=text, authors=[], references=references)

    ref_flags = [f for f in report.flags if f.rule == "reference_number_continuity"]
    assert len(ref_flags) == 1
    assert (
        ref_flags[0].message
        == "Reference [5] cited in text but not found in reference list"
    )
    assert ref_flags[0].evidence


def test_all_cited_references_match_passes():
    text = "Prior work [1] and [2] is relevant here."
    references = _refs((1, "Ref one"), (2, "Ref two"))
    report = check_consistency(full_text=text, authors=[], references=references)

    assert [f for f in report.flags if f.rule == "reference_number_continuity"] == []
    assert any(
        "reference_number_continuity" in check for check in report.passed_checks
    )


# RULE 3 — author name consistency


def test_author_last_name_missing_from_text_is_flagged():
    text = "Abstract\nA study of radar images is presented here.\n"
    report = check_consistency(full_text=text, authors=["Jane P. Doe"], references=[])

    author_flags = [f for f in report.flags if f.rule == "author_name_consistency"]
    assert len(author_flags) == 1
    assert (
        author_flags[0].message
        == "Author 'Jane P. Doe' from author list not found anywhere in paper text"
    )
    assert author_flags[0].evidence == "Jane P. Doe"


# RULE 4 — section structure consistency


def test_missing_conclusion_section_is_a_warning():
    text = (
        "Abstract\nWe study radar imagery.\n"
        "1. Introduction\nBody text.\n"
        "2. Method\nMore body text.\n"
        "References\n[1] A. Author, Journal, 2020.\n"
    )
    references = _refs((1, "A. Author, Journal, 2020."))
    report = check_consistency(full_text=text, authors=[], references=references)

    assert "Expected section 'Conclusion' not found in paper" in report.warnings
    assert report.flags == []


def test_all_standard_sections_present_passes():
    text = (
        "Abstract\nWe study radar imagery.\n"
        "1. Introduction\nBody text.\n"
        "5. Conclusion\nWe conclude.\n"
        "References\n[1] A. Author, Journal, 2020.\n"
    )
    report = check_consistency(full_text=text, authors=[], references=[])

    assert report.warnings == []
    assert any(
        "section_structure_consistency" in check for check in report.passed_checks
    )


# RULE 1 — date consistency


def test_reference_year_after_paper_year_is_flagged():
    text = (
        "Received: 2021\n"
        "Abstract\nWe study radar imagery.\n"
        "References\n[1] A. Author, Journal of Polar Research, 2024.\n"
    )
    references = _refs((1, "A. Author, Journal of Polar Research, 2024."))
    report = check_consistency(full_text=text, authors=[], references=references)

    date_flags = [f for f in report.flags if f.rule == "date_consistency"]
    assert len(date_flags) == 1
    assert (
        date_flags[0].message
        == "Reference [1] cites a paper from 2024 which is after this paper's year 2021"
    )
    assert date_flags[0].severity == "high"


def test_all_reference_years_older_than_paper_pass():
    text = (
        "Received: 2021\n"
        "Abstract\nWe study radar imagery.\n"
        "References\n"
        "[1] A. Author, Journal, 2018.\n"
        "[2] B. Author, Journal, 2019.\n"
    )
    references = _refs((1, "A. Author, Journal, 2018."), (2, "B. Author, Journal, 2019."))
    report = check_consistency(full_text=text, authors=[], references=references)

    assert [f for f in report.flags if f.rule == "date_consistency"] == []
    assert any("date_consistency" in check for check in report.passed_checks)


# Empty input and scoring


def test_empty_input_returns_no_flags_and_perfect_score():
    report = check_consistency(full_text="", authors=[], references=[])

    assert report.flags == []
    assert report.consistency_score == 1.0


def test_consistency_score_is_one_when_no_issues_found():
    text = (
        "Received: 2023\n"
        "Abstract\nWe study radar imaging.\n"
        "1. Introduction\nDoe's method [1] inspired this work.\n"
        "Figure 1: Radar output sample.\n"
        "2. Conclusion\nWe conclude.\n"
        "References\n[1] Jane Doe, Radar Journal, 2020.\n"
    )
    references = _refs((1, "Jane Doe, Radar Journal, 2020."))
    report = check_consistency(
        full_text=text, authors=["Jane Doe"], references=references
    )

    assert report.flags == []
    assert report.warnings == []
    assert report.consistency_score == 1.0


def test_consistency_score_is_below_one_when_issues_found():
    text = (
        "Received: 2023\n"
        "Abstract\nWe study radar imaging.\n"
        "1. Introduction\nResults are shown in Figure 3.\n"
        "2. Conclusion\nWe conclude.\n"
        "References\n[1] A. Author, Journal, 2020.\n"
    )
    report = check_consistency(full_text=text, authors=[], references=[])

    assert [f for f in report.flags if f.rule == "figure_reference_consistency"]
    assert report.consistency_score < 1.0


# Endpoint wiring


def test_integrity_check_endpoint_is_live(client):
    payload = {
        "analysis_id": "00000000-0000-0000-0000-000000000000",
        "full_text": "Abstract\nWe study radar.\n1. Introduction\nSee Figure 2.\n",
        "authors": [],
        "references": [],
        "pages": [{"page_number": 1, "text": "Abstract\nWe study radar.\n"}],
    }
    response = client.post("/api/v1/integrity/check", json=payload)

    assert response.status_code == 200
    body = response.json()
    assert "flags" in body and "warnings" in body
    assert "passed_checks" in body and "consistency_score" in body
    assert any(flag["rule"] == "figure_reference_consistency" for flag in body["flags"])