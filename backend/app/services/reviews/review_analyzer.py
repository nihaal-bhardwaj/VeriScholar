"""Review authenticity analyzer module.

Applies heuristic and NLP-derived screening rules to evaluate the
suspicion / authenticity level of individual product reviews.
"""

import re
from typing import Optional

from app.schemas.reviews import ReviewSignal, ScrapedReview

# --- Tokenization and regex patterns ----------------------------------

_WORD_RE = re.compile(r"\b[A-Za-z0-9À-ÿ]+(?:['-][A-Za-z0-9À-ÿ]+)*\b")

# Rule 2: Generic superlatives
_SUPERLATIVE_PHRASES = ["love it", "highly recommend", "so good", "best ever"]
_SUPERLATIVE_WORDS = [
    "amazing",
    "excellent",
    "best",
    "perfect",
    "awesome",
    "incredible",
    "outstanding",
    "fantastic",
    "wonderful",
    "greatest",
    "superb",
]
_SUPERLATIVE_PHRASE_RES = [
    re.compile(rf"\b{re.escape(phrase)}\b", re.IGNORECASE) for phrase in _SUPERLATIVE_PHRASES
]
_SUPERLATIVE_WORDS_RE = re.compile(
    rf"\b(?:{'|'.join(re.escape(w) for w in _SUPERLATIVE_WORDS)})\b", re.IGNORECASE
)

# Rule 3 Specificity Detection Patterns:
# 1. Digits and written numbers
_DIGITS_RE = re.compile(r"\d+")
_NUMBER_WORDS_RE = re.compile(
    r"\b(one|two|three|four|five|six|seven|eight|nine|ten|zero|first|second)\b",
    re.IGNORECASE,
)

# 2. Time-duration phrases
_TIME_DURATION_RE = re.compile(
    r"\b(?:\d+|one|two|three|four|five|six|seven|eight|nine|ten|a|an|few|several|couple)?\s*"
    r"(?:second|seconds|sec|secs|minute|minutes|min|mins|hour|hours|hr|hrs|"
    r"day|days|week|weeks|month|months|year|years|daily|weekly|monthly)\b",
    re.IGNORECASE,
)

# 3. Comparative or causal language
_COMPARATIVE_CAUSAL_RE = re.compile(
    r"\b(?:before and after|compared to|used to|now i|since i started|since using|"
    r"after using|prior to|as a result|results?|improvements?|improved|improving|"
    r"worse|worsened|better|changed|differences?|differently|noticeable|"
    r"effective(?:ness)?|helpful|progress|outcomes?)\b",
    re.IGNORECASE,
)

# 4. Named body parts, symptoms, health outcomes, or named use-cases/contexts
_CONTEXT_OR_SYMPTOMS_RE = re.compile(
    r"\b(?:for my|for our|for the|for a|for daily|for personal)\s+\w+\b|"
    r"\b(?:husband|wife|son|daughter|mother|father|mom|dad|family|gym|workout|office|"
    r"travel|skin|hair|face|body|stomach|gut|sleep|energy|pain|cramp|cramps|"
    r"immunity|weight|health|blood|pressure|digestion|headaches?|eyes?|joints?)\b",
    re.IGNORECASE,
)

# Rule 4: Emoji and exclamation
_EMOJI_RE = re.compile(r"[\U00010000-\U0010ffff]|[\u2600-\u27bf]")

# Rule 5: Before / After Narrative and Sentiment Mismatch Patterns
_BEFORE_RE = re.compile(r"\bbefore\b", re.IGNORECASE)
_AFTER_RE = re.compile(r"\bafter\b", re.IGNORECASE)

_TRANSITION_MARKERS_RE = re.compile(
    r"\b(?:since i started|since using|since switching|since taking|since buying|since adding)\b",
    re.IGNORECASE,
)

_EXPLICIT_RESOLUTION_RE = re.compile(
    r"\b(?:not seen|haven't seen|have not seen)\b.{1,50}\bsince\b|"
    r"\b(?:no more\b|no longer\b|gone away|cleared up|improved|resolved|fixed the issue|"
    r"solved (?:my|the) problem|cured)\b",
    re.IGNORECASE,
)

_PAST_PROBLEM_PHRASES_RE = re.compile(
    r"\b(?:used to|was getting|started getting|i had|we had|had been|suffered from|suffering from|"
    r"struggled with|struggling with|looking for (?:an?|something for)|prior to)\b",
    re.IGNORECASE,
)

_SYMPTOM_WORDS = [
    "dandruff",
    "flakes",
    "flake",
    "acne",
    "breakout",
    "breakouts",
    "pimples",
    "pimple",
    "pain",
    "itchy",
    "itching",
    "itch",
    "dryness",
    "dry",
    "cramp",
    "cramps",
    "headache",
    "headaches",
    "hairfall",
    "hair fall",
    "hair loss",
    "rash",
    "rashes",
    "irritation",
    "blemish",
    "blemishes",
    "bloating",
    "nausea",
    "soreness",
    "wrinkles",
    "wrinkle",
    "dark circles",
    "eczema",
    "inflammation",
]
_SYMPTOM_RE = re.compile(
    rf"\b(?:{'|'.join(re.escape(w) for w in _SYMPTOM_WORDS)})\b",
    re.IGNORECASE,
)

_RESOLUTION_MARKERS_RE = re.compile(
    r"\b(?:now\b|since\b|have not\b|haven't\b|has not\b|hasn't\b|no longer\b|not seen\b|"
    r"no more\b|gone away|cleared up|improved|resolved|fixed the issue|solved (?:my|the) problem|"
    r"effective|working well|worked well)\b",
    re.IGNORECASE,
)

_PRODUCT_COMPLAINT_PHRASES = [
    "waste of money",
    "waste of time",
    "returned it",
    "return it",
    "returning it",
    "doesn't work",
    "does not work",
    "didn't work",
    "did not work",
    "stopped working",
    "stops working",
    "stop working",
    "poor quality",
    "poor performance",
    "cheaply made",
    "hate this product",
    "hated this product",
    "hate this",
    "hated this",
    "worst purchase",
    "worst product",
    "don't buy",
    "do not buy",
    "not worth",
    "don't recommend",
    "do not recommend",
    "not recommend",
]

_PRODUCT_COMPLAINT_WORDS = [
    "broken",
    "defective",
    "disappointed",
    "disappointing",
    "disappointment",
    "terrible",
    "horrible",
    "awful",
    "faulty",
    "useless",
    "hated",
    "hate",
    "broke",
    "poor",
    "bad",
]

_COMPLAINT_PHRASE_RES = [
    re.compile(rf"\b{re.escape(phrase)}\b", re.IGNORECASE)
    for phrase in _PRODUCT_COMPLAINT_PHRASES
]
_COMPLAINT_WORDS_RE = re.compile(
    rf"\b(?:{'|'.join(re.escape(w) for w in _PRODUCT_COMPLAINT_WORDS)})\b",
    re.IGNORECASE,
)

_POSITIVE_PHRASES = [
    "works well",
    "works great",
    "works perfectly",
    "highly recommend",
    "no longer an issue",
    "solved my problem",
    "cleared up",
    "fixed the issue",
]

_POSITIVE_WORDS = [
    "good",
    "great",
    "love",
    "loved",
    "excellent",
    "happy",
    "satisfied",
    "effective",
    "recommend",
    "improved",
    "resolved",
    "wonderful",
    "fantastic",
    "perfect",
]

_POS_PHRASE_RES = [
    re.compile(rf"\b{re.escape(phrase)}\b", re.IGNORECASE)
    for phrase in _POSITIVE_PHRASES
]
_POS_WORDS_RE = re.compile(
    rf"\b(?:{'|'.join(re.escape(w) for w in _POSITIVE_WORDS)})\b",
    re.IGNORECASE,
)

_NEGATION_WORDS = {
    "not",
    "no",
    "never",
    "without",
    "haven't",
    "hasn't",
    "hadn't",
    "wasn't",
    "weren't",
    "hardly",
    "barely",
}

_POSITIVE_NEGATION_WORDS = _NEGATION_WORDS | {"don't", "doesn't", "didn't"}

# Rule 8: Product Category Incoherence term groups
_CATEGORY_TERMS = {
    "electronics": [
        "phone", "battery", "screen", "charging", "camera",
        "signal", "wifi", "bluetooth", "app", "display",
    ],
    "haircare": [
        "scalp", "hair", "shampoo", "conditioner",
        "dandruff", "hairfall", "frizz", "moisturize",
    ],
    "health/body": [
        "heart", "blood pressure", "immunity",
        "digestion", "weight", "calories", "muscle",
    ],
    "food/taste": [
        "taste", "flavor", "smell", "aroma",
        "delicious", "bitter", "sweet", "sour",
    ],
    "clothing": [
        "fit", "size", "fabric", "stitching",
        "color faded", "shrunk", "material",
    ],
}


def _make_category_pattern(term: str) -> re.Pattern:
    if " " in term:
        return re.compile(rf"\b{re.escape(term)}\b", re.IGNORECASE)
    if term == "fit":
        return re.compile(r"\bfits?\b", re.IGNORECASE)
    if term == "battery":
        return re.compile(r"\bbatter(?:y|ies)\b", re.IGNORECASE)
    if term == "hair":
        return re.compile(r"\bhair\b", re.IGNORECASE)
    if term.endswith("e"):
        stem = term[:-1]
        return re.compile(rf"\b{re.escape(stem)}(?:e|es|ed|ing)?\b", re.IGNORECASE)
    if term.endswith("y"):
        stem = term[:-1]
        return re.compile(rf"\b{re.escape(stem)}(?:y|ies)?\b", re.IGNORECASE)
    return re.compile(rf"\b{re.escape(term)}(?:s|es|ed|ing)?\b", re.IGNORECASE)


_CATEGORY_PATTERNS = {
    category: [_make_category_pattern(term) for term in terms]
    for category, terms in _CATEGORY_TERMS.items()
}

# Severity weights for authenticity / suspicion scoring
_SEVERITY_WEIGHTS = {
    "high": 15.0,
    "medium": 8.0,
    "low": 3.0,
}


def _count_words(text: str) -> int:
    """Return word count of text."""
    if not text:
        return 0
    words = _WORD_RE.findall(text)
    return len(words) if words else len(text.split())


def _compute_superlative_density(text: str, word_count: int) -> float:
    """Calculate the count of generic superlatives per 100 words."""
    if word_count <= 0 or not text:
        return 0.0

    phrase_matches = sum(len(res.findall(text)) for res in _SUPERLATIVE_PHRASE_RES)
    word_matches = len(_SUPERLATIVE_WORDS_RE.findall(text))
    total_superlatives = phrase_matches + word_matches
    return (total_superlatives / word_count) * 100.0


def _is_before_after_narrative(text: str) -> bool:
    """Detect before/after and problem-solved narrative structures."""
    if not text:
        return False

    # 1. 'before' + 'after' both present
    if _BEFORE_RE.search(text) and _AFTER_RE.search(text):
        return True

    # 2. Transition phrases like 'since I started', 'since using', 'since switching'
    if _TRANSITION_MARKERS_RE.search(text):
        return True

    # 3. Explicit resolution phrases (e.g. 'not seen ... since', 'cleared up', 'no more', etc.)
    if _EXPLICIT_RESOLUTION_RE.search(text):
        return True

    # 4. Temporal contrast: problem description or symptom followed by resolution marker
    problem_matches = list(_PAST_PROBLEM_PHRASES_RE.finditer(text)) + list(_SYMPTOM_RE.finditer(text))
    if problem_matches:
        earliest_problem_pos = min(m.start() for m in problem_matches)
        res_matches = list(_RESOLUTION_MARKERS_RE.finditer(text))
        if any(m.start() > earliest_problem_pos for m in res_matches):
            return True

    return False


def _is_complaint_negated(text: str, start: int, end: int) -> bool:
    """Check if a complaint match at (start, end) is negated or resolved nearby."""
    preceding_text = text[:start]
    preceding_tokens = _WORD_RE.findall(preceding_text)
    preceding_window = [w.lower() for w in preceding_tokens[-5:]]
    if any(w in _NEGATION_WORDS for w in preceding_window):
        return True

    following_text = text[end:]
    following_tokens = _WORD_RE.findall(following_text)
    following_window = [w.lower() for w in following_tokens[:3]]
    if "since" in following_window:
        return True

    return False


def _count_product_complaints(text: str) -> int:
    """Count genuine, un-negated product complaint phrases and words."""
    matched_spans: list[tuple[int, int]] = []
    count = 0

    # 1. Multi-word phrases
    for res in _COMPLAINT_PHRASE_RES:
        for match in res.finditer(text):
            span = match.span()
            matched_spans.append(span)
            if not _is_complaint_negated(text, span[0], span[1]):
                count += 1

    # 2. Single words (ignoring overlaps with matched phrases)
    for match in _COMPLAINT_WORDS_RE.finditer(text):
        span = match.span()
        if any(s[0] <= span[0] and span[1] <= s[1] for s in matched_spans):
            continue
        if not _is_complaint_negated(text, span[0], span[1]):
            count += 1

    return count


def _count_positive_sentiment(text: str) -> int:
    """Count un-negated positive phrases and words."""
    matched_spans: list[tuple[int, int]] = []
    count = 0

    for res in _POS_PHRASE_RES:
        for match in res.finditer(text):
            span = match.span()
            matched_spans.append(span)
            preceding_tokens = _WORD_RE.findall(text[: span[0]])
            if not any(w.lower() in _POSITIVE_NEGATION_WORDS for w in preceding_tokens[-3:]):
                count += 1

    for match in _POS_WORDS_RE.finditer(text):
        span = match.span()
        if any(s[0] <= span[0] and span[1] <= s[1] for s in matched_spans):
            continue
        preceding_tokens = _WORD_RE.findall(text[: span[0]])
        if not any(w.lower() in _POSITIVE_NEGATION_WORDS for w in preceding_tokens[-3:]):
            count += 1

    return count


def analyze_review(review: ScrapedReview) -> list[ReviewSignal]:
    """Analyze a single review and produce a list of triggered ReviewSignals.

    Returns:
        List of ReviewSignal objects triggered by the review text and metadata.
    """
    signals: list[ReviewSignal] = []
    text = review.review_text or ""
    word_count = _count_words(text)

    # RULE 1 — Extreme Length Anomaly
    if word_count < 5:
        signals.append(
            ReviewSignal(
                rule="too_short",
                severity="low",
                message="Review is extremely short, may lack genuine detail",
            )
        )
    elif word_count > 500:
        signals.append(
            ReviewSignal(
                rule="unusually_long",
                severity="low",
                message="Review is unusually long for a product review, may be template-stuffed content",
            )
        )

    # RULE 2 — Generic Superlative Density
    superlative_density = _compute_superlative_density(text, word_count)
    if superlative_density > 8.0:
        signals.append(
            ReviewSignal(
                rule="superlative_stuffing",
                severity="medium",
                message="Unusually high density of generic superlatives, common in fake or incentivized reviews",
            )
        )

    # RULE 3 — Lack of Specific Detail (Revamped)
    # Only flag as lacking detail if:
    # 1. Word count > 15
    # 2. Contains ZERO digits/numbers anywhere
    # 3. Contains ZERO time-duration phrases
    # 4. Contains ZERO comparative/causal phrases
    # 5. Contains ZERO named context, symptoms, or body parts
    # 6. High superlative density (> 8.0) — predominantly generic fluff
    has_numbers = bool(_DIGITS_RE.search(text) or _NUMBER_WORDS_RE.search(text))
    has_time_duration = bool(_TIME_DURATION_RE.search(text))
    has_comparative_causal = bool(_COMPARATIVE_CAUSAL_RE.search(text))
    has_context_or_symptoms = bool(_CONTEXT_OR_SYMPTOMS_RE.search(text))

    if (
        word_count > 15
        and not has_numbers
        and not has_time_duration
        and not has_comparative_causal
        and not has_context_or_symptoms
        and superlative_density > 8.0
    ):
        signals.append(
            ReviewSignal(
                rule="generic_no_detail",
                severity="medium",
                message=(
                    "Review reads as generic praise or complaint without concrete details "
                    "(numbers, timeframes, or specific outcomes) — worth a second look"
                ),
            )
        )

    # RULE 4 — Excessive Exclamation/Emoji Density
    exclamation_count = text.count("!")
    emoji_count = len(_EMOJI_RE.findall(text))
    total_punct = exclamation_count + emoji_count
    if word_count > 0 and (total_punct / word_count) > (1.0 / 20.0):
        signals.append(
            ReviewSignal(
                rule="excessive_punctuation",
                severity="low",
                message="Excessive exclamation marks, a pattern seen in incentivized reviews",
            )
        )

    # RULE 5 — Rating-Sentiment Mismatch
    if review.rating is not None:
        # Step 1: Check for before/after narrative pattern -> skip if detected
        if not _is_before_after_narrative(text):
            # Step 2: Negation-aware complaint and positive counts
            complaint_count = _count_product_complaints(text)
            positive_count = _count_positive_sentiment(text)
            symptom_count = len(_SYMPTOM_RE.findall(text))

            # Step 3: Flag mismatch conditions
            if review.rating == 5 and complaint_count > positive_count:
                signals.append(
                    ReviewSignal(
                        rule="rating_sentiment_mismatch",
                        severity="high",
                        message=(
                            "5-star rating but review describes specific problems with the product "
                            "itself (not just a symptom it was meant to treat)"
                        ),
                    )
                )
            elif review.rating in (1, 2) and positive_count > complaint_count and symptom_count == 0:
                signals.append(
                    ReviewSignal(
                        rule="rating_sentiment_mismatch",
                        severity="high",
                        message="Low rating but review text contains predominantly positive language",
                    )
                )

    # RULE 6 — Duplicate/Template Phrase Detection (Handled at batch level)

    # RULE 7 — Unverified Purchase + High Praise
    if review.verified_purchase is False and superlative_density > 8.0:
        signals.append(
            ReviewSignal(
                rule="unverified_high_praise",
                severity="medium",
                message="Review is not from a verified purchase and contains unusually enthusiastic language",
            )
        )

    # RULE 8 — Product Category Incoherence
    matched_categories = []
    text_lower = text.lower()
    for cat_name, patterns in _CATEGORY_PATTERNS.items():
        if any(pat.search(text_lower) for pat in patterns):
            matched_categories.append(cat_name)

    if len(matched_categories) >= 3:
        signals.append(
            ReviewSignal(
                rule="product_category_incoherence",
                severity="high",
                message=(
                    "Review mentions features from multiple unrelated product categories — "
                    "a strong indicator of bot-generated or nonsense content"
                ),
            )
        )

    return signals


def calculate_review_authenticity_score(signals: list[ReviewSignal]) -> float:
    """Calculate authenticity / suspicion score for an individual review.

    Weights: high=15, medium=8, low=3. Capped at 100.0.
    Higher score indicates higher suspicion of inauthenticity.
    """
    total = sum(_SEVERITY_WEIGHTS.get(sig.severity.lower(), 0.0) for sig in signals)
    return min(100.0, float(total))
