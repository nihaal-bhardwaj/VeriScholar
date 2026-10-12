"""Tests for cross-review batch pattern analyzer."""

from app.schemas.reviews import ScrapedReview
from app.services.reviews.review_batch_analyzer import analyze_review_batch


def test_batch_analyzer_empty_reviews_list():
    """Empty review list returns empty result without crashing."""
    result = analyze_review_batch([])
    assert result.reviews_flagged_as_duplicate == 0
    assert len(result.duplicate_pairs) == 0
    assert len(result.product_level_signals) == 0


def test_batch_analyzer_single_review():
    """Single review gracefully skips batch comparison rules."""
    reviews = [
        ScrapedReview(
            review_text="This is a good item with solid battery life and quality.",
            reviewer_name="User123",
            review_date="2024-01-01",
        )
    ]
    result = analyze_review_batch(reviews)
    assert result.reviews_flagged_as_duplicate == 0
    assert len(result.duplicate_pairs) == 0
    assert len(result.product_level_signals) == 0


def test_batch_analyzer_duplicate_detection():
    """Two near-identical reviews (>0.85 similarity) are flagged as duplicates."""
    rev1 = ScrapedReview(
        review_text="This is an absolutely fantastic product that worked wonders for my home setup today!",
        reviewer_name="User A",
    )
    rev2 = ScrapedReview(
        review_text="This is an absolutely fantastic product that worked wonders for my home setup today.",
        reviewer_name="User B",
    )
    rev3 = ScrapedReview(
        review_text="Completely different review focusing on the packaging, color, and delivery time.",
        reviewer_name="User C",
    )

    result = analyze_review_batch([rev1, rev2, rev3])
    assert result.reviews_flagged_as_duplicate == 2
    assert len(result.duplicate_pairs) == 1
    assert result.duplicate_pairs[0] == (0, 1)


def test_batch_analyzer_all_unique_reviews():
    """Batch with all distinct reviews has zero duplicate pairs."""
    rev1 = ScrapedReview(
        review_text="The battery life lasts throughout the workday and charges in under an hour.",
        reviewer_name="User A",
    )
    rev2 = ScrapedReview(
        review_text="Audio quality is decent for podcasts, though bass is slightly subdued.",
        reviewer_name="User B",
    )
    rev3 = ScrapedReview(
        review_text="The color was exactly as shown in the picture, and delivery was prompt.",
        reviewer_name="User C",
    )

    result = analyze_review_batch([rev1, rev2, rev3])
    assert result.reviews_flagged_as_duplicate == 0
    assert len(result.duplicate_pairs) == 0


def test_batch_analyzer_burst_pattern_detection():
    """More than 30% reviews sharing the same date triggers review_burst_pattern."""
    reviews = [
        ScrapedReview(review_text="Review one details about size.", review_date="2024-03-15"),
        ScrapedReview(review_text="Review two details about quality.", review_date="2024-03-15"),
        ScrapedReview(review_text="Review three details about price.", review_date="2024-03-15"),
        ScrapedReview(review_text="Review four details about screen.", review_date="2024-01-10"),
        ScrapedReview(review_text="Review five details about delivery.", review_date="2024-02-20"),
    ]
    # 3 out of 5 reviews (60%) share 2024-03-15 > 30% threshold
    result = analyze_review_batch(reviews)

    rules = [s.rule for s in result.product_level_signals]
    assert "review_burst_pattern" in rules
    burst_sig = next(s for s in result.product_level_signals if s.rule == "review_burst_pattern")
    assert burst_sig.severity == "medium"


def test_batch_analyzer_suspicious_reviewer_names():
    """More than 20% of reviewers having generic/numeric names triggers suspicious_reviewer_names."""
    reviews = [
        ScrapedReview(review_text="Review one with details.", reviewer_name="Amazon Customer"),
        ScrapedReview(review_text="Review two with details.", reviewer_name="987654321"),
        ScrapedReview(review_text="Review three with details.", reviewer_name="Sarah Connor"),
        ScrapedReview(review_text="Review four with details.", reviewer_name="David Miller"),
    ]
    # 2 out of 4 (50%) are generic/numeric > 20% threshold
    result = analyze_review_batch(reviews)

    rules = [s.rule for s in result.product_level_signals]
    assert "suspicious_reviewer_names" in rules
    name_sig = next(s for s in result.product_level_signals if s.rule == "suspicious_reviewer_names")
    assert name_sig.severity == "low"
