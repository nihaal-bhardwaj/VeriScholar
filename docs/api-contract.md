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

Combines outputs from all analysis modules into one unified risk report. Citation, metadata and ML modules are optional placeholders for now — they may be `null` and the generator still works. The report is an explainable screening signal for human review, never a fake-paper verdict.

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
  "ml_results": null
}
```

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

- Each `ConsistencyFlag` with severity `high` adds 15 points, `medium` adds 8, `low` adds 3; capped at 100.0.
- Risk level thresholds: `0-25` low, `26-50` medium, `51-75` high, `76-100` critical.
- Confidence: `0.0` when no modules ran; capped at `0.6` when only the consistency module contributed.
- `signal.weight` is the share of the maximum per-signal score (high = 1.0, medium ≈ 0.5333, low = 0.2).

### `POST /analyze/full`

All-in-one endpoint: uploads a PDF, runs extraction, runs the consistency rules and generates the `RiskReport` in a single request. The frontend calls this for the complete analysis.

Request: one PDF via multipart form data (field name `file`), same validations as `/papers/extract` (400 missing/empty, 415 non-PDF, 413 oversized, 422 unusable PDF).

Response: `RiskReport` (same shape as `/report/generate`). `modules_used` currently contains only `"consistency"` until the citation/metadata/ML modules are built.

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
