"""LLM-powered review authenticity analyzer service using Groq API."""

import json
import logging
import os
import re
import time
from typing import Optional

import httpx
import groq
from groq import Groq

from app.core.config import get_settings
from app.schemas.reviews import LLMReviewAnalysis, LLMSignal, ScrapedReview

logger = logging.getLogger(__name__)

DEFAULT_GEMINI_MODEL = "gemini-3.1-flash-lite"
MIN_ALLOWED_GEMINI_VERSION = 3.1
MODEL_NAME = "qwen/qwen3.8-27b"
REQUEST_TIMEOUT = 10.0
MAX_REVIEW_LENGTH = 1500

SYSTEM_PROMPT = """You are an expert at detecting fake, incentivized, or
manipulated product reviews. You have deep knowledge of the
patterns that distinguish genuine customer experiences from
fake reviews posted by bots, paid reviewers, or incentivized
customers.

You analyze one review at a time and return ONLY a valid JSON
object — no explanation, no preamble, no markdown, no code
blocks. Just the raw JSON."""


def _build_user_prompt(
    review: ScrapedReview,
    product_title: Optional[str] = None,
) -> str:
    """Construct the primary user prompt for the Groq model."""
    raw_text = review.review_text or ""
    truncated_text = raw_text[:MAX_REVIEW_LENGTH]

    prod = product_title.strip() if product_title and product_title.strip() else "Unknown product"
    rev = review.reviewer_name.strip() if review.reviewer_name and review.reviewer_name.strip() else "Anonymous"
    rat = f"{review.rating}/5 stars" if review.rating is not None else "Not provided"

    if review.verified_purchase is True:
        vp = "Yes"
    elif review.verified_purchase is False:
        vp = "No"
    else:
        vp = "Unknown"

    return f"""Analyze this product review for authenticity.

Product: {prod}
Reviewer: {rev}
Rating: {rat}
Verified Purchase: {vp}

Review text:
\"{truncated_text}\"

Evaluate this review on the following dimensions and return
ONLY this JSON structure with no other text:

{{
  "authenticity_score": <integer 0-100, where 0=certainly fake
    and 100=certainly genuine>,
  "classification": <"likely_genuine", "uncertain", or
    "likely_fake">,
  "confidence": <"high", "medium", or "low" — how confident
    you are in this classification>,
  "reasoning": <one sentence explaining the most important
    signal that drove your score>,
  "signals": [
    {{
      "type": <short signal name, e.g. "before_after_narrative",
        "vague_generic_praise", "rating_text_mismatch",
        "specific_detail_present", "incentivized_language",
        "template_phrasing", "genuine_complaint", etc.>,
      "is_suspicious": <true if this signal suggests fake,
        false if it supports genuineness>,
      "description": <one sentence describing what you found>
    }}
  ],
  "llm_available": true
}}

Guidelines for scoring:
- A score of 80-100 means the review reads as genuinely written
  by a real customer with a real experience
- A score of 50-79 means the review has some suspicious
  elements but could be genuine
- A score of 20-49 means the review has multiple red flags
  and is likely fake or incentivized
- A score of 0-19 means the review is almost certainly fake,
  bot-generated, or heavily templated
- A score of 0-10 should be given to reviews that are
  clearly nonsensical, incoherent, or contain impossible
  product claims. Do not hesitate to score near 0 for
  obvious bot-generated or nonsense content.

Key things to look for:
- GENUINE signals: specific product details, before/after
  narratives, mentions of personal context (who they bought
  it for, their specific use case), balanced feedback (mentions
  both positives and minor negatives), natural language,
  time-specific usage details
- FAKE signals: generic superlative praise with no specifics,
  exact same phrasing as other reviews, suspiciously perfect
  5-star language with zero nuance, very short content-free
  reviews, incentivized language ("I received this for free",
  "in exchange for my honest review"), unnatural keyword
  stuffing, rating that contradicts the text content
- INCOHERENCE: Review mentions product features or outcomes
  that are physically impossible, medically implausible, or
  completely unrelated to the product category (e.g. a phone
  review mentioning scalp health, a shampoo review mentioning
  battery life). This is a STRONG fake signal.
- CATEGORY CONFUSION: The reviewer describes benefits or
  features that belong to a completely different product type
  than what is being reviewed. Real customers describe what
  the actual product does.
- MIXED SIGNAL INCOHERENCE: Review uses positive language
  ('best', 'amazing', 'love it') but gives a 1 or 2 star
  rating, OR uses negative language but gives 5 stars, with
  no coherent explanation for the contradiction. This is
  different from a nuanced mixed review — look for reviews
  where the text and rating are completely at odds with zero
  logical explanation.
- IMPLAUSIBLE CAUSAL CHAINS: Review claims a product caused
  an implausible sequence of effects (e.g. 'phone dried my
  scalp which improved my heart health'). Real reviews
  describe direct, plausible product experiences.
- NONSENSE TEXT: Review text is grammatically bizarre,
  logically incoherent, or reads like it was randomly
  assembled. Real customer reviews, even poorly written
  ones, follow basic logical structure about their experience.
- CONTEXT: Consider the product type. For health/wellness
  products, mentioning a symptom or problem (dandruff, acne,
  pain) that the product helped with is a GENUINE signal, not
  a negative one. Do not penalize before/after narratives."""



def _build_fallback_prompt(review: ScrapedReview) -> str:
    """Construct a simplified fallback prompt for JSON repair."""
    raw_text = review.review_text or ""
    truncated_text = raw_text[:MAX_REVIEW_LENGTH]
    rat = f"{review.rating}/5 stars" if review.rating is not None else "Not provided"

    return f"""You are a review authenticity detector. Reply with ONLY valid
JSON, nothing else.

Review: \"{truncated_text}\"
Rating: {rat}

Return exactly this JSON:
{{"authenticity_score": <0-100>, "classification":
"likely_genuine" or "uncertain" or "likely_fake",
"confidence": "high" or "medium" or "low",
"reasoning": "<one sentence>", "signals": [],
"llm_available": true}}"""


def _extract_and_parse_json(content: str) -> Optional[dict]:
    """Safely parse JSON response from LLM output, stripping markdown formatting if present."""
    if not content:
        return None
    cleaned = content.strip()

    # Strip markdown backticks if present
    if cleaned.startswith("```json"):
        cleaned = cleaned[7:]
    elif cleaned.startswith("```"):
        cleaned = cleaned[3:]
    if cleaned.endswith("```"):
        cleaned = cleaned[:-3]
    cleaned = cleaned.strip()

    try:
        data = json.loads(cleaned)
        if isinstance(data, dict):
            return data
    except Exception:
        # Regex fallback to find outermost JSON object
        match = re.search(r"\{.*\}", cleaned, re.DOTALL)
        if match:
            try:
                data = json.loads(match.group(0))
                if isinstance(data, dict):
                    return data
            except Exception:
                pass
    return None


def _validate_gemini_model(model_name: str) -> str:
    """Ensure only Gemini 3 models or higher are used (strictly rejecting models below 3.1)."""
    if not isinstance(model_name, str) or not model_name.strip():
        return DEFAULT_GEMINI_MODEL
    clean_model = model_name.replace("models/", "").strip()
    version_match = re.search(r"gemini-(\d+(?:\.\d+)?)", clean_model, re.IGNORECASE)
    if not version_match:
        logger.warning(
            "Configured model '%s' is not a recognized Gemini model. Enforcing %s.",
            clean_model,
            DEFAULT_GEMINI_MODEL,
        )
        return DEFAULT_GEMINI_MODEL

    try:
        ver = float(version_match.group(1))
        if ver < MIN_ALLOWED_GEMINI_VERSION:
            logger.warning(
                "Configured Gemini model '%s' (version %.1f) is below minimum allowed version %.1f. Enforcing %s.",
                clean_model,
                ver,
                MIN_ALLOWED_GEMINI_VERSION,
                DEFAULT_GEMINI_MODEL,
            )
            return DEFAULT_GEMINI_MODEL
    except ValueError:
        return DEFAULT_GEMINI_MODEL

    return clean_model


def _call_gemini_completion(
    api_key: str,
    model: str,
    system_content: str,
    user_content: str,
) -> str:
    """Invoke Google Gemini generateContent API (version >= 3.1) with strict timeout."""
    validated_model = _validate_gemini_model(model)
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{validated_model}:generateContent?key={api_key}"

    payload = {
        "system_instruction": {
            "parts": [{"text": system_content}]
        },
        "contents": [
            {
                "role": "user",
                "parts": [{"text": user_content}]
            }
        ],
        "generationConfig": {
            "response_mime_type": "application/json",
            "temperature": 0.1,
        },
    }

    with httpx.Client(timeout=REQUEST_TIMEOUT) as client:
        resp = client.post(url, json=payload)

    if resp.status_code == 200:
        data = resp.json()
        candidates = data.get("candidates", [])
        if candidates:
            parts = candidates[0].get("content", {}).get("parts", [])
            if parts:
                return parts[0].get("text", "")
        return ""
    elif resp.status_code == 404:
        raise RuntimeError(f"Gemini model `{validated_model}` not found (HTTP 404): {resp.text}")
    else:
        raise RuntimeError(f"Gemini API error (HTTP {resp.status_code}): {resp.text}")


def _call_groq_completion(
    client: Groq,
    system_content: str,
    user_content: str,
    model: str = MODEL_NAME,
) -> str:
    """Invoke Groq chat completion API with strict timeout."""
    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": system_content},
            {"role": "user", "content": user_content},
        ],
        temperature=0.1,
        timeout=REQUEST_TIMEOUT,
    )
    if response and response.choices and len(response.choices) > 0:
        return response.choices[0].message.content or ""
    return ""


def _parse_analysis_dict(parsed_data: dict) -> LLMReviewAnalysis:
    """Convert raw dictionary from LLM into a validated LLMReviewAnalysis model."""
    raw_score = parsed_data.get("authenticity_score", 50)
    try:
        score = int(raw_score)
        score = max(0, min(100, score))
    except (ValueError, TypeError):
        score = 50

    classification = str(parsed_data.get("classification", "uncertain")).strip().lower()
    if classification not in ("likely_genuine", "uncertain", "likely_fake"):
        if score >= 80:
            classification = "likely_genuine"
        elif score <= 49:
            classification = "likely_fake"
        else:
            classification = "uncertain"

    confidence = str(parsed_data.get("confidence", "low")).strip().lower()
    if confidence not in ("high", "medium", "low"):
        confidence = "medium"

    reasoning = str(parsed_data.get("reasoning", "")).strip()

    raw_signals = parsed_data.get("signals", [])
    signals: list[LLMSignal] = []
    if isinstance(raw_signals, list):
        for sig in raw_signals:
            if isinstance(sig, dict):
                signals.append(
                    LLMSignal(
                        type=str(sig.get("type", "llm_signal")),
                        is_suspicious=bool(sig.get("is_suspicious", False)),
                        description=str(sig.get("description", "")),
                    )
                )

    return LLMReviewAnalysis(
        authenticity_score=score,
        classification=classification,
        confidence=confidence,
        reasoning=reasoning,
        signals=signals,
        llm_available=True,
        fallback_reason=None,
    )


def analyze_review_with_llm(
    review: ScrapedReview,
    product_title: Optional[str] = None,
    index: Optional[int] = None,
) -> LLMReviewAnalysis:
    """Analyze a single review for authenticity using Gemini 3.1+ (or Groq fallback).

    Args:
        review: ScrapedReview object containing text and metadata.
        product_title: Optional product title for context.
        index: Optional review index for logging.

    Returns:
        LLMReviewAnalysis object with structured evaluation.
    """
    settings = get_settings()
    raw_gemini_key = getattr(settings, "gemini_api_key", "")
    if not isinstance(raw_gemini_key, str):
        raw_gemini_key = ""
    gemini_key = (raw_gemini_key or os.environ.get("GEMINI_API_KEY", "")).strip()

    raw_groq_key = getattr(settings, "groq_api_key", "")
    if not isinstance(raw_groq_key, str):
        raw_groq_key = ""
    groq_key = (raw_groq_key or os.environ.get("GROQ_API_KEY", "")).strip()

    use_gemini = bool(gemini_key and gemini_key != "your_gemini_api_key_here")
    use_groq = bool(not use_gemini and groq_key and groq_key != "your_groq_api_key_here")

    if not use_gemini and not use_groq:
        return LLMReviewAnalysis(
            authenticity_score=50,
            classification="uncertain",
            confidence="low",
            reasoning="",
            signals=[],
            llm_available=False,
            fallback_reason="not_configured",
        )

    idx_str = str(index) if index is not None else "0"
    provider = "gemini" if use_gemini else "groq"
    logger.info("LLM analysis called for review %s (provider=%s)", idx_str, provider)

    user_prompt = _build_user_prompt(review, product_title)

    def _execute_call(prompt: str) -> str:
        if use_gemini:
            raw_model = getattr(settings, "gemini_model", DEFAULT_GEMINI_MODEL)
            if not isinstance(raw_model, str):
                raw_model = DEFAULT_GEMINI_MODEL
            model = _validate_gemini_model(raw_model)
            return _call_gemini_completion(gemini_key, model, SYSTEM_PROMPT, prompt)
        else:
            client = Groq(api_key=groq_key, timeout=REQUEST_TIMEOUT)
            raw_groq_model = getattr(settings, "groq_model", MODEL_NAME)
            groq_model = raw_groq_model if isinstance(raw_groq_model, str) else MODEL_NAME
            return _call_groq_completion(client, SYSTEM_PROMPT, prompt, model=groq_model)

    # First attempt with full prompt
    try:
        raw_output = _execute_call(user_prompt)
    except (groq.APITimeoutError, TimeoutError, httpx.TimeoutException):
        return LLMReviewAnalysis(
            authenticity_score=50,
            classification="uncertain",
            confidence="low",
            reasoning="",
            signals=[],
            llm_available=False,
            fallback_reason="timeout",
        )
    except Exception as exc:
        exc_name = type(exc).__name__.lower()
        exc_str = str(exc).lower()
        if "timeout" in exc_name or "timeout" in exc_str:
            return LLMReviewAnalysis(
                authenticity_score=50,
                classification="uncertain",
                confidence="low",
                reasoning="",
                signals=[],
                llm_available=False,
                fallback_reason="timeout",
            )
        return LLMReviewAnalysis(
            authenticity_score=50,
            classification="uncertain",
            confidence="low",
            reasoning="",
            signals=[],
            llm_available=False,
            fallback_reason="api_error",
        )

    parsed_data = _extract_and_parse_json(raw_output)

    # If first attempt fails JSON parsing, retry once with fallback prompt
    if parsed_data is None:
        fallback_prompt = _build_fallback_prompt(review)
        try:
            raw_fallback = _execute_call(fallback_prompt)
            parsed_data = _extract_and_parse_json(raw_fallback)
        except (groq.APITimeoutError, TimeoutError, httpx.TimeoutException):
            return LLMReviewAnalysis(
                authenticity_score=50,
                classification="uncertain",
                confidence="low",
                reasoning="",
                signals=[],
                llm_available=False,
                fallback_reason="timeout",
            )
        except Exception as exc:
            exc_name = type(exc).__name__.lower()
            exc_str = str(exc).lower()
            if "timeout" in exc_name or "timeout" in exc_str:
                return LLMReviewAnalysis(
                    authenticity_score=50,
                    classification="uncertain",
                    confidence="low",
                    reasoning="",
                    signals=[],
                    llm_available=False,
                    fallback_reason="timeout",
                )
            return LLMReviewAnalysis(
                authenticity_score=50,
                classification="uncertain",
                confidence="low",
                reasoning="",
                signals=[],
                llm_available=False,
                fallback_reason="api_error",
            )

    if parsed_data is None:
        return LLMReviewAnalysis(
            authenticity_score=50,
            classification="uncertain",
            confidence="low",
            reasoning="",
            signals=[],
            llm_available=False,
            fallback_reason="parse_error",
        )

    result = _parse_analysis_dict(parsed_data)
    logger.info("LLM analysis result: %s with %s confidence", result.classification, result.confidence)
    return result


def analyze_reviews_batch_with_llm(
    reviews: list[ScrapedReview],
    product_title: Optional[str] = None,
) -> list[LLMReviewAnalysis]:
    """Call analyze_review_with_llm for each review with a 0.2s inter-call delay."""
    results: list[LLMReviewAnalysis] = []
    for idx, review in enumerate(reviews):
        if idx > 0:
            time.sleep(0.2)
        analysis = analyze_review_with_llm(review, product_title=product_title, index=idx)
        results.append(analysis)
    return results
