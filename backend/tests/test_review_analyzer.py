"""Tests for individual review authenticity analyzer rules and scoring."""

from app.schemas.reviews import ReviewSignal, ScrapedReview
from app.services.reviews.review_analyzer import (
    analyze_review,
    calculate_review_authenticity_score,
)


def test_rule_1_too_short():
    """Reviews with fewer than 5 words trigger 'too_short'."""
    review = ScrapedReview(review_text="Great headphones.")
    signals = analyze_review(review)

    rules = [s.rule for s in signals]
    assert "too_short" in rules
    short_sig = next(s for s in signals if s.rule == "too_short")
    assert short_sig.severity == "low"


def test_rule_1_unusually_long():
    """Reviews exceeding 500 words trigger 'unusually_long'."""
    long_text = "word " * 520
    review = ScrapedReview(review_text=long_text)
    signals = analyze_review(review)

    rules = [s.rule for s in signals]
    assert "unusually_long" in rules
    long_sig = next(s for s in signals if s.rule == "unusually_long")
    assert long_sig.severity == "low"


def test_rule_2_superlative_stuffing():
    """Reviews with high density of generic superlatives trigger 'superlative_stuffing'."""
    text = (
        "This is amazing, excellent, best, perfect, awesome, incredible, outstanding, "
        "fantastic, wonderful, and I love it and highly recommend this item!"
    )
    review = ScrapedReview(review_text=text)
    signals = analyze_review(review)

    rules = [s.rule for s in signals]
    assert "superlative_stuffing" in rules
    sig = next(s for s in signals if s.rule == "superlative_stuffing")
    assert sig.severity == "medium"


def test_rule_3_generic_no_detail():
    """Reviews longer than 15 words with zero concrete details and high superlatives trigger 'generic_no_detail'."""
    text = (
        "Amazing amazing best product ever love it so good so wonderful amazing fantastic "
        "highly recommend perfect product ever and always!"
    )
    review = ScrapedReview(review_text=text)
    signals = analyze_review(review)

    rules = [s.rule for s in signals]
    assert "generic_no_detail" in rules
    sig = next(s for s in signals if s.rule == "generic_no_detail")
    assert sig.severity == "medium"
    assert "without concrete details" in sig.message


def test_rule_3_dosage_duration_avoids_flag():
    """Reviews mentioning dosage/duration (e.g. used it daily for 60 days) are not flagged."""
    text = "I used it daily for 60 days and experienced consistent results across the board."
    review = ScrapedReview(review_text=text)
    signals = analyze_review(review)

    rules = [s.rule for s in signals]
    assert "generic_no_detail" not in rules


def test_rule_3_comparative_language_avoids_flag():
    """Reviews with comparative or causal language are not flagged."""
    text = (
        "This is much better than before, since I started using it I noticed a real difference."
    )
    review = ScrapedReview(review_text=text)
    signals = analyze_review(review)

    rules = [s.rule for s in signals]
    assert "generic_no_detail" not in rules


def test_rule_3_real_supplement_review_1_not_flagged():
    """Real health supplement review with dosage/duration/outcome is not flagged."""
    text = "Despite of using One capsule a day for 60 days also, I am yet to see the basic improvement"
    review = ScrapedReview(review_text=text)
    signals = analyze_review(review)

    rules = [s.rule for s in signals]
    assert "generic_no_detail" not in rules


def test_rule_3_real_supplement_review_2_not_flagged():
    """Real health supplement review with timeframe, symptoms and outcomes is not flagged."""
    text = "used for a year, immunity improved, muscle cramps gone"
    review = ScrapedReview(review_text=text)
    signals = analyze_review(review)

    rules = [s.rule for s in signals]
    assert "generic_no_detail" not in rules


def test_rule_3_specific_detail_present_avoids_flag():
    """Reviews mentioning specific feature words or numbers do not trigger 'generic_no_detail'."""
    text = (
        "I really appreciated the battery life and the affordable price for everyday usage "
        "and I enjoy having it around the house."
    )
    review = ScrapedReview(review_text=text)
    signals = analyze_review(review)

    rules = [s.rule for s in signals]
    assert "generic_no_detail" not in rules


def test_rule_4_excessive_punctuation():
    """Reviews with excessive exclamation or emojis trigger 'excessive_punctuation'."""
    text = "Great product! Wow! Amazing! Super! Fantastic! Loved it!"
    review = ScrapedReview(review_text=text)
    signals = analyze_review(review)

    rules = [s.rule for s in signals]
    assert "excessive_punctuation" in rules
    sig = next(s for s in signals if s.rule == "excessive_punctuation")
    assert sig.severity == "low"


def test_rule_5_rating_sentiment_mismatch_5_star_negative():
    """5-star review with predominantly negative words triggers 'rating_sentiment_mismatch'."""
    text = "Terrible, broken, poor performance, hated this bad product."
    review = ScrapedReview(review_text=text, rating=5)
    signals = analyze_review(review)

    rules = [s.rule for s in signals]
    assert "rating_sentiment_mismatch" in rules
    sig = next(s for s in signals if s.rule == "rating_sentiment_mismatch")
    assert sig.severity == "high"


def test_rule_5_rating_sentiment_mismatch_1_star_positive():
    """1-star review with predominantly positive words triggers 'rating_sentiment_mismatch'."""
    text = "Great, good, loved it, satisfied, wonderful, happy."
    review = ScrapedReview(review_text=text, rating=1)
    signals = analyze_review(review)

    rules = [s.rule for s in signals]
    assert "rating_sentiment_mismatch" in rules
    sig = next(s for s in signals if s.rule == "rating_sentiment_mismatch")
    assert sig.severity == "high"


def test_rule_5_rating_none_skips_mismatch():
    """When rating is None, rating-sentiment mismatch is skipped."""
    text = "Terrible, broken, poor performance, hated this bad product."
    review = ScrapedReview(review_text=text, rating=None)
    signals = analyze_review(review)

    rules = [s.rule for s in signals]
    assert "rating_sentiment_mismatch" not in rules


def test_rule_5_shampoo_before_after_review_not_flagged():
    """Real before/after dandruff shampoo review with rating=5 does not trigger rating_sentiment_mismatch."""
    text = (
        "I was looking for an exfoliating shampoo as I started getting dandruff bad. "
        "I was washing once a week and by day 4 I was getting huge flakes. "
        "I then found this brand and decided to give it a try. "
        "I now wash twice a week with this shampoo. "
        "This is my 4th use just about, and I have not seen flakes since... "
        "It seems to be effective thus far."
    )
    review = ScrapedReview(review_text=text, rating=5)
    signals = analyze_review(review)

    rules = [s.rule for s in signals]
    assert "rating_sentiment_mismatch" not in rules


def test_rule_5_acne_before_after_review_not_flagged():
    """Before/after review describing past acne problem and cleared-up outcome is not flagged."""
    text = (
        "I had terrible acne before using this. After 2 weeks, my skin cleared up completely "
        "and I haven't had a breakout since."
    )
    review = ScrapedReview(review_text=text, rating=5)
    signals = analyze_review(review)

    rules = [s.rule for s in signals]
    assert "rating_sentiment_mismatch" not in rules


def test_rule_5_genuine_mismatch_5_star_triggers():
    """Defective product review with 5-star rating triggers rating_sentiment_mismatch."""
    text = (
        "This product is defective, stopped working after one day, waste of money, "
        "extremely disappointed"
    )
    review = ScrapedReview(review_text=text, rating=5)
    signals = analyze_review(review)

    rules = [s.rule for s in signals]
    assert "rating_sentiment_mismatch" in rules
    sig = next(s for s in signals if s.rule == "rating_sentiment_mismatch")
    assert sig.severity == "high"
    assert "describes specific problems with the product itself" in sig.message


def test_rule_5_negated_symptom_not_flagged():
    """Review with negated symptom ('not had any flakes since...') does not trigger mismatch."""
    text = "I have not had any flakes since I started using this shampoo"
    review = ScrapedReview(review_text=text, rating=5)
    signals = analyze_review(review)

    rules = [s.rule for s in signals]
    assert "rating_sentiment_mismatch" not in rules


def test_rule_5_low_rating_genuine_complaint_not_flagged():
    """Consistent 1-star review with genuine complaints does not trigger mismatch."""
    text = "Poor quality, broke within a week, don't recommend"
    review = ScrapedReview(review_text=text, rating=1)
    signals = analyze_review(review)

    rules = [s.rule for s in signals]
    assert "rating_sentiment_mismatch" not in rules


def test_rule_5_low_rating_mismatch_triggers():
    """Inconsistent 1-star review with pure praise text triggers rating_sentiment_mismatch."""
    text = "Great product, works perfectly, very happy"
    review = ScrapedReview(review_text=text, rating=1)
    signals = analyze_review(review)

    rules = [s.rule for s in signals]
    assert "rating_sentiment_mismatch" in rules
    sig = next(s for s in signals if s.rule == "rating_sentiment_mismatch")
    assert sig.severity == "high"
    assert "Low rating but review text contains predominantly positive language" in sig.message


def test_rule_7_unverified_purchase_high_praise():
    """Unverified purchase combined with high superlative density triggers 'unverified_high_praise'."""
    text = "This is amazing, excellent, best, perfect, awesome, incredible, outstanding item!"
    review = ScrapedReview(review_text=text, verified_purchase=False)
    signals = analyze_review(review)

    rules = [s.rule for s in signals]
    assert "unverified_high_praise" in rules
    sig = next(s for s in signals if s.rule == "unverified_high_praise")
    assert sig.severity == "medium"


def test_rule_7_verified_purchase_does_not_trigger_unverified_praise():
    """Verified purchase does not trigger 'unverified_high_praise'."""
    text = "This is amazing, excellent, best, perfect, awesome, incredible, outstanding item!"
    review = ScrapedReview(review_text=text, verified_purchase=True)
    signals = analyze_review(review)

    rules = [s.rule for s in signals]
    assert "unverified_high_praise" not in rules


def test_normal_balanced_review_clean():
    """A realistic balanced review with details triggers zero suspicious signals."""
    text = (
        "The screen quality is clear and the battery lasts about seven hours. "
        "The packaging was neat, though the delivery took an extra day. "
        "Overall a fair purchase for the price."
    )
    review = ScrapedReview(review_text=text, rating=4, verified_purchase=True)
    signals = analyze_review(review)

    assert len(signals) == 0


def test_calculate_review_authenticity_score_points_and_cap():
    """Scores correctly aggregate high=15, medium=8, low=3 and cap at 100.0."""
    signals = [
        ReviewSignal(rule="sig1", severity="high", message="m"),    # 15
        ReviewSignal(rule="sig2", severity="medium", message="m"),  # 8
        ReviewSignal(rule="sig3", severity="low", message="m"),     # 3
    ]
    score = calculate_review_authenticity_score(signals)
    assert score == 26.0

    # Test capping at 100.0
    many_high_signals = [ReviewSignal(rule=f"h{i}", severity="high", message="m") for i in range(10)]  # 150
    capped_score = calculate_review_authenticity_score(many_high_signals)
    assert capped_score == 100.0


def test_rule_8_product_category_incoherence_fires():
    """Review mentioning 3+ unrelated product categories fires Rule 8 with high severity."""
    text = "best phone ever it dries my scalp and reduces hairfall which improved my heart health"
    review = ScrapedReview(review_text=text, rating=1)
    signals = analyze_review(review)

    rules = [s.rule for s in signals]
    assert "product_category_incoherence" in rules
    sig = next(s for s in signals if s.rule == "product_category_incoherence")
    assert sig.severity == "high"
    assert "multiple unrelated product categories" in sig.message


def test_rule_8_single_category_electronics_does_not_fire():
    """Review with terms from only 1 category does not trigger Rule 8."""
    text = "great phone, fast charging, good camera"
    review = ScrapedReview(review_text=text, rating=5)
    signals = analyze_review(review)

    rules = [s.rule for s in signals]
    assert "product_category_incoherence" not in rules


def test_rule_8_two_categories_haircare_and_sensory_does_not_fire():
    """Review with terms from only 2 categories (haircare + sensory) does not trigger Rule 8."""
    text = "amazing shampoo, no more dandruff, smells great"
    review = ScrapedReview(review_text=text, rating=5)
    signals = analyze_review(review)

    rules = [s.rule for s in signals]
    assert "product_category_incoherence" not in rules


def test_rule_8_electronics_haircare_health_fires():
    """Review explicitly combining electronics, haircare, and health terms fires Rule 8."""
    text = "The battery life of this phone helps my hair condition while stabilizing blood pressure."
    review = ScrapedReview(review_text=text, rating=5)
    signals = analyze_review(review)

    rules = [s.rule for s in signals]
    assert "product_category_incoherence" in rules
    sig = next(s for s in signals if s.rule == "product_category_incoherence")
    assert sig.severity == "high"

