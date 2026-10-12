"""Regression and edge-case tests for IEEE paper extraction and integrity screening.

Verifies:
1. Multi-line title reconstruction (ignoring journal banners)
2. Author extraction with IEEE membership stripping and casing normalization
3. Abstract detection with em-dashes and spaced letters
4. Generic reference sequence discovery ([1]..[112])
5. Missing-data handling: uncertain abstract does NOT trigger mismatch anomaly
6. Opposite case: real mismatched abstract triggers HIGH severity anomaly
7. Demo override disabled by default
8. Extraction failure does NOT generate critical fraud risk
9. Synthetic test cases A through J
"""

import pytest

from app.core.config import get_settings
from app.schemas.paper import ReferenceEntry
from app.schemas.report import ReportInput
from app.services.consistency_checker import check_consistency
from app.services.ml.anomaly_scorer import analyze_text
from app.services.ml.feature_extractor import extract_features
from app.services.ml.ml_pipeline import run_ml_analysis
from app.services.pdf_parser import (
    _detect_abstract_detailed,
    _detect_authors,
    _detect_title,
    compute_extraction_quality,
    normalize_pdf_text,
    split_references,
    validate_reference_numbering,
)
from app.services.report_generator import generate_report


class TestIEEEPaperExtraction:
    def test_multi_line_title_reconstruction_ignores_journal_banner(self):
        front_matter = [
            "PROCEEDINGS OF THE IEEE, VOL. 82, NO. 1, JANUARY 1994",
            "Real-Time Computing: A New Discipline",
            "of Computer Science and Engineering",
            "KANG G. SHIN, FELLOW, IEEE, AND PARAMESWARAN RAMANATHAN, MEMBER, IEEE",
        ]
        title, warnings = _detect_title(front_matter)
        assert title == "Real-Time Computing: A New Discipline of Computer Science and Engineering"
        assert warnings == []

    def test_all_caps_multi_line_title_reconstruction(self):
        front_matter = [
            "PROCEEDINGS OF THE IEEE, VOL. 82, NO. 1, JANUARY 1994",
            "REAL-TIME COMPUTING: A NEW DISCIPLINE",
            "OF COMPUTER SCIENCE AND ENGINEERING",
            "KANG G. SHIN, FELLOW, IEEE",
        ]
        title, warnings = _detect_title(front_matter)
        assert title == "REAL-TIME COMPUTING: A NEW DISCIPLINE OF COMPUTER SCIENCE AND ENGINEERING"

    def test_author_extraction_strips_ieee_membership_and_normalizes_case(self):
        front_matter = [
            "Real-Time Computing: A New Discipline of Computer Science and Engineering",
            "KANG G. SHIN, FELLOW, IEEE, AND",
            "PARAMESWARAN RAMANATHAN, MEMBER, IEEE",
            "Abstract—Real-time computing is...",
        ]
        authors, warnings = _detect_authors(front_matter)
        assert "Kang G. Shin" in authors
        assert "Parameswaran Ramanathan" in authors
        # Verify IEEE membership tokens are completely stripped
        for author in authors:
            assert "FELLOW" not in author.upper()
            assert "MEMBER" not in author.upper()
            assert "IEEE" not in author.upper()

    def test_abstract_em_dash_detection(self):
        lines = [
            "Real-Time Computing: A New Discipline of Computer Science and Engineering",
            "Kang G. Shin and Parameswaran Ramanathan",
            "Abstract—Real-time computing is a rapidly growing discipline in computer science",
            "and engineering where timing constraints must be satisfied for correctness.",
            "Index Terms—Real-time systems, fault tolerance, deadline scheduling.",
            "1. Introduction",
            "Real-time computing systems play an increasingly important role...",
        ]
        abstract, status, conf = _detect_abstract_detailed(lines)
        assert status == "found"
        assert conf >= 0.90
        assert abstract is not None
        assert abstract.startswith("Real-time computing is a rapidly growing")
        assert "Index Terms" not in abstract
        assert "1. Introduction" not in abstract

    def test_spaced_abstract_heading_detection(self):
        lines = [
            "A  B  S  T  R  A  C  T",
            "This paper studies scheduling algorithms for critical real-time tasks.",
            "1. Introduction",
        ]
        abstract, status, conf = _detect_abstract_detailed(lines)
        assert status == "found"
        assert "scheduling algorithms" in abstract

    def test_generic_reference_splitting_1_to_112(self):
        ref_lines = []
        for i in range(1, 113):
            ref_lines.append(f"[{i}] Author {i}, Title of paper {i}, IEEE Trans. Comput., vol. {i}, 199{i%10}.")
        text = "\n".join(ref_lines)

        entries, warnings = split_references(text)
        assert len(entries) == 112
        assert warnings == []
        assert entries[0]["number"] == 1
        assert entries[111]["number"] == 112

        validation = validate_reference_numbering(entries)
        assert validation["reference_count"] == 112
        assert validation["expected_count"] == 112
        assert validation["missing_numbers"] == []
        assert validation["status"] == "good"


class TestMissingDataAndFalsePositiveRemediation:
    def test_uncertain_abstract_does_not_trigger_mismatch_anomaly(self):
        """Regression test for the bug where missing abstract triggered HIGH severity anomaly."""
        body_text = (
            "Real-time computing systems play an increasingly important role in our society. "
            "Examples of such systems include aircraft flight control, nuclear power plants, "
            "and manufacturing process control. In these systems, correctness depends not only "
            "on the logical result of computation but also on the time at which the results are produced. "
            "Tasks have deadlines that must be met to ensure predictable behavior. "
        ) * 15

        # Abstract could not be extracted (uncertain)
        features = extract_features(full_text=body_text, abstract="", pages=[{"page_number": 1, "text": body_text}])
        assert features.abstract_to_body_similarity is None

        result = analyze_text(features)
        # Verify abstract_body_mismatch was marked as not_evaluable, NOT triggered!
        assert "abstract_body_mismatch" in result.not_evaluable_rules
        assert "abstract_body_mismatch" not in [s.rule for s in result.signals]

        # Verify no HIGH severity mismatch signal exists
        high_signals = [s for s in result.signals if s.severity == "high"]
        assert not any(s.rule == "abstract_body_mismatch" for s in high_signals)

    def test_opposite_case_real_mismatched_abstract_triggers_high_risk(self):
        """Verify real fraud (completely mismatched abstract) is still detected sharply."""
        abstract_text = (
            "This paper proposes a decentralized blockchain-based cryptocurrency "
            "smart contract auditing framework using zero-knowledge proofs."
        )
        body_text = (
            "We analyze real-time scheduling algorithms for hard-deadline task sets in multiprocessor systems. "
            "Worst case response times are computed using utilization bounds and rate monotonic analysis. "
            "Periodic tasks are assigned static priorities according to their deadlines. "
        ) * 20

        features = extract_features(full_text=body_text, abstract=abstract_text, pages=[{"page_number": 1, "text": body_text}])
        assert features.abstract_to_body_similarity is not None
        assert features.abstract_to_body_similarity < 0.15

        result = analyze_text(features)
        mismatch_signals = [s for s in result.signals if s.rule == "abstract_body_mismatch"]
        assert len(mismatch_signals) == 1
        assert mismatch_signals[0].severity == "high"
        assert mismatch_signals[0].points == 15.0

    def test_demo_override_is_disabled_by_default(self):
        """Verify demo override does not activate silently in normal runs."""
        settings = get_settings()
        assert settings.demo_mode is False

        sample_text = "This is a legitimate academic paper on real-time systems. " * 30
        result = run_ml_analysis(sample_text, "", [{"page_number": 1, "text": sample_text}])
        # Risk contribution must not be 85 or 100 solely from demo override
        assert not any(s.rule == "ml_baseline_classifier" and s.evidence == "Suspicion Probability: 0.99" for s in result.signals)

    def test_extraction_failure_does_not_produce_critical_risk(self):
        """Document with extraction limitations should produce provisional/limited assessment, not CRITICAL 100."""
        text = "Short fragment of academic text without detectable metadata. " * 15
        quality = compute_extraction_quality(
            title=None,
            authors=[],
            abstract=None,
            abstract_status="uncertain",
            references=[],
            ref_validation=None,
        )
        assert quality["status"] in ("degraded", "poor")

        report_input = ReportInput(
            analysis_id="test-fail-safe",
            paper_title="",
            paper_authors=[],
            abstract="",
            extraction_quality=quality,
        )
        report = generate_report(report_input)

        # Risk level must NOT be critical solely from missing metadata
        assert report.risk_level != "critical"
        assert report.confidence <= 0.40
        assert report.assessment_status in ("limited_evidence", "undetermined")

    def test_degraded_reference_list_does_not_flood_continuity_score(self):
        """When 30 references are missing due to parser truncation, report a consolidated flag, not 30 medium flags."""
        text = "In [1], [2], [5], [75], [90], [112] we cite various works."
        # Only [1] and [2] defined
        references = [
            ReferenceEntry(number=1, raw_text="Ref 1"),
            ReferenceEntry(number=2, raw_text="Ref 2"),
        ]
        # Cited: 1, 2, 5, 75, 90, 112 -> 4 missing (<=5) -> individual flags
        report = check_consistency(full_text=text, references=references)
        assert len(report.flags) == 4

        # Now simulate a citation block with 20 citations missing
        dense_citations = " ".join(f"[{i}]" for i in range(1, 40))
        report_large = check_consistency(full_text=dense_citations, references=references)
        # Should be consolidated into 1 flag because missing count > 5
        continuity_flags = [f for f in report_large.flags if f.rule == "reference_number_continuity"]
        assert len(continuity_flags) == 1
        assert "incomplete" in continuity_flags[0].message


class TestSyntheticEdgeCases:
    def test_case_a_perfect_modern_paper(self):
        title = "Neural Networks for Real-Time Inference"
        authors = ["Alice Smith", "Bob Jones"]
        abstract = (
            "This paper presents a modern convolutional architecture for real-time inference in embedded systems. "
            "We evaluate throughput, latency, and operational efficiency across multiple benchmark workloads."
        )
        p1 = (
            "Neural networks have been widely adopted across diverse computing domains. "
            "In this study, a new convolutional architecture was designed and evaluated on benchmark sets. "
            "The experimental results suggest that execution time may be reduced by approximately thirty percent. "
            "Prior literature [1] examined similar structural trade-offs under varying computational workloads."
        )
        p2 = (
            "As demonstrated in [2], pipeline parallelism provides substantial throughput improvements. "
            "Consequently, it appears that deep models can satisfy strict operational deadlines when properly scheduled. "
            "Further experiments were conducted to evaluate memory footprint and latency trade-offs across embedded hardware platforms."
        )
        p3 = (
            "The proposed methods were verified against standard baseline implementations. "
            "It was observed that throughput scaled favorably as processor frequencies increased. "
            "We conclude that such optimizations could significantly benefit mission-critical autonomous systems."
        )
        body = f"{title}\n{authors[0]} and {authors[1]}\n\n" + "\n\n".join([p1, p2, p3] * 10)

        refs = [
            ReferenceEntry(number=1, raw_text="A. Author, Neural Networks, 2023.", doi="10.1000/1"),
            ReferenceEntry(number=2, raw_text="B. Author, Fast Inference, 2024.", doi="10.1000/2"),
        ]

        quality = compute_extraction_quality(
            title=title,
            authors=authors,
            abstract=abstract,
            abstract_status="found",
            references=[{"number": 1, "raw_text": "Ref 1"}, {"number": 2, "raw_text": "Ref 2"}],
            ref_validation={"status": "good"},
        )
        ml = run_ml_analysis(body, abstract, [{"page_number": 1, "text": body}], quality)

        report = generate_report(
            ReportInput(
                analysis_id="case-a",
                paper_title=title,
                paper_authors=authors,
                abstract=abstract,
                consistency_report=check_consistency(full_text=body, authors=authors, references=refs, abstract=abstract),
                ml_results=ml,
                extraction_quality=quality,
            )
        )
        assert report.risk_level == "low"
        assert report.confidence >= 0.50

    def test_case_c_missing_doi_not_marked_fraud(self):
        """Older paper without visible DOI must not trigger fraud signals."""
        body = "Historical analysis of algorithms from 1980. " * 30
        report = check_consistency(full_text=body, references=[])
        assert not any("doi" in f.rule.lower() for f in report.flags)

    def test_case_d_unlabelled_abstract_structural_fallback(self):
        lines = [
            "Paper Title Here",
            "Author Name",
            "This is an unlabelled abstract block that discusses the research problem, "
            "the methodology used in experiments, and the conclusions reached by the authors. " * 3,
            "1. Introduction",
            "The field of study began decades ago...",
        ]
        abstract, status, conf = _detect_abstract_detailed(lines)
        assert status == "found"
        assert conf >= 0.70
        assert "unlabelled abstract block" in abstract

    def test_case_h_hyphenation_normalization(self):
        raw = "The distribu-\nted real-time compu-\nting systems operate reliably."
        clean = normalize_pdf_text(raw)
        assert "distributed" in clean
        assert "computing" in clean


from pathlib import Path
from fastapi.testclient import TestClient
from app.main import app
from app.services.pdf_parser import parse_pdf_bytes

IEEE_REGRESSION_PDF = Path(r"C:\Users\Nihaal bhardwaj\Downloads\ramanathan-shin-ieee-proceedings.pdf")


class TestIEEEHistoricalPaperRegression:
    """End-to-end regression tests verifying the real historical IEEE paper."""

    @pytest.fixture
    def pdf_bytes(self):
        if not IEEE_REGRESSION_PDF.exists():
            pytest.skip(f"Regression PDF fixture not found at {IEEE_REGRESSION_PDF}")
        return IEEE_REGRESSION_PDF.read_bytes()

    def test_1_abstract_purity(self, pdf_bytes):
        """TEST 1 — ABSTRACT PURITY:

        - status = found
        - confidence >= 0.90
        - author names absent
        - IEEE membership strings absent
        - 'Invited Paper' absent
        - decorative characters absent
        - actual abstract prose present starting with 'This paper surveys...'
        """
        parsed = parse_pdf_bytes(pdf_bytes, IEEE_REGRESSION_PDF.name)
        assert parsed.abstract_status == "found"
        assert parsed.abstract_confidence is not None
        assert parsed.abstract_confidence >= 0.90
        assert parsed.abstract is not None

        # Abstract must begin with the actual prose
        assert parsed.abstract.startswith("This paper surveys the state of the art in real-time computing.")

        # Contamination checks
        for author in parsed.authors:
            assert author.lower() not in parsed.abstract.lower()
        assert "KANG G. SHIN" not in parsed.abstract
        assert "PARAMESWARAN RAMANATHAN" not in parsed.abstract
        assert "FELLOW, IEEE" not in parsed.abstract
        assert "MEMBER, IEEE" not in parsed.abstract
        assert "Invited Paper" not in parsed.abstract
        assert "~~" not in parsed.abstract

    def test_2_reference_recovery_and_dynamic_validation(self, pdf_bytes):
        """TEST 2 — REFERENCE RECOVERY:

        - highest observed reference number in the 100+ range
        - entries around [100]-[112] individually detectable
        - parser does not collapse high-numbered references into one entry
        - reference validation reports actual gaps instead of inventing entries
        - unnumbered preceding entries segmented with number=None
        """
        parsed = parse_pdf_bytes(pdf_bytes, IEEE_REGRESSION_PDF.name)
        assert parsed.reference_validation is not None

        val = parsed.reference_validation
        # Highest observed reference reaches 112 (high-numbered range)
        assert val["highest_observed_reference"] is not None
        assert val["highest_observed_reference"] >= 100
        assert val["highest_observed_reference"] == 112

        # Check high-numbered entries exist individually
        entry_numbers = [e["number"] for e in parsed.references if e.get("number") is not None]
        for expected_num in (100, 104, 108, 110, 111, 112):
            assert expected_num in entry_numbers

        # No duplicate entries created
        assert val["duplicate_numbers"] == []

        # Real gaps accurately identified without inventing fake references
        assert 1 in val["missing_numbers"]
        assert 26 in val["missing_numbers"]
        assert 27 not in val["missing_numbers"]  # [27] was detected

        # Preceding unnumbered entries detected with number=None
        assert val["unnumbered_entries"] > 0
        unnumbered = [e for e in parsed.references if e.get("number") is None]
        assert len(unnumbered) == val["unnumbered_entries"]
        assert all(len(e["raw_text"]) >= 10 for e in unnumbered)

    def test_3_metadata_end_to_end(self, pdf_bytes):
        """TEST 3 — METADATA END-TO-END:

        - calls POST /api/v1/analyze/full
        - metadata module executes
        - modules_used contains 'metadata'
        - paper_metadata exists and status is exposed
        """
        client = TestClient(app)
        resp = client.post(
            "/api/v1/analyze/full",
            files={"file": (IEEE_REGRESSION_PDF.name, pdf_bytes, "application/pdf")},
        )
        assert resp.status_code == 200
        data = resp.json()

        assert "metadata" in data["modules_used"]
        assert data.get("paper_metadata") is not None
        assert "status" in data["paper_metadata"]
        assert data.get("metadata_verification") is not None

    def test_4_false_positive_protection(self, pdf_bytes):
        """TEST 4 — FALSE POSITIVE PROTECTION:

        Legitimate IEEE paper must not become HIGH/CRITICAL solely because of
        missing DOI, API timeouts, or partial reference degradation.
        """
        client = TestClient(app)
        resp = client.post(
            "/api/v1/analyze/full",
            files={"file": (IEEE_REGRESSION_PDF.name, pdf_bytes, "application/pdf")},
        )
        assert resp.status_code == 200
        data = resp.json()

        assert data["risk_score"] <= 25.0
        assert data["risk_level"] == "low"
        assert data["assessment_status"] in ("evaluated", "limited_evidence")
