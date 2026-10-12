"""Batch analyzer for detecting cross-review patterns and coordination."""

from collections import Counter
import difflib
import re
from typing import Optional

from app.schemas.reviews import BatchAnalysisResult, ReviewSignal, ScrapedReview

# Common generic reviewer names across e-commerce platforms
_GENERIC_REVIEWER_NAMES = {
    "amazon customer",
    "flipkart customer",
    "customer",
    "anonymous",
    "user",
    "buyer",
    "verified buyer",
}

# Date regex patterns for standard date extractions
_DATE_PATTERNS = [
    re.compile(r"\b\d{4}-\d{2}-\d{2}\b"),  # 2024-01-15
    re.compile(r"\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{1,2},?\s+\d{4}\b", re.IGNORECASE),  # Jan 15, 2024
    re.compile(r"\b\d{1,2}\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{4}\b", re.IGNORECASE),  # 15 Jan 2024
]


def _extract_normalized_date(date_str: Optional[str]) -> Optional[str]:
    """Attempt to extract and normalize a date substring from raw review date text."""
    if not date_str:
        return None
    raw = date_str.strip()
    for pattern in _DATE_PATTERNS:
        match = pattern.search(raw)
        if match:
            return match.group(0).lower()
    # Fallback: if short string (e.g. '2024-05-10' or '12/10/2024'), return lowercase trimmed
    if len(raw) <= 25 and any(char.isdigit() for char in raw):
        return raw.lower()
    return None


def _is_suspicious_reviewer_name(name: Optional[str]) -> bool:
    """Check if reviewer name is all-numeric or a known generic placeholder."""
    if not name:
        return False
    trimmed = name.strip()
    if not trimmed:
        return False
    if trimmed.isdigit():
        return True
    if trimmed.lower() in _GENERIC_REVIEWER_NAMES:
        return True
    return False


def analyze_review_batch(reviews: list[ScrapedReview]) -> BatchAnalysisResult:
    """Analyze batch of reviews for duplicates, burst temporal clusters, and name anomalies.

    Args:
        reviews: List of ScrapedReview objects for a single product.

    Returns:
        BatchAnalysisResult containing product-level signals and duplicate pair indices.
    """
    if len(reviews) < 2:
        return BatchAnalysisResult(
            product_level_signals=[],
            duplicate_pairs=[],
            reviews_flagged_as_duplicate=0,
        )

    product_level_signals: list[ReviewSignal] = []
    duplicate_pairs: list[tuple[int, int]] = []
    duplicate_indices: set[int] = set()

    # RULE B1 — Duplicate/Near-Duplicate Text Detection
    num_reviews = len(reviews)
    cleaned_texts = [r.review_text.strip().lower() for r in reviews]

    for i in range(num_reviews):
        for j in range(i + 1, num_reviews):
            text_i = cleaned_texts[i]
            text_j = cleaned_texts[j]
            # Fast check: identical strings
            if text_i and text_j and text_i == text_j:
                similarity = 1.0
            elif len(text_i) > 0 and len(text_j) > 0:
                similarity = difflib.SequenceMatcher(None, text_i, text_j).ratio()
            else:
                similarity = 0.0

            if similarity > 0.85:
                duplicate_pairs.append((i, j))
                duplicate_indices.add(i)
                duplicate_indices.add(j)

    # RULE B2 — Burst Pattern Detection
    extracted_dates = []
    for r in reviews:
        norm_date = _extract_normalized_date(r.review_date)
        if norm_date:
            extracted_dates.append(norm_date)

    # Only evaluate burst pattern if dates were successfully extracted for multiple reviews
    if extracted_dates:
        date_counts = Counter(extracted_dates)
        max_same_date_count = max(date_counts.values())
        if (max_same_date_count / num_reviews) > 0.30:
            product_level_signals.append(
                ReviewSignal(
                    rule="review_burst_pattern",
                    severity="medium",
                    message=(
                        "Unusually high concentration of reviews posted in a short time window "
                        "— may indicate a coordinated review campaign"
                    ),
                )
            )

    # RULE B3 — Reviewer Name Pattern
    suspicious_names_count = sum(
        1 for r in reviews if _is_suspicious_reviewer_name(r.reviewer_name)
    )
    if (suspicious_names_count / num_reviews) > 0.20:
        product_level_signals.append(
            ReviewSignal(
                rule="suspicious_reviewer_names",
                severity="low",
                message="A notable portion of reviewers have generic or anonymized names",
            )
        )

    return BatchAnalysisResult(
        product_level_signals=product_level_signals,
        duplicate_pairs=duplicate_pairs,
        reviews_flagged_as_duplicate=len(duplicate_indices),
    )
