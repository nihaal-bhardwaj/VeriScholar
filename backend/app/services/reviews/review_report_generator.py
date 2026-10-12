"""Unified report generator for product review authenticity."""

from datetime import datetime, timezone
import time
from typing import Optional

from app.schemas.reviews import (
    BatchAnalysisResult,
    ProductReviewReport,
    ReviewAnalysisResult,
    ReviewSignal,
    ScrapedReviewData,
)
from app.services.reviews.llm_analyzer import analyze_review_with_llm
from app.services.reviews.review_analyzer import (
    analyze_review,
    calculate_review_authenticity_score,
)
from app.services.reviews.review_batch_analyzer import analyze_review_batch

# Batch signal weights
_BATCH_SIGNAL_WEIGHTS = {
    "high": 15.0,
    "medium": 8.0,
    "low": 3.0,
}


def _classify_review(authenticity_score: float) -> str:
    """Classify review suspicion level based on heuristic score."""
    if authenticity_score < 20.0:
        return "likely_genuine"
    elif authenticity_score < 50.0:
        return "uncertain"
    else:
        return "likely_fake"


def _determine_trust_level(trust_score: float) -> str:
    """Determine product review trust level from overall trust score."""
    if trust_score <= 25.0:
        return "low_trust_concern"
    elif trust_score <= 50.0:
        return "moderate_concern"
    elif trust_score <= 75.0:
        return "high_concern"
    else:
        return "critical_concern"


def _build_summary(
    trust_level: str,
    total_reviews: int,
    duplicate_count: int,
    batch_signals: list[ReviewSignal],
    single_review: bool = False,
) -> str:
    """Construct human-readable summary for the report."""
    if total_reviews == 0:
        return "No reviews were found for this product."

    if single_review:
        base = "Only one review found — batch pattern analysis was skipped."
        if trust_level == "low_trust_concern":
            return f"{base} The single review appears authentic with minimal suspicion signals."
        else:
            return f"{base} The single review exhibits elevated suspicion patterns."

    level_descriptions = {
        "low_trust_concern": "Product reviews appear mostly authentic with low indicators of manipulation.",
        "moderate_concern": "Product reviews show moderate indicators of potential manipulation or incentivization; review with caution.",
        "high_concern": "Product reviews exhibit significant suspicious patterns (e.g. duplicate phrasing, generic praise, or temporal clustering).",
        "critical_concern": "Product reviews exhibit widespread signals of artificial inflation, duplication, or coordinated manipulation.",
    }
    desc = level_descriptions.get(
        trust_level, "Review analysis completed."
    )

    details = [f"Analyzed {total_reviews} reviews."]
    if duplicate_count > 0:
        details.append(f"Detected {duplicate_count} duplicate or near-duplicate reviews.")
    if batch_signals:
        signals_str = ", ".join(s.rule for s in batch_signals)
        details.append(f"Cross-review signals detected: {signals_str}.")

    return f"{desc} {' '.join(details)}"


def _should_call_llm(heuristic_signals: list[ReviewSignal], review_text: str) -> bool:
    """Decide whether to call the Groq LLM for a review.

    Call LLM for ALL reviews EXCEPT:
      1. Review text has <= 5 words (too short to analyze, let heuristics handle it)
      2. Heuristic signals include severity 'high' AND the signal is a clear-cut
         definitive catch like 'duplicate_text' (near-identical to another review)

    Call LLM for EVERYTHING ELSE including:
      - Reviews with zero heuristic signals
      - Reviews with only low severity signals
      - Reviews with only medium severity signals
      - Short-but-not-too-short reviews (6-15 words)
      - Reviews with non-duplicate high severity signals (e.g. category incoherence)
    """
    words = review_text.split() if review_text else []
    if len(words) <= 5:
        return False

    has_duplicate_high = any(
        s.severity.lower() == "high" and "duplicate" in s.rule.lower()
        for s in heuristic_signals
    )
    if has_duplicate_high:
        return False

    return True


def generate_review_report(scraped_data: ScrapedReviewData) -> ProductReviewReport:
    """Generate a unified review authenticity report.

    Combines heuristic individual analysis, batch patterns, and LLM evaluations.
    """
    reviews = scraped_data.reviews
    total_reviews = len(reviews)

    # Edge Case 1: Zero reviews
    if total_reviews == 0:
        return ProductReviewReport(
            product_url=scraped_data.product_url,
            product_title=scraped_data.product_title,
            source_site=getattr(scraped_data, "source_site", None),
            total_reviews_analyzed=0,
            overall_trust_score=0.0,
            trust_level="insufficient_data",
            reviews=[],
            batch_signals=[],
            duplicate_review_count=0,
            summary="No reviews were found for this product.",
            generated_at=datetime.now(timezone.utc),
        )

    # Edge Case 2: Exactly 1 review (skip batch analysis)
    if total_reviews == 1:
        single_rev = reviews[0]
        h_signals = analyze_review(single_rev)
        h_score = calculate_review_authenticity_score(h_signals)

        if _should_call_llm(h_signals, single_rev.review_text):
            llm_result = analyze_review_with_llm(
                single_rev, product_title=scraped_data.product_title, index=0
            )
            if llm_result.llm_available:
                # Invert LLM authenticity score (0=fake, 100=genuine) to suspicion score (0=genuine, 100=fake)
                llm_suspicion = max(0.0, min(100.0, 100.0 - float(llm_result.authenticity_score)))
                has_high = any(s.severity.lower() == "high" for s in h_signals)
                if has_high:
                    final_score = max(llm_suspicion, float(h_score))
                else:
                    final_score = llm_suspicion
                final_classification = _classify_review(final_score)
                converted_llm_signals = [
                    ReviewSignal(
                        rule=sig.type,
                        severity="medium" if sig.is_suspicious else "low",
                        message=sig.description,
                    )
                    for sig in llm_result.signals
                ]
                high_h_signals = [s for s in h_signals if s.severity.lower() == "high"]
                final_signals = converted_llm_signals + high_h_signals
                analyzed_by = "llm+heuristics" if len(h_signals) > 0 else "llm"
                reasoning = llm_result.reasoning
            else:
                final_score = h_score
                final_classification = _classify_review(h_score)
                final_signals = h_signals
                analyzed_by = "heuristics"
                reasoning = None
        else:
            final_score = h_score
            final_classification = _classify_review(h_score)
            final_signals = h_signals
            analyzed_by = "heuristics"
            reasoning = None

        trust_level = _determine_trust_level(final_score)

        analyzed_review = ReviewAnalysisResult(
            review_text=single_rev.review_text,
            reviewer_name=single_rev.reviewer_name,
            rating=single_rev.rating,
            review_date=single_rev.review_date,
            verified_purchase=single_rev.verified_purchase,
            authenticity_score=final_score,
            classification=final_classification,
            signals=final_signals,
            analyzed_by=analyzed_by,
            reasoning=reasoning,
        )

        summary = _build_summary(
            trust_level=trust_level,
            total_reviews=1,
            duplicate_count=0,
            batch_signals=[],
            single_review=True,
        )

        return ProductReviewReport(
            product_url=scraped_data.product_url,
            product_title=scraped_data.product_title,
            source_site=getattr(scraped_data, "source_site", None),
            total_reviews_analyzed=1,
            overall_trust_score=round(final_score, 1),
            trust_level=trust_level,
            reviews=[analyzed_review],
            batch_signals=[],
            duplicate_review_count=0,
            summary=summary,
            generated_at=datetime.now(timezone.utc),
        )

    # Standard Case: 2+ reviews
    # 1. Individual heuristic analysis
    per_review_signals: list[list[ReviewSignal]] = [analyze_review(r) for r in reviews]

    # 2. Batch analysis
    batch_result: BatchAnalysisResult = analyze_review_batch(reviews)

    # 3. Add Rule 6 (duplicate detection) to individual reviews in duplicate_pairs
    duplicate_indices: set[int] = set()
    for i, j in batch_result.duplicate_pairs:
        duplicate_indices.add(i)
        duplicate_indices.add(j)

    for idx in duplicate_indices:
        per_review_signals[idx].append(
            ReviewSignal(
                rule="duplicate_or_near_duplicate_text",
                severity="high",
                message="This review is nearly identical to another review on this product — a strong signal of fake reviews",
            )
        )

    # 4. For each review, evaluate whether to call LLM, with 0.2s delay between calls
    analyzed_reviews: list[ReviewAnalysisResult] = []
    scores: list[float] = []
    llm_call_count = 0

    for idx, (r, h_sigs) in enumerate(zip(reviews, per_review_signals)):
        h_score = calculate_review_authenticity_score(h_sigs)

        if _should_call_llm(h_sigs, r.review_text):
            if llm_call_count > 0:
                time.sleep(0.2)
            llm_call_count += 1

            llm_result = analyze_review_with_llm(
                r, product_title=scraped_data.product_title, index=idx
            )
            if llm_result.llm_available:
                # Invert LLM authenticity score (0=fake, 100=genuine) to suspicion score (0=genuine, 100=fake)
                llm_suspicion = max(0.0, min(100.0, 100.0 - float(llm_result.authenticity_score)))
                has_high = any(s.severity.lower() == "high" for s in h_sigs)
                if has_high:
                    final_score = max(llm_suspicion, float(h_score))
                else:
                    final_score = llm_suspicion
                final_classification = _classify_review(final_score)
                converted_llm_signals = [
                    ReviewSignal(
                        rule=sig.type,
                        severity="medium" if sig.is_suspicious else "low",
                        message=sig.description,
                    )
                    for sig in llm_result.signals
                ]
                high_h_signals = [s for s in h_sigs if s.severity.lower() == "high"]
                final_signals = converted_llm_signals + high_h_signals
                analyzed_by = "llm+heuristics" if len(h_sigs) > 0 else "llm"
                reasoning = llm_result.reasoning
            else:
                final_score = h_score
                final_classification = _classify_review(h_score)
                final_signals = h_sigs
                analyzed_by = "heuristics"
                reasoning = None
        else:
            final_score = h_score
            final_classification = _classify_review(h_score)
            final_signals = h_sigs
            analyzed_by = "heuristics"
            reasoning = None

        scores.append(final_score)
        analyzed_reviews.append(
            ReviewAnalysisResult(
                review_text=r.review_text,
                reviewer_name=r.reviewer_name,
                rating=r.rating,
                review_date=r.review_date,
                verified_purchase=r.verified_purchase,
                authenticity_score=final_score,
                classification=final_classification,
                signals=final_signals,
                analyzed_by=analyzed_by,
                reasoning=reasoning,
            )
        )

    # 5. Overall product trust score calculation
    avg_individual_score = sum(scores) / total_reviews if total_reviews > 0 else 0.0

    batch_pts = sum(
        _BATCH_SIGNAL_WEIGHTS.get(sig.severity.lower(), 0.0)
        for sig in batch_result.product_level_signals
    )
    # Capped at 30.0 points total from batch signals
    batch_contribution = min(30.0, float(batch_pts))

    overall_trust_score = round(
        min(100.0, max(0.0, avg_individual_score + batch_contribution)), 1
    )

    trust_level = _determine_trust_level(overall_trust_score)

    summary = _build_summary(
        trust_level=trust_level,
        total_reviews=total_reviews,
        duplicate_count=batch_result.reviews_flagged_as_duplicate,
        batch_signals=batch_result.product_level_signals,
    )

    return ProductReviewReport(
        product_url=scraped_data.product_url,
        product_title=scraped_data.product_title,
        source_site=getattr(scraped_data, "source_site", None),
        total_reviews_analyzed=total_reviews,
        overall_trust_score=overall_trust_score,
        trust_level=trust_level,
        reviews=analyzed_reviews,
        batch_signals=batch_result.product_level_signals,
        duplicate_review_count=batch_result.reviews_flagged_as_duplicate,
        summary=summary,
        generated_at=datetime.now(timezone.utc),
    )
