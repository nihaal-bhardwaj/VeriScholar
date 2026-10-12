"""Tests for the Groq LLM Review Analyzer service and integration pipeline."""

import json
import time
from unittest.mock import MagicMock, patch

import pytest

from app.schemas.reviews import (
    LLMReviewAnalysis,
    LLMSignal,
    ScrapedReview,
    ScrapedReviewData,
)
from app.services.reviews.llm_analyzer import (
    analyze_review_with_llm,
    analyze_reviews_batch_with_llm,
)
from app.services.reviews.review_report_generator import generate_review_report


@pytest.fixture
def mock_settings():
    """Mock application settings with a valid Groq API key."""
    with patch("app.services.reviews.llm_analyzer.get_settings") as mock:
        settings_instance = MagicMock()
        settings_instance.groq_api_key = "gsk_test_mock_key_1234567890"
        mock.return_value = settings_instance
        yield mock


def test_successful_llm_call_valid_json(mock_settings):
    """Successful LLM call with valid JSON response returns populated LLMReviewAnalysis."""
    valid_payload = {
        "authenticity_score": 88,
        "classification": "likely_genuine",
        "confidence": "high",
        "reasoning": "Detailed personal context and specific usage narrative indicate genuine experience.",
        "signals": [
            {
                "type": "before_after_narrative",
                "is_suspicious": False,
                "description": "User describes dandruff issue clearing up over 4 uses.",
            },
            {
                "type": "specific_detail_present",
                "is_suspicious": False,
                "description": "Mentions wash schedule and specific bottle usage.",
            },
        ],
        "llm_available": True,
    }

    mock_chat_completion = MagicMock()
    mock_chat_completion.choices = [
        MagicMock(message=MagicMock(content=json.dumps(valid_payload)))
    ]

    with patch("app.services.reviews.llm_analyzer.Groq") as mock_groq:
        client_instance = MagicMock()
        client_instance.chat.completions.create.return_value = mock_chat_completion
        mock_groq.return_value = client_instance

        review = ScrapedReview(
            review_text=(
                "I was looking for an exfoliating shampoo as I started getting dandruff bad. "
                "I now wash twice a week with this shampoo and have not seen flakes since."
            ),
            reviewer_name="Jordan",
            rating=5,
            verified_purchase=True,
        )

        result = analyze_review_with_llm(review, product_title="Anti-Dandruff Scalp Shampoo")

        assert result.llm_available is True
        assert result.authenticity_score == 88
        assert result.classification == "likely_genuine"
        assert result.confidence == "high"
        assert "Detailed personal context" in result.reasoning
        assert len(result.signals) == 2
        assert result.signals[0].type == "before_after_narrative"
        assert result.signals[0].is_suspicious is False
        assert result.fallback_reason is None


def test_llm_malformed_json_retry_succeeds(mock_settings):
    """LLM returns malformed JSON on first attempt, retries with fallback prompt, and succeeds."""
    malformed_output = "I evaluated the review. Here is what I think: {authenticity_score: 85, invalid json"
    valid_fallback_payload = {
        "authenticity_score": 82,
        "classification": "likely_genuine",
        "confidence": "medium",
        "reasoning": "Product worked as expected with realistic details.",
        "signals": [],
        "llm_available": True,
    }

    mock_resp_malformed = MagicMock(choices=[MagicMock(message=MagicMock(content=malformed_output))])
    mock_resp_fallback = MagicMock(
        choices=[MagicMock(message=MagicMock(content=json.dumps(valid_fallback_payload)))]
    )

    with patch("app.services.reviews.llm_analyzer.Groq") as mock_groq:
        client_instance = MagicMock()
        client_instance.chat.completions.create.side_effect = [
            mock_resp_malformed,
            mock_resp_fallback,
        ]
        mock_groq.return_value = client_instance

        review = ScrapedReview(
            review_text="Solid build quality, buttons have a satisfying click and cable is braided nicely.",
            rating=5,
        )

        result = analyze_review_with_llm(review)

        assert client_instance.chat.completions.create.call_count == 2
        assert result.llm_available is True
        assert result.authenticity_score == 82
        assert result.classification == "likely_genuine"
        assert result.confidence == "medium"
        assert result.fallback_reason is None


def test_llm_malformed_json_both_attempts_fails(mock_settings):
    """LLM returns malformed JSON on both initial and fallback calls -> parse_error fallback."""
    mock_resp_malformed = MagicMock(
        choices=[MagicMock(message=MagicMock(content="Unparseable gibberish output"))]
    )

    with patch("app.services.reviews.llm_analyzer.Groq") as mock_groq:
        client_instance = MagicMock()
        client_instance.chat.completions.create.side_effect = [
            mock_resp_malformed,
            mock_resp_malformed,
        ]
        mock_groq.return_value = client_instance

        review = ScrapedReview(
            review_text="Tested this gadget for a week and found it quite helpful for daily notes.",
            rating=4,
        )

        result = analyze_review_with_llm(review)

        assert client_instance.chat.completions.create.call_count == 2
        assert result.llm_available is False
        assert result.fallback_reason == "parse_error"
        assert result.authenticity_score == 50


def test_groq_api_timeout(mock_settings):
    """Groq API timeout returns safe LLMReviewAnalysis with fallback_reason='timeout'."""
    with patch("app.services.reviews.llm_analyzer.Groq") as mock_groq:
        client_instance = MagicMock()
        client_instance.chat.completions.create.side_effect = TimeoutError("Request timed out")
        mock_groq.return_value = client_instance

        review = ScrapedReview(
            review_text="Packaging arrived intact and item worked as advertised on the box.",
            rating=5,
        )

        result = analyze_review_with_llm(review)

        assert result.llm_available is False
        assert result.fallback_reason == "timeout"
        assert result.authenticity_score == 50
        assert result.classification == "uncertain"


def test_groq_api_error(mock_settings):
    """Groq API error (e.g. 429 rate limit or 500 error) returns fallback_reason='api_error'."""
    with patch("app.services.reviews.llm_analyzer.Groq") as mock_groq:
        client_instance = MagicMock()
        client_instance.chat.completions.create.side_effect = Exception("429 Rate limit exceeded")
        mock_groq.return_value = client_instance

        review = ScrapedReview(
            review_text="Very good product with excellent finish and durable material throughout.",
            rating=5,
        )

        result = analyze_review_with_llm(review)

        assert result.llm_available is False
        assert result.fallback_reason == "api_error"
        assert result.authenticity_score == 50


def test_groq_api_key_not_configured():
    """GROQ_API_KEY not configured returns fallback_reason='not_configured' without calling Groq."""
    with patch("app.services.reviews.llm_analyzer.get_settings") as mock_s, patch.dict(
        "os.environ", {"GROQ_API_KEY": ""}
    ):
        settings_instance = MagicMock()
        settings_instance.groq_api_key = ""
        mock_s.return_value = settings_instance

        with patch("app.services.reviews.llm_analyzer.Groq") as mock_groq:
            review = ScrapedReview(
                review_text="The sound stage is wide and bass is punchy without distorting vocals.",
                rating=5,
            )

            result = analyze_review_with_llm(review)

            mock_groq.assert_not_called()
            assert result.llm_available is False
            assert result.fallback_reason == "not_configured"


def test_high_severity_duplicate_heuristic_skips_llm():
    """High severity duplicate signal causes pipeline to skip LLM entirely."""
    dup_review_1 = ScrapedReview(
        review_text="This is an exact duplicate review repeated across multiple accounts to manipulate score.",
        rating=5,
        reviewer_name="User A",
    )
    dup_review_2 = ScrapedReview(
        review_text="This is an exact duplicate review repeated across multiple accounts to manipulate score.",
        rating=5,
        reviewer_name="User B",
    )

    data = ScrapedReviewData(
        product_url="https://www.amazon.com/dp/B08N5WRWNW",
        product_title="Gadget",
        reviews=[dup_review_1, dup_review_2],
        total_reviews_found=2,
        scrape_successful=True,
    )

    with patch("app.services.reviews.review_report_generator.analyze_review_with_llm") as mock_llm:
        report = generate_review_report(data)

        mock_llm.assert_not_called()
        assert report.reviews[0].analyzed_by == "heuristics"
        assert report.reviews[1].analyzed_by == "heuristics"
        assert report.duplicate_review_count == 2


def test_zero_heuristic_signals_calls_llm():
    """Reviews with zero heuristic signals now route to LLM (fixing previous bug)."""
    clean_review = ScrapedReview(
        review_text="This laptop stand is sturdy, holds my computer securely and has great rubber grips.",
        rating=5,
        reviewer_name="Taylor",
    )

    data = ScrapedReviewData(
        product_url="https://www.amazon.com/dp/B08N5WRWNW",
        product_title="Laptop Stand",
        reviews=[clean_review],
        total_reviews_found=1,
        scrape_successful=True,
    )

    mock_llm_result = LLMReviewAnalysis(
        authenticity_score=95,
        classification="likely_genuine",
        confidence="high",
        reasoning="Genuine description of product features.",
        signals=[],
        llm_available=True,
    )

    with patch(
        "app.services.reviews.review_report_generator.analyze_review_with_llm",
        return_value=mock_llm_result,
    ) as mock_llm:
        report = generate_review_report(data)

        mock_llm.assert_called_once()
        assert report.reviews[0].analyzed_by == "llm"
        # 100 - 95 authenticity = 5 suspicion score
        assert report.reviews[0].authenticity_score == 5.0
        assert report.reviews[0].classification == "likely_genuine"


def test_5_word_review_skips_llm():
    """5-word review does not call LLM (minimum length guard)."""
    five_word_review = ScrapedReview(
        review_text="One two three four five.",  # exactly 5 words
        rating=5,
        reviewer_name="Alex",
    )

    data = ScrapedReviewData(
        product_url="https://www.amazon.com/dp/B08N5WRWNW",
        product_title="Gadget",
        reviews=[five_word_review],
        total_reviews_found=1,
        scrape_successful=True,
    )

    with patch("app.services.reviews.review_report_generator.analyze_review_with_llm") as mock_llm:
        report = generate_review_report(data)

        mock_llm.assert_not_called()
        assert report.reviews[0].analyzed_by == "heuristics"


def test_4_word_review_skips_llm():
    """4-word review does not call LLM."""
    four_word_review = ScrapedReview(
        review_text="Great product works well.",  # 4 words
        rating=5,
        reviewer_name="Alex",
    )

    data = ScrapedReviewData(
        product_url="https://www.amazon.com/dp/B08N5WRWNW",
        product_title="Gadget",
        reviews=[four_word_review],
        total_reviews_found=1,
        scrape_successful=True,
    )

    with patch("app.services.reviews.review_report_generator.analyze_review_with_llm") as mock_llm:
        report = generate_review_report(data)

        mock_llm.assert_not_called()
        assert report.reviews[0].analyzed_by == "heuristics"


def test_incoherent_review_with_category_incoherence_high_calls_llm():
    """Review with product_category_incoherence HIGH signal IS still sent to LLM."""
    incoherent_review = ScrapedReview(
        review_text="best phone ever it dries my scalp and reduces hairfall which improved my heart health",
        rating=1,
        reviewer_name="Bot Reviewer",
    )

    data = ScrapedReviewData(
        product_url="https://www.amazon.com/dp/B08N5WRWNW",
        product_title="Smartphone",
        reviews=[incoherent_review],
        total_reviews_found=1,
        scrape_successful=True,
    )

    mock_llm_result = LLMReviewAnalysis(
        authenticity_score=5,  # Very fake (0-10 guideline)
        classification="likely_fake",
        confidence="high",
        reasoning="Completely incoherent product features mixing electronics, haircare, and cardiovascular health.",
        signals=[
            LLMSignal(
                type="product_incoherence",
                is_suspicious=True,
                description="Impossible product claims spanning unrelated categories.",
            )
        ],
        llm_available=True,
    )

    with patch(
        "app.services.reviews.review_report_generator.analyze_review_with_llm",
        return_value=mock_llm_result,
    ) as mock_llm:
        report = generate_review_report(data)

        mock_llm.assert_called_once()
        # Triggered both Rule 8 (heuristic) and LLM -> "llm+heuristics"
        assert report.reviews[0].analyzed_by == "llm+heuristics"
        # 100 - 5 = 95 suspicion score, max(95, 15 heuristic) = 95.0
        assert report.reviews[0].authenticity_score == 95.0
        assert report.reviews[0].classification == "likely_fake"
        rules = [s.rule for s in report.reviews[0].signals]
        assert "product_category_incoherence" in rules


def test_score_inversion_authenticity_10_yields_suspicion_90():
    """LLM returning authenticity_score=10 (very fake) yields final suspicion_score=90."""
    review = ScrapedReview(
        review_text="Completely generic praise with unnatural keyword repetitions throughout.",
        rating=5,
    )

    data = ScrapedReviewData(
        product_url="https://www.amazon.com/dp/B08N5WRWNW",
        product_title="Item",
        reviews=[review],
        total_reviews_found=1,
        scrape_successful=True,
    )

    mock_llm_result = LLMReviewAnalysis(
        authenticity_score=10,
        classification="likely_fake",
        confidence="high",
        reasoning="Unnatural templated text.",
        signals=[],
        llm_available=True,
    )

    with patch(
        "app.services.reviews.review_report_generator.analyze_review_with_llm",
        return_value=mock_llm_result,
    ):
        report = generate_review_report(data)

        # 100 - 10 = 90 suspicion
        assert report.reviews[0].authenticity_score == 90.0
        assert report.reviews[0].classification == "likely_fake"


def test_llm_genuine_with_high_heuristic_takes_max():
    """If LLM returns authenticity_score=90 (genuine, suspicion=10) but heuristic has HIGH signal, max wins."""
    # Rating 5 with negative complaint text triggers rating_sentiment_mismatch (severity=high, score=15)
    review = ScrapedReview(
        review_text="Terrible, broken, poor performance, hated this bad product completely.",
        rating=5,
    )

    data = ScrapedReviewData(
        product_url="https://www.amazon.com/dp/B08N5WRWNW",
        product_title="Item",
        reviews=[review],
        total_reviews_found=1,
        scrape_successful=True,
    )

    # LLM mistakenly thought it was genuine (authenticity 90 -> suspicion 10)
    mock_llm_result = LLMReviewAnalysis(
        authenticity_score=90,
        classification="likely_genuine",
        confidence="low",
        reasoning="Misinterpreted text.",
        signals=[],
        llm_available=True,
    )

    with patch(
        "app.services.reviews.review_report_generator.analyze_review_with_llm",
        return_value=mock_llm_result,
    ):
        report = generate_review_report(data)

        # max(suspicion 10, heuristic 15) = 15.0
        assert report.reviews[0].authenticity_score == 15.0


def test_medium_severity_heuristic_calls_llm():
    """Medium severity heuristic only (e.g. repeated exclamation or moderate signals) triggers LLM."""
    # Text > 10 words, repetitive punctuation triggers excessive_punctuation (medium), but no high severity rule
    medium_review = ScrapedReview(
        review_text=(
            "I have been using this keyboard for my office desk every single day! "
            "Typing feels smooth and the keycaps are comfortable! "
            "Battery lasts long enough! Great purchase!"
        ),
        rating=5,
        reviewer_name="Sam",
    )

    data = ScrapedReviewData(
        product_url="https://www.amazon.com/dp/B08N5WRWNW",
        product_title="Ergonomic Keyboard",
        reviews=[medium_review],
        total_reviews_found=1,
        scrape_successful=True,
    )

    mock_llm_result = LLMReviewAnalysis(
        authenticity_score=85,
        classification="likely_genuine",
        confidence="high",
        reasoning="Consistent daily usage context with enthusiastic but realistic feedback.",
        signals=[
            LLMSignal(
                type="specific_detail_present",
                is_suspicious=False,
                description="Mentions keycaps and battery life.",
            )
        ],
        llm_available=True,
        fallback_reason=None,
    )

    with patch(
        "app.services.reviews.review_report_generator.analyze_review_with_llm",
        return_value=mock_llm_result,
    ) as mock_llm:
        report = generate_review_report(data)

        mock_llm.assert_called_once()
        assert report.reviews[0].analyzed_by == "llm+heuristics"
        # Inverted: 100 - 85 = 15.0 suspicion score
        assert report.reviews[0].authenticity_score == 15.0
        assert report.reviews[0].classification == "likely_genuine"
        assert report.reviews[0].reasoning == mock_llm_result.reasoning


def test_llm_score_overrides_heuristic_score():
    """LLM score completely replaces heuristic score when llm_available is True and no high heuristic."""
    review = ScrapedReview(
        review_text=(
            "I was looking for an exfoliating shampoo as I started getting dandruff bad. "
            "I now wash twice a week with this shampoo and have not seen flakes since."
        ),
        rating=5,
        reviewer_name="Verified Buyer",
        verified_purchase=True,
    )

    data = ScrapedReviewData(
        product_url="https://www.amazon.com/dp/B08N5WRWNW",
        product_title="Scalp Shampoo",
        reviews=[review],
        total_reviews_found=1,
        scrape_successful=True,
    )

    # LLM assigns a high authenticity score (92) -> suspicion score 8.0
    mock_llm_result = LLMReviewAnalysis(
        authenticity_score=92,
        classification="likely_genuine",
        confidence="high",
        reasoning="Genuine problem-solution narrative describing dandruff resolution.",
        signals=[
            LLMSignal(
                type="before_after_narrative",
                is_suspicious=False,
                description="Problem-solution narrative verified.",
            )
        ],
        llm_available=True,
    )

    with patch(
        "app.services.reviews.review_report_generator.analyze_review_with_llm",
        return_value=mock_llm_result,
    ):
        report = generate_review_report(data)

        # Inverted: 100 - 92 = 8.0 suspicion score
        assert report.reviews[0].authenticity_score == 8.0
        assert report.reviews[0].classification == "likely_genuine"
        assert report.overall_trust_score == 8.0
        assert report.reviews[0].reasoning == mock_llm_result.reasoning


def test_batch_llm_delay():
    """Batch function calls analyze_review_with_llm for each review with ~0.2s inter-call delay."""
    reviews = [
        ScrapedReview(review_text="First genuine review with enough details to evaluate authenticity.", rating=5),
        ScrapedReview(review_text="Second genuine review describing product performance over time.", rating=4),
        ScrapedReview(review_text="Third genuine review detailing shipping quality and packaging.", rating=5),
    ]

    mock_analysis = LLMReviewAnalysis(
        authenticity_score=85,
        classification="likely_genuine",
        confidence="high",
        reasoning="Genuine review.",
        signals=[],
        llm_available=True,
    )

    with patch(
        "app.services.reviews.llm_analyzer.analyze_review_with_llm",
        return_value=mock_analysis,
    ) as mock_single:
        start_time = time.perf_counter()
        results = analyze_reviews_batch_with_llm(reviews, product_title="Test Product")
        elapsed = time.perf_counter() - start_time

        assert len(results) == 3
        assert mock_single.call_count == 3
        # 3 reviews -> 2 delays of 0.2s = 0.4s total sleep minimum
        assert elapsed >= 0.35, f"Expected delay >= 0.35s, got {elapsed:.3f}s"
