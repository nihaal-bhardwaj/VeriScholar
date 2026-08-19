"""Tests for the rule-based ML feature extractor.

All tests are purely local — no network calls and no files are read.
"""

from app.schemas.ml import TextFeatures
from app.services.ml.feature_extractor import extract_features


def _pages(text: str) -> list[dict]:
    return [{"page_number": 1, "text": text}]


def _features(full_text: str, abstract: str = "", pages: list[dict] | None = None) -> TextFeatures:
    return extract_features(full_text, abstract, pages or _pages(full_text))


# Normal text


def test_normal_academic_text_returns_all_fields_populated():
    text = (
        "The results are consistent with prior work. Our method was evaluated "
        "on a benchmark dataset [1]. The findings may suggest a relationship, "
        "which could possibly be explained by the framework described in [2] "
        "and [3]. These observations were measured carefully and are reported "
        "in Table 1. The approach appears robust."
    )
    features = _features(text, abstract="The results are consistent with prior work.")

    for value in features.model_dump().values():
        assert value is not None

    assert isinstance(features, TextFeatures)
    assert features.total_words > 0
    assert features.total_sentences > 0


# Empty and degenerate inputs


def test_empty_text_returns_all_zeros():
    features = _features("", "")

    dumped = features.model_dump()
    for value in dumped.values():
        assert value == 0


def test_whitespace_only_text_returns_all_zeros():
    features = _features("   \n  \n  ", "   ")

    for value in features.model_dump().values():
        assert value == 0


def test_sentence_length_variance_zero_for_single_sentence():
    features = _features("Only one sentence lives here.")

    assert features.total_sentences == 1
    assert features.sentence_length_variance == 0.0


# Vocabulary


def test_unique_word_ratio_is_always_between_zero_and_one():
    texts = [
        "The cat sat on the mat.",
        "a a a a a a",
        "Eleven twelve thirteen fourteen fifteen sixteen seventeen eighteen.",
        "",
    ]
    for text in texts:
        features = _features(text)
        assert 0.0 <= features.unique_word_ratio <= 1.0


# Abstract / body similarity


def test_abstract_body_similarity_is_one_when_identical():
    text = "The quick brown fox jumps over the lazy dog."
    features = _features(text, abstract=text)

    assert features.abstract_to_body_similarity == 1.0


def test_abstract_body_similarity_is_zero_when_abstract_empty():
    features = _features("Some body text here.", abstract="")

    assert features.abstract_to_body_similarity == 0.0


# Citations


def test_citation_density_positive_with_citations():
    text = "The method in [1] and [2] extends the earlier work [3]."
    features = _features(text)

    assert features.citation_density > 0.0


def test_citation_density_zero_without_citations():
    text = "This paragraph contains no numbered citation markers at all."
    features = _features(text)

    assert features.citation_density == 0.0


# Hedging


def test_hedge_word_ratio_positive_with_hedge_words():
    text = "This may be true. It might also hold. The effect could appear."
    features = _features(text)

    assert features.hedge_word_ratio > 0.0


# Section style variance


def test_section_style_variance_zero_for_uniform_style():
    text = "The results are consistent with prior work. " * 16
    features = _features(text)

    assert features.total_sentences == 16
    assert features.section_style_variance == 0.0


def test_short_text_below_four_chunks_does_not_crash():
    features = _features("One short sentence. A second one. A third.")

    assert isinstance(features.section_style_variance, float)


# Counts


def test_total_words_counts_correctly():
    features = _features("The cat sat on the mat.")

    assert features.total_words == 6


def test_total_sentences_counts_correctly():
    features = _features("First sentence. Second sentence! Is this the third?")

    assert features.total_sentences == 3


# Paragraphs


def test_total_paragraphs_counts_blank_line_blocks():
    text = "First paragraph.\n\nSecond paragraph.\n\nThird paragraph."
    features = _features(text)

    assert features.total_paragraphs == 3


def test_total_paragraphs_falls_back_to_full_text_without_pages():
    features = extract_features("One.\n\nTwo.", "", pages=[])

    assert features.total_paragraphs == 2


# Passive voice


def test_passive_voice_ratio_positive_for_passive_text():
    text = "The model was evaluated on the benchmark. The results were recorded."
    features = _features(text)

    assert features.passive_voice_ratio > 0.0