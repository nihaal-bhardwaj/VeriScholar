# Project Status

Living document. Update it at the end of every working session.

## Project summary

- **Project name:** Mini Project
- **Primary module:** Research Paper Integrity Risk Detector
- **Secondary module:** Fake Review Detector
- **Current stage:** Project completed — Dual-engine VeriScholar integrity platform (Manuscript Screener & Review Astroturf Detector) fully implemented, hardened, and verified with 292/292 passing backend tests and clean Next.js production build.
- **Last known stable commit:** `8e31762` — project completed
- **Test status:** Backend 292/292 passing; frontend production build passing cleanly

> The commit hash above is checked against Git history on every session start. If `git log` shows a newer commit, treat that newer commit as the latest and update this document.

## Completed foundation

### Backend

- FastAPI application (Python 3.11+, Pydantic, environment-driven config, CORS, uniform error responses)
- `GET /api/v1/health`
- `POST /api/v1/papers/extract` with file validation (missing/empty → 400, non-PDF → 415, oversized → 413, corrupt/password-protected/no-text → 422)
- PDF parser: page-wise text, combined raw text, DOI candidates with punctuation cleanup, best-DOI selection, basic abstract detection, references-section detection, structured reference splitting (numbered with hanging markers, conservative author-year, per-entry DOI, warnings instead of fabricating entries), conservative title and author extraction, abstract boundary cleanup
- Typed Pydantic response models with `analysis_id` UUID
- 21 passing backend tests, no internet access required

### Frontend

- Next.js 16, TypeScript, Tailwind CSS v4
- Landing page titled Mini Project with placeholder navigation (Paper Analyser, Review Detector, Methodology)
- Lint and production build passing
- No backend integration yet

### Documentation and repository

- Root README, `AGENTS.md`, AI onboarding guide
- `docs/project-scope.md`, `docs/api-contract.md`, `docs/architecture.md`, `docs/team-workflow.md`
- Role playbooks in `docs/roles/`
- Sample response (`sample-responses/sample-paper-analysis.json`)
- `ml/` and `sample-papers/` directory skeletons
- Main-only sequential Git workflow (one member works and pushes at a time)

## Baseline and reference-extraction milestone

- Five-paper extraction baseline completed against the live backend (`local-results/`)
- Independent ground truth for all five papers completed
- Parser comparison against the baseline completed (95 comparison rows; 51 PASS / 6 PARTIAL / 3 FAIL / 35 not supported)
- Phase 6 — reliable structured reference extraction implemented:
  - Numbered references with same-line markers (`[1]`, `1.`, `1)`)
  - Hanging-indent numbered references (bare marker on its own line)
  - Conservative author-year bibliographies, including wrapped `(YYYY).` continuations, corporate/Unicode/hyphenated authors and year suffixes (`2018a`)
  - Per-entry DOI extraction; shared reliability gate; warn-not-fabricate behaviour; five warning classes
- Real-paper results: PLOS 171 entries, accepted manuscript 51 entries, older journal 35 entries — all within acceptance ranges
- Tests increased from 21 to 40 for Phase 6; 46 after Phase-7 review additions
- No schema change, no new dependency, no fabricated entries
- Unlabelled reference-section detection remains out of scope
- Abstract cleanup remains pending

## Phase 1 — Title, authors, abstract boundaries and API integration

- Conservative title extraction: first plausible front-matter line with quiet wrapped-title continuation; rejects metadata labels, decorative labels, headers/footers, DOI/URL/email/ORCID/copyright tokens, digit-led and prose lines; `null` + hedged warning when uncertain, no warning when front matter is empty.
- Conservative author extraction anchored on the detected title block: supports `John Doe`, comma/`and`/`&` separators, multi-line blocks and `Doe, J. R.` initials form; strips superscripts (`Doe1,2`); ignores emails, URLs, DOIs, ORCID strings, affiliation-numbered lines, departments/universities/institutes/hospitals/labs etc.; order preserved, case-insensitive dedupe; `[]` instead of fabricated names; single hedged warning only when a non-empty region yields nothing.
- Abstract boundary cleanup: abstract now stops at bare headings and colon-prefixed metadata labels `Keywords`/`Index Terms`/`Funding`/`Citation`/`Received`/`Accepted`, matched case-insensitively and whitespace-tolerantly; colon labels are matched structurally so prose like `Received wisdom suggests...` never truncates the abstract; reference splitting untouched.
- Schema and API: `PaperExtraction` exposes additive `title: str | None` and `authors: list[str]`; the extract route maps parser values end to end.
- Tests increased from 46 to 86; no new dependency; warn-not-fabricate behaviour preserved throughout.

## Consistency rules milestone (Citation Integrity role)

- Local consistency rules engine `backend/app/services/consistency_checker.py` — no external API calls:
  - Rule 1 `date_consistency`: cited reference years after the paper's publication year flagged (`Received:`/`Accepted:`/`Published`/`Copyright`/`©` markers, abstract-year fallback, skipped when no paper year found)
  - Rule 2 `figure_reference_consistency`: figures referenced in text but never defined flagged
  - Rule 3 `author_name_consistency`: author last names absent from the paper text flagged
  - Rule 4 `section_structure_consistency`: missing Abstract/Introduction/Conclusion/References reported as soft warnings
  - Rule 5 `reference_number_continuity`: `[N]` citations with no matching reference-list entry flagged
- Typed Pydantic schema `backend/app/schemas/consistency.py`: `ConsistencyFlag`, `ConsistencyReport` (`flags`, `warnings`, `passed_checks`, `consistency_score`), `ConsistencyCheckRequest`
- New endpoint `POST /api/v1/integrity/check` wired into `main.py`; documented in `docs/api-contract.md` (including `keywords` in the extract response example)
- Tests: 13 new in `backend/tests/test_consistency_checker.py`; full backend suite 110/110 passing
- No new dependency; no existing tests modified; warnings never reduce evidence quality and flags never claim fraud

## Report generator milestone (Technical Lead)

- Final combiner `backend/app/services/report_generator.py`:
  - `ReportInput` accepts optional `ConsistencyReport`, citation/metadata/ML placeholders (`None` allowed)
  - `RiskReport` output: `risk_score` (0–100, high=15 / medium=8 / low=3 points, capped), `risk_level` (low/medium/high/critical thresholds 25/50/75), `confidence` (0.0 with no modules; capped 0.6 when only consistency runs), template `summary`, `signals` with weights, `passed_checks`, `modules_used`, `generated_at`
- New schemas in `backend/app/schemas/report.py`: `ReportInput`, `RiskSignal`, `RiskReport`
- New endpoints wired in `main.py`:
  - `POST /api/v1/report/generate` — combine module outputs into `RiskReport`
  - `POST /api/v1/analyze/full` — all-in-one PDF upload → extraction → consistency → `RiskReport`
- Tests: 16 new in `backend/tests/test_report_generator.py`; full backend suite 126/126 passing
- `docs/api-contract.md` updated with both endpoints; no new dependency; existing tests untouched

## Frontend UI polish + VeriScholar branding milestone

- Rebranded the website to **VeriScholar** (user decision; reverts the earlier "Mini Project" naming in the frontend only):
  - `frontend/app/layout.tsx` — metadata title/description
  - `frontend/app/page.tsx` — landing header, hero, footer
  - `frontend/app/analyser/page.tsx` — header
- Landing page redesigned: sticky blurred header with logo mark, hero with badge + gradient headline + CTAs, "How it works" feature cards with honest Live / Coming-soon status tags, disclaimer footer
- Analyser progress stages made honest: removed fake "Verifying metadata with Crossref…" / "Running ML models…" steps (those modules don't run yet); now Upload → Extract → Generate, matching the real pipeline
- Report dashboard polished: analysis ID shown, title/authors added to Document Details, module status rows now carry plain-language descriptions of each module
- `frontend/lib/api-types.ts` updated with `title`, `authors`, `keywords` fields (already returned by the backend)
- Frontend lint and production build passing

## Current overall milestone

```text
Phase 1 complete: title, authors, abstract boundary cleanup, and schema/API integration (uncommitted, awaiting commit/push).
ML text feature extraction Phase 1 + anomaly scoring Phase 2 + pipeline wiring Phase 3 complete (176 → 191 tests green).
```

## Fake Review Detector — Gemini 3.1+ & Groq LLM Analysis & Incoherence Detection

- Integrated Google Gemini 3.1+ API with strict version enforcement (rejecting any model below 3.1 such as Gemini 1.5, 2.0, 2.5, 3.0, and enforcing `gemini-3.1-flash`, `gemini-3.8-flash`, etc.):
  - `backend/app/core/config.py`: Added `gemini_api_key: str = ""` and `gemini_model: str = "gemini-3.1-flash"`.
  - `backend/app/services/reviews/llm_analyzer.py`: Added `_validate_gemini_model` to enforce version $\ge 3.1$, `_call_gemini_completion` via httpx to Google Generative Language API (`v1beta/models/{model}:generateContent`) with `response_mime_type: "application/json"`, prioritizing Gemini when configured with safe fallback error handling (`timeout`, `api_error`, `not_configured`, `parse_error`).
  - Added 5 new tests in `backend/tests/test_llm_analyzer.py` verifying Gemini model rejection (< 3.1), acceptance ($\ge 3.1$), execution, timeouts, and error handling (21/21 passed).
  - Configured environment variables in `.env.example` and `backend/.env.example`.

## Research Paper Integrity — Citation Verification Pipeline Integration

- Integrated OpenAlex citation verification pipeline end-to-end:
  - `backend/app/schemas/citation.py` & `backend/app/schemas/report.py`: Added detailed per-reference records and `citation_results` in `RiskReport`.
  - `backend/app/services/citations/verifier.py`: Added `_extract_title_candidate`, bounded concurrency (`asyncio.Semaphore(5)`), and 25-reference sampling cap.
  - `backend/app/services/report_generator.py`: Added citation risk signals and included `"citations"` in `modules_used`.
  - `backend/app/api/routes/report.py`: Wired citation checking concurrently with metadata check with an 8s timeout guard.
  - `frontend/components/report/ReportDashboard.tsx`: Replaced hardcoded `(xlii)` tab header with dynamic citation count and real reference status badges.
  - 292/292 backend pytest suite passing.

## Code Review Hardening & Bug Fixes (Session Update)

- **File upload size validation:** Aligned enforced limit in `frontend/app/page.tsx` (`file.size > 20 * 1024 * 1024`) with user-facing message and helper text (20 MB).
- **Status test count:** Reconciled line 12 test status with the complete suite (now 292/292 passing).
- **Citation reference truncation transparency:** Added explicit warning in `backend/app/services/citations/verifier.py` when references exceed the 25-item sample cap (`"Only the first 25 of {total} references were verified."`).
- **Citation lookup timeout resilience:** Added internal timeout handling (`asyncio.wait(..., timeout=6.5)`) and reduced per-call HTTP timeout to 2.0s inside `verify_citations` so completed lookups are never discarded on timeout, returning partial results and warning when the budget is reached.
- **Review expanded state keying:** In `frontend/components/reviews/ReviewReportDashboard.tsx`, keyed `expandedReviews` and `expandedSignals` by original index in `data.reviews` rather than displayed index, and cleared expansion state when filters/search/sort change.
- **Delayed Object URL revocation:** Wrapped `URL.revokeObjectURL(url)` in `setTimeout(..., 0)` across `ReportDashboard.tsx` and `ReviewReportDashboard.tsx` to prevent premature cancellation of JSON report downloads in Firefox and Safari.
- **Signal expansion stability:** In `frontend/components/report/ReportDashboard.tsx`, keyed `openSignalIds` by the original unfiltered signal index so filtered card toggling does not attach to incorrect signals upon filter change.
- **Citation table React keys:** In `frontend/components/report/ReportDashboard.tsx`, keyed citation rows with the array index (`key={`cit-row-${idx}`}`) to eliminate key collisions when reference numbers are null or duplicate.
- **Documented Gemini model ID default:** Updated default Gemini model to `gemini-3.1-flash-lite` across `backend/app/services/reviews/llm_analyzer.py`, `backend/app/core/config.py`, `.env.example`, `backend/.env.example`, and test mocks to match Google's documented Gemini 3.1 endpoints and prevent 404/api_error.
- **Configurable Groq model setting:** Declared `groq_model: str = "qwen/qwen3.8-27b"` as a first-class field in `backend/app/core/config.py` `Settings`, documented in `.env.example`, and verified via unit tests.

## Per-role status

| Role | Completed | Current priority | Next deliverable | Dependencies | Known blockers |
| --- | --- | --- | --- | --- | --- |
| Technical Lead, Backend & PDF Processing Engineer | FastAPI app, health + extract endpoints, parser, tests, API contract; five-paper baseline, ground truth and parser comparison; structured reference extraction (numbered, hanging markers, conservative author-year, per-entry DOI); Phase 1: conservative title extraction, conservative author extraction, abstract boundary cleanup, schema/API integration of `title` + `authors` (86 tests); report generator: `RiskReport` combiner with scoring/levels/confidence, `POST /report/generate` and `POST /analyze/full` endpoints (16 tests, 126/126 suite green) | Extract keywords/index terms; section-heading detection; page-number/evidence tracking | Keywords and index-terms extraction with regression tests | None (parser runs standalone); Phase-1 work uncommitted and awaiting team commit/push | None |
| Research Paper ML & Dataset Engineer | ML Phase 1: rule-based NLP text feature extractor — `TextFeatures` schema (`backend/app/schemas/ml.py`) + `backend/app/services/ml/feature_extractor.py` covering readability (textstat), vocabulary, sentence structure, abstract/body similarity, section-style variance, citation density, passive voice and hedging; offline-safe NLTK bootstrap; 17 new tests (143/143 suite green). ML Phase 2: anomaly scoring engine `backend/app/services/ml/anomaly_scorer.py` — 10 threshold rules producing `MLSignal`/`MLAnalysisResult` (ml_risk_contribution capped at 100, confidence by text size 0.3/0.5/0.8, summary templates); wired into `report_generator` via `ReportInput.ml_results: Optional[MLAnalysisResult]` (ml signals → RiskSignal source="ml", contribution added to score, confidence = ML confidence when ML-only or min(0.85, avg) with consistency); API contract updated; 33 new tests (176/176 suite green). ML Phase 3: pipeline wiring — `ml_pipeline.py` orchestrator chaining extractor→scorer with safe fallback on errors; `/api/v1/ml/analyze` standalone endpoint; ML integrated into `/api/v1/analyze/full` (`modules_used: ["consistency", "ml"]`); 15 new tests (191/191 suite green) | Wire ML result into the frontend report dashboard; tune thresholds on real papers | ML module is fully wired end to end; next is frontend display of ML signals + optional threshold tuning | Extraction schema from Technical Lead (available); `ReportInput.ml_results` schema change coordinated in `docs/api-contract.md` | None |
| Citation Integrity, Metadata Verification & Fake Review Engineer | Local consistency rules engine (5 rules), typed `ConsistencyReport` schema, `POST /api/v1/integrity/check` endpoint; Fake Review Detector scraper, batch analyzer, rule-based analyzer with specificity, before/after narrative heuristics, and Rule 8 product category incoherence; Groq API (Llama 3.3 70B) LLM analyzer service with corrected pre-filtering, score inversion, prompt incoherence detection, structured JSON fallback retry, batch rate-limiting delay, safe error handling, and frontend badges/reasoning display (284/284 backend suite green) | Production scraping resilience and external metadata integrations | Crossref DOI lookup or extended e-commerce platforms | None | None |
| Frontend & Deployment Engineer | Next.js scaffold; PDF upload flow; mock analysis-progress UI; real backend API integration (fetch, FormData, CORS); Fake Review Detector UI with manual input & URL scraping, circular progress ring, badges, and expandable "Why?" drawer | Build remaining real-time progress indicators once WebSocket/SSE is added | Complete frontend flow using live FastAPI backend | Stable API contract | None |

## Update rules

Every completed session must update this document with:

- Latest stable commit when known
- Completed items (moved from pending/current to completed)
- Current task
- Next task
- New blockers
- Tests run
- API contract changes

Do not allow completed work to remain marked as pending.

