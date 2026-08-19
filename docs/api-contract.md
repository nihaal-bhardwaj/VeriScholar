# API Contract

Base URL: `http://localhost:8000/api/v1` (configurable via `API_PREFIX`).

All responses are JSON. Errors use `{"error": "...", "detail": "..."}` with appropriate HTTP status codes.

## Implemented endpoints

### `GET /health`

Health check.

```json
{
  "status": "healthy",
  "service": "mini-project-api",
  "version": "0.1.0"
}
```

### `POST /papers/extract`

Accepts one PDF via multipart form data (field name `file`).

Validations:

| Condition | Status code |
| --- | --- |
| No file provided / empty file | 400 |
| Non-PDF extension or wrong MIME type | 415 |
| File larger than `MAX_UPLOAD_SIZE_MB` | 413 |
| Password-protected / corrupt / no extractable text | 422 |
| Unexpected server errors | 500 |

Response:

```json
{
  "analysis_id": "generated-uuid",
  "status": "completed",
  "paper": {
    "filename": "example.pdf",
    "file_size_bytes": 123456,
    "page_count": 8,
    "doi": "10.1234/example",
    "doi_candidates": ["10.1234/example"],
    "abstract": "Extracted abstract text",
    "title": "Deep Learning for Iceberg Detection",
    "authors": ["Jane P. Doe", "John A. Smith"],
    "keywords": ["deep learning", "iceberg detection", "radar imagery"],
    "references_text": "Full extracted references section",
    "references": [
      {
        "number": 1,
        "raw_text": "First reference text",
        "doi": null
      }
    ],
    "pages": [
      {
        "page_number": 1,
        "text": "Page content"
      }
    ]
  },
  "warnings": []
}
```

`analysis_id` is a UUID v4 generated per request. Warnings describe signals the parser detected (e.g. missing abstract, unreliable reference splitting) — never a fake-paper verdict.

`title` is the conservatively detected paper title (`null` when the parser is uncertain or no abstract heading exists to anchor front matter). `authors` is the ordered, deduplicated list of detected author names; it is `[]` when no trustworthy names could be identified, never fabricated. `keywords` is the ordered list of detected keywords/index terms; it is `[]` when no keywords block exists.

### `POST /integrity/check`

Runs local consistency rules over an already-extracted paper. It performs no external API calls and never renders a fake-paper verdict — flags are explainable screening signals for human review.

Request body:

```json
{
  "analysis_id": "generated-uuid",
  "full_text": "Combined extracted text of the paper",
  "authors": ["Jane P. Doe", "John A. Smith"],
  "references": [
    {
      "number": 1,
      "raw_text": "First reference text",
      "doi": null
    }
  ],
  "pages": [
    {
      "page_number": 1,
      "text": "Page content"
    }
  ]
}
```

Response — the typed `ConsistencyReport`:

```json
{
  "flags": [
    {
      "rule": "figure_reference_consistency",
      "severity": "medium",
      "message": "Figure 3 is referenced in text but never defined",
      "evidence": "Results are shown in Figure 3 below."
    }
  ],
  "warnings": ["Expected section 'Conclusion' not found in paper"],
  "passed_checks": ["date_consistency: all cited reference years are on or before the paper's publication year"],
  "consistency_score": 0.75
}
```

- `flags` — one `ConsistencyFlag` per issue found by a rule (`rule` is the rule id, `severity` is `high`/`medium`/`low`, `message` is human-readable, `evidence` is the triggering text snippet).
- `warnings` — soft issues such as missing standard sections (Abstract, Introduction, Conclusion, References).
- `passed_checks` — rules that ran and found no issues.
- `consistency_score` — `0.0` to `1.0`; `1.0` means no issues found. Never a fraud verdict.

Rules currently implemented: `date_consistency`, `figure_reference_consistency`, `author_name_consistency`, `section_structure_consistency`, `reference_number_continuity`.

### `POST /report/generate`

Combines outputs from all analysis modules into one unified risk report. Citation and metadata modules are optional placeholders for now — they may be `null` and the generator still works. The report is an explainable screening signal for human review, never a fake-paper verdict.

Request body (`ReportInput`):

```json
{
  "analysis_id": "generated-uuid",
  "paper_title": "Deep Learning for Iceberg Detection",
  "paper_authors": ["Jane P. Doe", "John A. Smith"],
  "abstract": "Extracted abstract text",
  "keywords": ["deep learning", "iceberg detection"],
  "consistency_report": {
    "flags": [],
    "warnings": [],
    "passed_checks": [],
    "consistency_score": 1.0
  },
  "citation_results": null,
  "metadata_results": null,
  "ml_results": {
    "signals": [
      {
        "rule": "uniform_sentence_length",
        "severity": "medium",
        "message": "Sentence length variance is unusually low, suggesting AI-generated or templated writing",
        "evidence": "Sentence length variance: 2.10 (threshold: 5.0)",
        "weight": 0.5
      }
    ],
    "passed_rules": ["vocabulary_inflation", "abstract_body_mismatch", "style_shifting", "missing_hedging", "missing_citations", "low_readability", "high_readability", "passive_voice_absent", "short_paper"],
    "ml_risk_contribution": 8.0,
    "confidence": 0.8,
    "features_used": {
      "flesch_reading_ease": 42.3,
      "flesch_kincaid_grade": 9.1,
      "gunning_fog_index": 11.2,
      "automated_readability_index": 10.4,
      "unique_word_ratio": 0.61,
      "avg_word_length": 5.4,
      "rare_word_ratio": 0.06,
      "avg_sentence_length": 17.5,
      "sentence_length_variance": 2.1,
      "total_sentences": 88,
      "total_words": 1540,
      "total_paragraphs": 12,
      "abstract_to_body_similarity": 0.5,
      "section_style_variance": 8.0,
      "citation_density": 3.2,
      "passive_voice_ratio": 0.31,
      "hedge_word_ratio": 0.012
    },
    "summary": "Minor writing anomalies detected. Low concern."
  }
}
```

`ml_results` is the typed `MLAnalysisResult` from the rule-based anomaly scorer (ML module). It may be `null` while the ML module is unavailable. `signals` are threshold-based explainable writing-pattern findings; `ml_risk_contribution` is the points added to the final score; `confidence` reflects how much text was available (0.3 below 500 words, 0.5 below 1000, 0.8 at 1000+).

Response — the typed `RiskReport`:

```json
{
  "analysis_id": "generated-uuid",
  "paper_title": "Deep Learning for Iceberg Detection",
  "paper_authors": ["Jane P. Doe", "John A. Smith"],
  "risk_score": 15.0,
  "risk_level": "low",
  "confidence": 0.4,
  "summary": "Minor inconsistencies were detected. Human review is recommended but risk is low.",
  "signals": [
    {
      "source": "consistency",
      "severity": "medium",
      "message": "Figure 3 is referenced in text but never defined",
      "evidence": "Results are shown in Figure 3 below.",
      "weight": 0.5333
    }
  ],
  "passed_checks": ["date_consistency: all cited reference years are on or before the paper's publication year"],
  "modules_used": ["consistency"],
  "generated_at": "2026-08-18T12:00:00Z"
}
```

Scoring rules:

- Each `ConsistencyFlag` with severity `high` adds 15 points, `medium` adds 8, `low` adds 3; the ML module's `ml_risk_contribution` (computed the same way from its signals, capped at 100) is added on top; the combined score is capped at 100.0.
- Risk level thresholds: `0-25` low, `26-50` medium, `51-75` high, `76-100` critical.
- Confidence: `0.0` when no modules ran; capped at `0.6` when only the consistency module contributed; equal to the ML module's confidence when only ML ran; `min(0.85, average)` of the consistency score and ML confidence when both ran.
- `signal.weight` is the share of the maximum per-signal score (high = 1.0, medium ≈ 0.5333, low = 0.2 for consistency; ML signals carry their rule's own weight, e.g. 0.5 for medium-severity ML rules).

### `POST /analyze/full`

All-in-one endpoint: uploads a PDF, runs extraction, runs the consistency rules, runs the ML text analysis and generates the `RiskReport` in a single request. The frontend calls this for the complete analysis.

Request: one PDF via multipart form data (field name `file`), same validations as `/papers/extract` (400 missing/empty, 415 non-PDF, 413 oversized, 422 unusable PDF).

Response: `RiskReport` (same shape as `/report/generate`). `modules_used` now contains `["consistency", "ml"]` since both modules run. ML signals appear in `signals` with `source: "ml"`, and `confidence` is `min(0.85, average of the consistency score and the ML confidence)`.

```json
{
  "analysis_id": "generated-uuid",
  "paper_title": "Deep Learning for Iceberg Detection",
  "paper_authors": ["Jane P. Doe", "John A. Smith"],
  "risk_score": 37.0,
  "risk_level": "medium",
  "confidence": 0.6,
  "summary": "Several inconsistencies were found. A human reviewer should examine this paper.",
  "signals": [
    {
      "source": "consistency",
      "severity": "medium",
      "message": "Figure 3 is referenced in text but never defined",
      "evidence": "Results are shown in Figure 3 below.",
      "weight": 0.5333
    },
    {
      "source": "ml",
      "severity": "high",
      "message": "Paper contains fewer than 1000 words — insufficient content for a legitimate academic paper",
      "evidence": "Total words: 421 (threshold: 1000)",
      "weight": 1.0
    }
  ],
  "passed_checks": ["date_consistency: all cited reference years are on or before the paper's publication year"],
  "modules_used": ["consistency", "ml"],
  "generated_at": "2026-08-19T12:00:00Z"
}
```

### `POST /ml/analyze`

Runs the ML text analysis (feature extraction + anomaly scoring) on submitted text without a PDF upload. Never renders a fake-paper verdict — signals are explainable screening indicators for human review.

Request body (`MLAnalysisRequest`):

```json
{
  "full_text": "Combined text of the paper",
  "abstract": "The paper's abstract (optional, may be empty)",
  "pages": [
    {
      "page_number": 1,
      "text": "Page content"
    }
  ]
}
```

`full_text` is required; `pages` is optional and uses the same shape as the PDF parser's page output.

Response — the typed `MLAnalysisResult` (same shape as `ml_results` in `/report/generate`):

```json
{
  "signals": [
    {
      "rule": "uniform_sentence_length",
      "severity": "medium",
      "message": "Sentence length variance is unusually low, suggesting AI-generated or templated writing",
      "evidence": "Sentence length variance: 2.10 (threshold: 5.0)",
      "weight": 0.5
    }
  ],
  "passed_rules": ["vocabulary_inflation", "abstract_body_mismatch", "style_shifting", "missing_hedging", "missing_citations", "low_readability", "high_readability", "passive_voice_absent", "short_paper"],
  "ml_risk_contribution": 8.0,
  "confidence": 0.8,
  "features_used": {
    "flesch_reading_ease": 42.3,
    "flesch_kincaid_grade": 9.1,
    "gunning_fog_index": 11.2,
    "automated_readability_index": 10.4,
    "unique_word_ratio": 0.61,
    "avg_word_length": 5.4,
    "rare_word_ratio": 0.06,
    "avg_sentence_length": 17.5,
    "sentence_length_variance": 2.1,
    "total_sentences": 88,
    "total_words": 1540,
    "total_paragraphs": 12,
    "abstract_to_body_similarity": 0.5,
    "section_style_variance": 8.0,
    "citation_density": 3.2,
    "passive_voice_ratio": 0.31,
    "hedge_word_ratio": 0.012
  },
  "summary": "Minor writing anomalies detected. Low concern."
}
```

- `signals` — one `MLSignal` per triggered threshold rule (`rule` is the rule id, `severity` is `high`/`medium`/`low`, `message` is human-readable, `evidence` states the value and threshold).
- `passed_rules` — rule names that did not trigger.
- `ml_risk_contribution` — points contributed to the final risk score (high=15, medium=8, low=3, capped at 100).
- `confidence` — based on text availability: `0.3` under 500 words, `0.5` under 1000, `0.8` at 1000+ words; `0.0` when ML analysis could not run.
- `features_used` — the raw `TextFeatures` that were analyzed.

Rules implemented: `uniform_sentence_length`, `vocabulary_inflation`, `abstract_body_mismatch`, `style_shifting`, `missing_hedging`, `missing_citations`, `low_readability`, `high_readability`, `passive_voice_absent`, `short_paper`.

## Future combined analysis contract

All future team modules **must** follow this shared response shape. Each sub-analysis reports its own status; unimplemented modules return `"pending"` with `null` values, never fabricated numbers.

```json
{
  "analysis_id": "sample-id",
  "paper": {},
  "metadata_analysis": {
    "status": "pending",
    "warnings": []
  },
  "citation_analysis": {
    "status": "pending",
    "verified": 0,
    "unresolved": 0,
    "warnings": []
  },
  "ml_analysis": {
    "status": "pending",
    "risk_probability": null,
    "signals": []
  },
  "consistency_analysis": {
    "status": "pending",
    "warnings": []
  },
  "final_assessment": {
    "risk_score": null,
    "risk_level": null,
    "confidence": null,
    "main_reasons": []
  }
}
```

## Status codes

- `400` invalid or empty upload
- `413` oversized file
- `415` non-PDF file
- `422` extraction cannot produce usable content
- `500` unexpected server error only (stack traces are never exposed)

## Rules for team members

- Do not change field names in the shared contract without updating this document and coordinating with all members.
- New endpoints go under `/api/v1` with the module name, e.g. `/api/v1/metadata/verify`, `/api/v1/citations/verify`.
- Responses must be typed Pydantic models.
