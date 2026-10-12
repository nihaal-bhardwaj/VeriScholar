"""Tests for the unified review report generator."""

from app.schemas.reviews import ScrapedReview, ScrapedReviewData
from app.services.reviews.review_report_generator import (
    _determine_trust_level,
    generate_review_report,
)


def test_trust_level_threshold_boundaries():
    """Verify exact trust_level boundaries at 25, 26, 50, 51, 75, and 76."""
    assert _determine_trust_level(25.0) == "low_trust_concern"
    assert _determine_trust_level(26.0) == "moderate_concern"
    assert _determine_trust_level(50.0) == "moderate_concern"
    assert _determine_trust_level(51.0) == "high_concern"
    assert _determine_trust_level(75.0) == "high_concern"
    assert _determine_trust_level(76.0) == "critical_concern"


def test_generate_report_zero_reviews():
    """Zero reviews returns insufficient_data report with zero score."""
    data = ScrapedReviewData(
        product_url="https://www.amazon.com/dp/B08N5WRWNW",
        product_title="Test Product",
        reviews=[],
        total_reviews_found=0,
        scrape_successful=True,
    )
    report = generate_review_report(data)

    assert report.total_reviews_analyzed == 0
    assert report.overall_trust_score == 0.0
    assert report.trust_level == "insufficient_data"
    assert "No reviews were found" in report.summary
    assert len(report.reviews) == 0


def test_generate_report_single_review():
    """Single review skips batch analysis and documents it in the summary."""
    data = ScrapedReviewData(
        product_url="https://www.amazon.com/dp/B08N5WRWNW",
        product_title="Solo Product",
        reviews=[
            ScrapedReview(
                review_text="The battery life and screen quality are both high standard for this price.",
                reviewer_name="Sam",
                rating=5,
                verified_purchase=True,
            )
        ],
        total_reviews_found=1,
        scrape_successful=True,
    )
    report = generate_review_report(data)

    assert report.total_reviews_analyzed == 1
    assert "batch pattern analysis was skipped" in report.summary
    assert len(report.batch_signals) == 0
    assert len(report.reviews) == 1
    assert report.duplicate_review_count == 0


def test_generate_report_full_pipeline_with_5_reviews_and_duplicates():
    """Full pipeline with 5 reviews, including duplicates, evaluates all components correctly."""
    duplicate_text = "This item is truly revolutionary for my workspace, completely changed my daily routine!"
    reviews = [
        # Pair of near-duplicate reviews
        ScrapedReview(
            review_text=duplicate_text,
            reviewer_name="User 1",
            rating=5,
            review_date="2024-02-01",
            verified_purchase=False,
        ),
        ScrapedReview(
            review_text=duplicate_text + " Loved it!",
            reviewer_name="User 2",
            rating=5,
            review_date="2024-02-01",
            verified_purchase=False,
        ),
        # Short review
        ScrapedReview(
            review_text="Good product.",
            reviewer_name="User 3",
            rating=4,
            review_date="2024-02-01",
            verified_purchase=True,
        ),
        # Balanced detailed review
        ScrapedReview(
            review_text="The delivery was quick and packaging was sturdy. The battery lasts about eight hours.",
            reviewer_name="User 4",
            rating=5,
            review_date="2024-02-05",
            verified_purchase=True,
        ),
        # Mismatched review
        ScrapedReview(
            review_text="Broken, terrible, hated it, completely disappointed and poor quality.",
            reviewer_name="User 5",
            rating=5,
            review_date="2024-02-10",
            verified_purchase=True,
        ),
    ]

    data = ScrapedReviewData(
        product_url="https://www.amazon.com/dp/B08N5WRWNW",
        product_title="5-Review Test Item",
        reviews=reviews,
        total_reviews_found=5,
        scrape_successful=True,
    )

    report = generate_review_report(data)

    assert report.total_reviews_analyzed == 5
    assert report.duplicate_review_count == 2
    assert len(report.reviews) == 5

    # Check that duplicate reviews received the duplicate signal
    rev1_signals = [s.rule for s in report.reviews[0].signals]
    rev2_signals = [s.rule for s in report.reviews[1].signals]
    assert "duplicate_or_near_duplicate_text" in rev1_signals
    assert "duplicate_or_near_duplicate_text" in rev2_signals

    # Check overall trust score and trust level are populated
    assert 0.0 <= report.overall_trust_score <= 100.0
    assert report.trust_level in (
        "low_trust_concern",
        "moderate_concern",
        "high_concern",
        "critical_concern",
    )
    assert report.summary != ""
