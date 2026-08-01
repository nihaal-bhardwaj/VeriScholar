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
