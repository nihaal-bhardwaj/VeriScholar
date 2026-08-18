# Role Manual — Technical Lead, Backend & PDF Processing Engineer

## 1. Role name

- **Official role name:** Technical Lead, Backend & PDF Processing Engineer
- **Short role name:** Backend & PDF Lead
- **Purpose:** Own the main backend — receive uploaded research-paper PDFs, convert them into structured data, expose backend APIs, and later connect all analysis modules into one explainable result.

## 2. Position in the system

```text
PDF upload
→ PDF extraction           ← this role owns everything up to and including here
→ Metadata and citation checks   (Citation Integrity Engineer)
→ ML analysis                    (Paper ML Engineer)
→ Combined result                (this role orchestrates)
→ Frontend report                (Frontend Engineer)
```

This role owns the system entry point (`POST /api/v1/papers/extract`) and the future orchestrator that combines the outputs of all other modules. Every other role consumes the structured extraction produced here.

## 3. Main responsibilities

### Core responsibilities

- FastAPI application structure (`app/main.py`, routing, middleware, error handling).
- Central configuration via environment variables.
- PDF upload endpoint with file-type, file-size, empty-file, corrupt-PDF and password-protected-PDF validation.
- Research-paper structure parsing with PyMuPDF.
- Extraction of pages, combined text, DOIs, title, authors, keywords, abstract and major sections.
- Reference parsing with warnings instead of fabricated entries.
- Typed Pydantic request/response schemas.
- Uniform, non-leaking error responses.

### Integration responsibilities

- Orchestrating the future analysis chain: paper ML, metadata verification, citation checking and integrity rules.
- Combining partial results when some modules fail or time out.
- Producing the final explainable combined response with confidence based on which checks actually ran.

### Testing responsibilities

- Unit tests for the parser (offline, programmatically generated PDFs).
- Integration tests for endpoints (validation, status codes, error bodies).
- Regression tests whenever the extraction schema changes.

### Documentation responsibilities

- Keep `docs/api-contract.md` in sync with every schema change.
- Update `docs/project-status.md` and `docs/session-handoff.md` after meaningful work.

### Optional advanced responsibilities

- Result persistence (SQLite/PostgreSQL via SQLAlchemy) and report retrieval — later stages only.
- OCR handling for scanned PDFs — optional, not required for the MVP.

## 4. Owned files and directories

### Primary ownership

```text
backend/app/main.py
backend/app/api/
backend/app/core/
backend/app/schemas/
backend/app/services/pdf_parser.py
backend/tests/
docs/api-contract.md
```

### Future directories this role may create

```text
backend/app/services/orchestrator/
backend/app/services/scoring/
backend/app/database/
```

### Shared files requiring coordination

- `docs/api-contract.md` — response-shape changes require schema + tests + docs + sample-response + frontend coordination.
- `sample-responses/sample-paper-analysis.json` — must match the extraction schema.
- `backend/requirements*.txt` — dependency additions must be documented.

### Other members' areas (do not casually edit)

```text
ml/                       → Paper ML Engineer
backend/app/services/paper_ml/ → Paper ML Engineer
backend/app/services/metadata/, citations/, integrity_rules/, review_detector/ → Citation Integrity Engineer
frontend/                 → Frontend Engineer
```

## 5. Programming languages

| Language | Why it is needed | Expected level |
| --- | --- | --- |
| Python | The entire backend, parser and tests are written in Python | Advanced |
| JSON | API request/response payloads, sample responses, config | Intermediate |
| Markdown | API contract and project documentation | Basic |
| SQL | Later persistence and report retrieval (SQLite/PostgreSQL) | Basic (learn later) |

## 6. Technologies and libraries

| Technology | Purpose in Mini Project | Required or optional |
| --- | --- | --- |
| FastAPI | Web framework: routing, validation, OpenAPI docs, CORS | Required |
| Pydantic | Typed schemas and validation of all API inputs/outputs | Required |
| PyMuPDF (fitz) | PDF text extraction, page iteration, encryption/corruption detection | Required |
| Uvicorn | ASGI server for development and production | Required |
| Pytest | Backend test suite with fixtures and TestClient | Required |
| httpx | API testing and future outbound calls (orchestrator to module services) | Required |
| Regular expressions | DOI, reference and heading pattern matching | Required |
| SQLAlchemy | Future persistence layer | Optional (later) |
| SQLite / PostgreSQL | Future result storage | Optional (later) |

## 7. Knowledge requirements

### Must understand

- Python typing, dataclasses, exception handling and `re` module.
- FastAPI basics: routers, `File`/`UploadFile`, status codes, exception handlers, dependency-free thin handlers.
- Pydantic v2: `BaseModel`, defaults, optional fields, `model_dump`.
- PyMuPDF basics: `fitz.open(stream=...)`, `Document`, `Page.get_text`, `needs_pass`, exception types.
- Pytest: fixtures, parametrize, TestClient.
- PDF layout concepts: text blocks vs lines, headers/footers, two-column layouts.

### Should learn during development

- Heuristic section detection and confidence scoring for title/authors/sections.
- Reference-splitting strategies for varied bibliography styles.
- Pagination-aware extraction (sections spanning pages).
- Environment-driven configuration patterns.

### Optional advanced knowledge

- OCR (PyMuPDF Tesseract integration) for scanned PDFs.
- SQLAlchemy ORM and SQLite/PostgreSQL persistence.
- Async request handling and module timeout orchestration.

## 8. Official documentation and sources

| Source | What to learn or obtain from it | Priority |
| --- | --- | --- |
| [Python documentation](https://docs.python.org/3/) — verified | Language reference, `re` module, typing, stdlib | Required |
| [FastAPI documentation](https://fastapi.tiangolo.com/) — verified | Routing, UploadFile/File, exception handlers, CORS, OpenAPI | Required |
| [Pydantic documentation](https://docs.pydantic.dev/latest/) — verified | Models, validation, serialization | Required |
| [PyMuPDF documentation](https://pymupdf.readthedocs.io/en/latest/) — verified | Text extraction, document opening, encryption flags | Required |
| [Pytest documentation](https://docs.pytest.org/en/stable/) — verified | Fixtures, parametrization, TestClient usage | Required |
| [HTTPX documentation](https://www.python-httpx.org/) — verified | Client, timeouts, testing against ASGI apps | Required |
| Uvicorn documentation — docs.uvicorn.org — **URL could not be verified; confirm before adding** | ASGI server configuration | Recommended |
| [SQLAlchemy documentation](https://docs.sqlalchemy.org/en/20/) — verified | Future persistence layer | Optional (later) |
| [SQLite documentation](https://www.sqlite.org/docs.html) — verified | Future lightweight storage | Optional (later) |
| [PostgreSQL documentation](https://www.postgresql.org/docs/) — verified | Future production storage | Optional (later) |

## 9. Inputs received

### Currently

- **Source:** Frontend Engineer (or any HTTP client) uploads a PDF.
- **Endpoint:** `POST /api/v1/papers/extract` (multipart form field `file`).
- **Required:** one file with a `.pdf` extension.
- **Optional:** MIME type (`application/pdf` when supplied).
- **Missing-data behaviour:** 400 when no file or empty file; 415 for non-PDF extension/MIME; 413 above `MAX_UPLOAD_SIZE_MB`; 422 for corrupt, password-protected or text-less PDFs.

### Later (orchestrator)

- **Source:** Paper ML Engineer, Citation Integrity Engineer.
- Typed module outputs following `docs/api-contract.md` (combined analysis shape).
- Partial or missing module results must be tolerated and reported as unavailable, never fabricated.

## 10. Outputs produced

### Primary output

- **Consumer:** Frontend Engineer (display), Paper ML Engineer and Citation Integrity Engineer (features/input).
- **Contract:** `docs/api-contract.md` — `POST /papers/extract` response.
- **Required fields:** `analysis_id` (UUID), `status`, `paper` (filename, file_size_bytes, page_count, doi, doi_candidates, abstract, references_text, references, pages), `warnings`.
- **Status values:** `completed` when extraction succeeded.
- **Warnings:** free-form list describing missing sections, unreliable reference splitting, missing DOI — never a verdict about the paper.
- **Error behaviour:** uniform `{"error": ..., "detail": ...}` bodies; no stack traces.

### Later outputs (orchestrator)

- Combined response with `metadata_analysis`, `citation_analysis`, `ml_analysis`, `consistency_analysis` and `final_assessment` blocks, each reporting `pending` until a module actually runs.
- Model/version information for each executed module.

## 11. Things to implement

### Foundation (already in place — maintain and stabilise)

1. PDF upload endpoint with full validation and readable error codes.
2. Page-wise and combined text extraction.
3. DOI candidate extraction with punctuation cleanup.
4. Basic abstract and references-section detection.
5. Numbered reference splitting (`[1]` and `1.` styles) with warnings instead of fabrication.
6. Typed response schemas and uniform error handling.

### MVP implementation

7. Documented parser test matrix across academic PDF layouts (single-column, two-column, IEEE, APA, no-DOI, DOI in header/footer, "Summary" instead of "Abstract", keywords/index terms, numbered and unnumbered bibliographies, missing references, scanned/image-only, password-protected, corrupted).
8. Title extraction with confidence and warnings.
9. Conservative author extraction.
10. Keywords / index-terms extraction.
11. Section-heading detection.
12. Major-section extraction: abstract, introduction, methodology/methods, results, discussion, conclusion, references.
13. Page-number/evidence tracking for extracted content.
14. Improved reference parsing (author-year style, multi-line entries, references across pages).
15. Stable typed extraction schema reflecting the target structure in `docs/api-contract.md`.

### Integration

16. Orchestrator that calls ML, metadata, citation and integrity-rule modules.
17. Partial-failure handling with per-module timeouts.
18. Combined explainable response with confidence based on completed checks.

### Testing

19. Test every parser feature with programmatically generated PDFs; endpoint tests for every validation path.

### Optional improvements

20. Scanned-PDF OCR support.
21. Database persistence and stable report retrieval (SQLAlchemy + SQLite/PostgreSQL).
22. Caching of extraction results by file hash.

Do not begin scoring or database history before the structured extraction interface is stable enough for other modules to consume.

## 12. Acceptance criteria

- Every extraction field is defined in a Pydantic schema that matches `docs/api-contract.md` and `sample-responses/sample-paper-analysis.json`.
- The parser produces correct results on every layout in the documented test matrix; failures produce warnings, not wrong data.
- Missing sections, missing DOI and unreliable reference splitting always surface in `warnings`.
- No reference entry is invented: unsplittable bibliographies return the raw text plus a warning.
- All endpoint validation paths return the documented status codes with uniform error bodies.
- Adding a feature adds a test; the full suite stays green.

## 13. Testing responsibilities

### Unit tests

- DOI extraction, punctuation cleanup, deduplication.
- Abstract detection variants ("Abstract", "Summary", stop headings).
- Reference splitting for `[1]` and `1.` styles, multi-line entries, mixed/unreliable styles.
- Password-protected, corrupt and text-less PDF behaviour.

### Integration tests

- Health endpoint.
- Successful extraction round trip.
- 400 / 413 / 415 / 422 responses for each validation path.
- Uniform error body shape.

### Failure and edge cases

- Empty file, missing file field, oversized file, wrong MIME, wrong extension.
- Two-page documents, long sections spanning pages, references split across pages.
- No-DOI papers; DOIs with trailing punctuation; duplicate DOIs.
- Papers with no abstract, no references, or unnumbered bibliography.

### Manual demonstrations

- Run the server and upload a generated multi-page PDF via `curl` or the OpenAPI docs UI; confirm page count, sections, DOIs and warnings.

### Commands

```bash
cd backend
python -m pytest
uvicorn app.main:app --reload
```

### Evidence to record

- Full test output (pass/fail counts).
- Sample extraction JSON for one generated test PDF.

## 14. Dependencies on other roles

### Needs from other roles

- **Paper ML Engineer:** agreed feature fields (title/abstract) and the `ml_analysis` output shape for orchestration.
- **Citation Integrity Engineer:** the `metadata_analysis` / `citation_analysis` output shapes and endpoint names.
- **Frontend Engineer:** feedback on which extracted fields are needed for display; coordination before any response-shape change.

### What other roles need from this role

- A stable, typed extraction response (every other module consumes it).
- Updated `docs/api-contract.md` when the contract changes.

### What may be mocked temporarily

- ML, metadata and citation module outputs while building the orchestrator — clearly labelled as mocks, never presented as real analysis.

### Contract changes requiring coordination

Any response-shape change requires: schema update, backend test update, `docs/api-contract.md` update, `sample-responses/` update, frontend coordination, and a `docs/project-status.md` entry.

## 15. Common mistakes to avoid

- Breaking the API contract for a future feature instead of coordinating a versioned change.
- Fabricating references, sections or DOIs when detection fails — warn instead.
- Claiming parser output is reliable without testing across multiple layouts.
- Storing uploaded PDFs permanently without a deliberate, documented design.
- Exposing stack traces or secrets through error responses.
- Adding dependencies without documenting why.
- Silently editing ML, citation or frontend modules.
- Starting scoring/database work before extraction is stable.

## 16. Definition of done

- [ ] Working implementation matching the documented contract.
- [ ] Tests added/updated; full backend suite green.
- [ ] Error handling covers the relevant failure and edge cases.
- [ ] `docs/api-contract.md` and `sample-responses/` in sync with schemas.
- [ ] No unrelated files modified.
- [ ] `docs/project-status.md` updated.
- [ ] Handoff entry appended to `docs/session-handoff.md`.
- [ ] Commit/push status reported to the team.

## 17. Handoff requirements

After meaningful changes, report:

- Files changed.
- Interfaces added or changed (endpoints, schemas, status codes).
- Tests run and results.
- Known limitations (layouts not covered, unreliable patterns).
- Dependencies introduced and why.
- Whether changes were committed and pushed.

## 18. Viva knowledge

Be able to explain:

- The Mini Project pipeline and why outputs are risk signals, not proof of misconduct.
- Why heuristic parsing produces warnings instead of fabricated data.
- DOI regex design, candidate cleanup and best-DOI selection.
- How abstract and references detection works and when it fails.
- Reference-splitting strategy and why mixed styles return warnings.
- Validation mapping to HTTP status codes (400/413/415/422/500).
- Why route handlers are thin and logic lives in services.
- Environment-based configuration and CORS setup.
- Pydantic response models and why `analysis_id` is a UUID.
- The future combined-analysis contract and how module status must be reported honestly.
- Differences between single-column and two-column PDF text extraction.
- How password-protected and corrupt PDFs are detected with PyMuPDF.
- Design of the future orchestrator: timeouts, partial failures, confidence.
