"""Rule-based NLP feature extraction for research paper text.

Computes explainable writing-quality and style features from raw paper
text. This is a heuristic approach — no training data and no ML models —
so every feature is interpretable by a human reviewer. Features are
screening signals that surface suspicious patterns (uniform AI-like
style, style shifts, unrelated abstract/body, low citation density),
never proof of fraud.

Dependencies: nltk (tokenization) and textstat (readability). NLTK
data is downloaded lazily at import; if the download fails (offline),
tokenization falls back to deterministic regex tokenizers so the module
still works.
"""

import math
import re
import statistics
from typing import Any

import nltk
import textstat

from app.schemas.ml import TextFeatures

# --- NLTK data bootstrap (offline-safe) --------------------------------

for _resource in ("punkt", "punkt_tab", "averaged_perceptron_tagger"):
    try:
        nltk.download(_resource, quiet=True)
    except Exception:
        pass

# --- Tokenization helpers ----------------------------------------------

_WORD_RE = re.compile(r"[A-Za-zÀ-ÿ]+(?:['-][A-Za-zÀ-ÿ]+)*")
_SENTENCE_SPLIT_RE = re.compile(r"(?<=[.!?])\s+")

# GROUP 5 — academic writing signals

_CITATION_RE = re.compile(r"\[[0-9][0-9\s,\-]*\]")

_HEDGE_WORDS = [
    "may",
    "might",
    "could",
    "possibly",
    "probably",
    "suggests",
    "appears",
    "seems",
    "approximately",
    "generally",
]
_HEDGE_RES = [re.compile(rf"\b{re.escape(word)}\b", re.IGNORECASE) for word in _HEDGE_WORDS]

_PASSIVE_IRREGULAR_PARTICIPLES = (
    "taken|given|shown|made|found|done|known|written|built|held|kept|seen|said|"
    "bought|brought|thought|taught|sent|chosen|begun|broken|spoken|eaten|hidden|"
    "driven|grown|thrown|fallen|forgotten|risen|run|sung|blown|paid|meant|felt|"
    "left|lost|met|put|set|told|sold|cost|cut|hit|hurt|let|read|shut|spent|"
    "understood|won"
)
_PASSIVE_RE = re.compile(
    rf"\b(?:was|were|been|being|is|are)\s+"
    rf"(?:\w+ed\b|{_PASSIVE_IRREGULAR_PARTICIPLES})\b",
    re.IGNORECASE,
)

_N_CHUNKS = 4


def _words(text: str) -> list[str]:
    """Return word tokens for the given text.

    Prefers NLTK's tokenizer but falls back to a regex so the module
    keeps working offline or without NLTK data. Only alphabetic words
    (with apostrophes/hyphens) count — numbers, URLs and punctuation do not.
    """
    if not text:
        return []
    try:
        tokens = nltk.word_tokenize(text)
        words = [token for token in tokens if _WORD_RE.fullmatch(token)]
    except Exception:
        words = _WORD_RE.findall(text)
    return words


def _sentences(text: str) -> list[str]:
    """Return non-empty sentences for the given text."""
    if not text.strip():
        return []
    try:
        sentences = [s.strip() for s in nltk.sent_tokenize(text) if s.strip()]
    except Exception:
        sentences = [s.strip() for s in _SENTENCE_SPLIT_RE.split(text) if s.strip()]
    return sentences


def _avg_sentence_length(text: str) -> float:
    """Average number of words per sentence, or 0.0 for no sentences."""
    sentences = _sentences(text)
    if not sentences:
        return 0.0
    return sum(len(_words(sentence)) for sentence in sentences) / len(sentences)


def _safe_textstat(score_fn: Any, text: str) -> float:
    """Run a textstat scoring function, returning 0.0 on any failure."""
    try:
        return round(float(score_fn(text or "")), 4)
    except Exception:
        return 0.0


def _paragraph_count(pages: list[dict], text: str) -> int:
    """Count paragraphs as blank-line separated text blocks.

    Prefers the page texts from extraction (same shape as `pdf_parser`
    output); falls back to `full_text` when no pages are provided.
    """
    page_texts = [
        page.get("text", "") for page in pages if isinstance(page, dict) and page.get("text")
    ]
    combined = "\n".join(page_texts) if page_texts else text or ""
    if not combined.strip():
        return 0
    blocks = re.split(r"\n\s*\n+", combined)
    return sum(1 for block in blocks if block.strip())


def _chunk_sentences(sentences: list[str], n_chunks: int = _N_CHUNKS) -> list[list[str]]:
    """Split sentences into roughly equal consecutive chunks."""
    if not sentences:
        return []
    n = min(n_chunks, len(sentences))
    base, extra = divmod(len(sentences), n)
    chunks: list[list[str]] = []
    index = 0
    for chunk_index in range(n):
        take = base + (1 if chunk_index < extra else 0)
        chunks.append(sentences[index : index + take])
        index += take
    return chunks


def _hedge_occurrences(text: str) -> int:
    """Count total hedge word occurrences (case-insensitive)."""
    return sum(len(pattern.findall(text)) for pattern in _HEDGE_RES)


def extract_features(full_text: str, abstract: str, pages: list[dict]) -> TextFeatures:
    """Compute numerical writing-quality features for a research paper.

    Args:
        full_text: Combined extracted text of the paper (pdf_parser output).
        abstract: The paper's abstract text (may be empty).
        pages: Page-wise text from pdf_parser — a list of dicts with
            ``page_number`` and ``text`` keys.

    Empty or whitespace-only inputs yield a ``TextFeatures`` object with
    all fields at zero rather than raising. Any feature that cannot be
    computed (division by zero, no sentences, missing data) is 0.0.
    """
    text = full_text or ""
    abstract = abstract or ""

    words = _words(text)
    sentences = _sentences(text)
    total_words = len(words)
    total_sentences = len(sentences)

    # GROUP 1 — readability
    flesch_reading_ease = _safe_textstat(textstat.flesch_reading_ease, text)
    flesch_kincaid_grade = _safe_textstat(textstat.flesch_kincaid_grade, text)
    gunning_fog_index = _safe_textstat(textstat.gunning_fog, text)
    automated_readability_index = _safe_textstat(textstat.automated_readability_index, text)

    # GROUP 2 — vocabulary
    unique_word_ratio = len({word.lower() for word in words}) / total_words if total_words else 0.0
    avg_word_length = sum(len(word) for word in words) / total_words if total_words else 0.0
    rare_word_ratio = (
        sum(1 for word in words if len(word) > 10) / total_words if total_words else 0.0
    )

    # GROUP 3 — sentence structure
    sentence_lengths = [len(_words(sentence)) for sentence in sentences]
    avg_sentence_length = (
        sum(sentence_lengths) / total_sentences if total_sentences else 0.0
    )
    sentence_length_variance = (
        statistics.pvariance(sentence_lengths) if total_sentences >= 2 else 0.0
    )
    total_paragraphs = _paragraph_count(pages, text)

    # GROUP 4 — section consistency
    abstract_words = {word.lower() for word in _words(abstract)}
    body_words = {word.lower() for word in words}
    if abstract_words and body_words:
        abstract_to_body_similarity = round(
            len(abstract_words & body_words) / min(len(abstract_words), len(body_words)), 4
        )
    else:
        abstract_to_body_similarity = None

    chunk_lengths = [
        _avg_sentence_length(" ".join(chunk))
        for chunk in _chunk_sentences(sentences)
        if chunk
    ]
    section_style_variance = (
        statistics.pvariance(chunk_lengths) if len(chunk_lengths) >= 2 else 0.0
    )

    # GROUP 5 — academic writing
    citation_density = (
        len(_CITATION_RE.findall(text)) / total_words * 1000 if total_words else 0.0
    )
    passive_sentence_count = sum(1 for sentence in sentences if _PASSIVE_RE.search(sentence))
    passive_voice_ratio = (
        passive_sentence_count / total_sentences if total_sentences else 0.0
    )
    hedge_word_ratio = _hedge_occurrences(text) / total_words if total_words else 0.0

    return TextFeatures(
        flesch_reading_ease=flesch_reading_ease,
        flesch_kincaid_grade=flesch_kincaid_grade,
        gunning_fog_index=gunning_fog_index,
        automated_readability_index=automated_readability_index,
        unique_word_ratio=round(unique_word_ratio, 4),
        avg_word_length=round(avg_word_length, 4),
        rare_word_ratio=round(rare_word_ratio, 4),
        avg_sentence_length=round(avg_sentence_length, 4),
        sentence_length_variance=round(sentence_length_variance, 4),
        total_sentences=total_sentences,
        total_words=total_words,
        total_paragraphs=total_paragraphs,
        abstract_to_body_similarity=abstract_to_body_similarity,
        section_style_variance=round(section_style_variance, 4),
        citation_density=round(citation_density, 4),
        passive_voice_ratio=round(passive_voice_ratio, 4),
        hedge_word_ratio=round(hedge_word_ratio, 4),
    )