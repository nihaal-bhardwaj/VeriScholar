# Session Handoff Log

Append-only log. **New entries go at the bottom of this file** (keep chronological order). Copy the template below, fill it in, and append it after completing work.

## Template

```markdown
## YYYY-MM-DD — Member name or role

### Role
Frontend & Deployment Engineer

### Work completed
- ...

### Files changed
- ...

### Tests run
- ...

### Current state
- ...

### Next recommended task
- ...

### Dependencies or blockers
- ...

### Commit / push
- Commit:
- Pushed to main: Yes / No
```

---

## 2026-07-31 — Foundation (all roles)

### Role
Project foundation (initial scaffold; no individual role owner)

### Work completed
- FastAPI backend: health endpoint (`GET /api/v1/health`) and PDF extraction endpoint (`POST /api/v1/papers/extract`) with validation (400/413/415/422/500 error handling), environment-based configuration, CORS, uniform error responses.
- PDF parser: page-wise text, combined raw text, DOI candidates with punctuation cleanup, best-DOI selection, basic abstract and references-section detection, numbered reference splitting with warnings instead of fabrication.
- Typed Pydantic response models with `analysis_id` UUID.
- Frontend: Next.js 16 + TypeScript + Tailwind CSS v4 scaffold, landing page, placeholder navigation (Paper Analyser, Review Detector, Methodology).
- Documentation: root README, `docs/project-scope.md`, `docs/api-contract.md`, `docs/architecture.md`, `docs/team-workflow.md`, `AGENTS.md`, `docs/ai-onboarding.md`, `docs/project-status.md`, role playbooks in `docs/roles/`, `docs/session-handoff.md`.
- Repository: `.gitignore`, `.env.example`, `ml/` and `sample-papers/` skeletons, `sample-responses/sample-paper-analysis.json`.

### Files changed
- `backend/app/**`, `backend/tests/**`, `backend/requirements*.txt`
- `frontend/**` (scaffold)
- `ml/**`, `docs/**`, `sample-*/**`
- `.gitignore`, `.env.example`, `README.md`, `AGENTS.md`

### Tests run
- Backend: `python -m pytest` → 21 passed
- Frontend: `npm run lint` (clean), `npm run build` (success)

### Current state
- Foundation complete; independent module development can begin.
- Latest commit: `3e03bfc`

### Next recommended task
- Technical Lead: test parser on real academic PDFs, then improve title/authors/keywords/section extraction.
- Paper ML: define labels and build the TF-IDF Logistic Regression baseline.
- Citation Integrity: build Crossref/OpenAlex metadata verification with mocked tests.
- Frontend: build PDF upload and mock report flow.

### Dependencies or blockers
- None.

### Commit / push
- Commit: `3e03bfc` (Set up VeriScholar project foundation)
- Pushed to main: Yes

---

## 2026-08-01 — Technical Lead, Backend & PDF Processing Engineer

### Role
Technical Lead, Backend & PDF Processing Engineer (repository-wide coordination)

### Work completed
- Renamed the project from "VeriScholar" to "Mini Project" across docs, config, backend code and frontend text.
- Display names updated: `VeriScholar` → `Mini Project`.
- Service identifier updated: `verischolar-api` → `mini-project-api` (health endpoint, API contract, health test).
- Logger name updated: `verischolar` → `mini-project` in `backend/app/main.py`.
- `APP_NAME` updated to `Mini Project API` in `.env.example` and `backend/app/core/config.py`.
- Frontend page title and metadata updated in `frontend/app/layout.tsx` and `frontend/app/page.tsx`.

### Files changed
- `README.md`, `AGENTS.md`, `.env.example`
- `backend/app/main.py`, `backend/app/core/config.py`, `backend/app/api/routes/health.py`, `backend/app/__init__.py`, `backend/app/api/__init__.py`, `backend/tests/__init__.py`, `backend/tests/test_health.py`, `backend/README.md`
- `frontend/app/layout.tsx`, `frontend/app/page.tsx`, `frontend/README.md`
- `ml/README.md`
- `docs/**` (api-contract, project-scope, project-status, ai-onboarding, roles, session-handoff)

### Tests run
- Backend: `python -m pytest` (planned; health test updated to match new service name)
- Frontend: no logic changes; text-only

### Current state
- Name change complete. Historical commit-message quotes (`Set up VeriScholar project foundation`) left verbatim since they reference real Git history.
- The repository folder on disk is still named `verischolar`; renaming it is left to the team.

### Next recommended task
- Unchanged from the previous foundation entry per role.

### Dependencies or blockers
- None.

### Commit / push
- Commit: none (not requested)
- Pushed to main: No

---

## 2026-08-01 — Technical Lead, Backend & PDF Processing Engineer (Phases 6–7)

### Role
Technical Lead, Backend & PDF Processing Engineer

### Work completed
- Phases 1–5 baseline and analysis: five-paper extraction baseline, independent ground truth, parser comparison (95 rows; 51 PASS / 6 PARTIAL / 3 FAIL / 35 not supported), priorities file.
- Phase 6 — reliable structured reference extraction:
  - Numbered references: bracket, period and paren styles (same-line).
  - Hanging-indent numbered references (bare marker on its own line, e.g. `1.`).
  - Conservative author-year bibliography splitting, including wrapped `(YYYY).` continuations, corporate/Unicode/hyphenated authors, and year suffixes (`2018a`).
  - Per-entry DOI extraction; shared reliability gate; warn-not-fabricate behaviour; five warning classes.
  - Real-paper acceptance results: PLOS 171, accepted manuscript 51, older journal 35 (all within target ranges; arXiv unlabelled section intentionally out of scope; scanned paper stays empty).
  - Tests increased from 21 to 40; no schema change; no new dependency; no fabrication.
- Phase 7 — final review and documentation:
  - Reviewed architecture (separation of responsibilities), conservative behaviour, ordering/preservation, Unicode handling, regex/performance (linear), warning quality.
  - Audited test coverage and justified the adapted pre-existing test; added six focused tests (single bracket entry rejected, numbered multi-line bodies merged, marker-only fragments dropped, header/footer lines not boundaries, author-year tiny fragments rejected, low-confidence warning). Test count now 46.
  - Updated `docs/project-status.md` and `docs/session-handoff.md`.

### Files changed
- `backend/app/services/pdf_parser.py` — reference-splitting pipeline
- `backend/tests/test_pdf_parser.py` — Phase-6 tests, 1 adapted pre-existing test, 6 review additions
- `backend/tests/test_papers_api.py` — reference-schema regression test
- `docs/project-status.md`, `docs/session-handoff.md` — Phase-7 documentation updates

### Tests run
- Backend: `.\backend\.venv\Scripts\python.exe -m pytest -q` → 46 passed (1 pre-existing StarletteDeprecationWarning)
- Compile: `.\backend\.venv\Scripts\python.exe -m compileall .\backend\app` → clean
- Phase-6 real-paper baseline re-run → counts unchanged (171 / 51 / 35)

### Current state
- Branch: `main`; base commit: `36cb002`
- Phase-6 implementation files modified: the three parser/test files listed above
- Phase-7 documentation files modified: the two docs files listed above
- Nothing staged, committed or pushed

### Current parser support
- Numbered bracket, numbered period, numbered parenthesis, hanging marker, conservative author-year, per-entry DOI

### Known limitations
- No unlabelled References-section detection (arXiv-style preprints)
- Abstract boundary noise on some papers (PLOS front matter, Keywords block)
- No title/authors/keywords/sections in the schema
- No OCR or scan-quality warning; hidden OCR may be accepted as ordinary text

### Next recommended task
- Improve abstract boundary cleanup:
  - PLOS front-matter/citation/funding noise
  - Keywords-block leakage

### Dependencies or blockers
- None.

### Commit / push
- Commit: none (not requested)
- Pushed to main: No

### Verification commands
```powershell
cd backend
.\.venv\Scripts\python.exe -m pytest -q
cd ..
git status --short
```

---

## 2026-08-08 — Frontend & Deployment Engineer

### Role
Frontend & Deployment Engineer

### Work completed
- Built the PDF upload and mock report flow (`/analyser` route).
- Added drag-and-drop `PDFUploader` component with client-side file size (<10MB) and type validation.
- Built `AnalysisProgress` UI to simulate backend stage progression.
- Built `ReportDashboard` to render the `sample-responses/sample-paper-analysis.json` data.
- Handled empty, error, and partial-result states visually.
- Added strict type interfaces matching `docs/api-contract.md`.
- Added a `mock-api.ts` file that uses the sample JSON response and simulates processing delay.
- Ensured mandatory "human review" disclaimers are visible on the dashboard.

### Files changed
- `docs/project-status.md`
- `frontend/app/page.tsx`
- `frontend/app/analyser/page.tsx` (NEW)
- `frontend/components/upload/PDFUploader.tsx` (NEW)
- `frontend/components/progress/AnalysisProgress.tsx` (NEW)
- `frontend/components/report/ReportDashboard.tsx` (NEW)
- `frontend/lib/api-types.ts` (NEW)
- `frontend/lib/mock-api.ts` (NEW)
- `frontend/lib/sample-paper-analysis.json` (NEW)

### Tests run
- `npm run lint` — Pass
- `npm run build` — Pass

### Current state
- The frontend `/analyser` route provides a working mock flow from upload to report display.
- Latest base commit: `a1fa308`

### Next recommended task
- Integrate the real extraction endpoint using an environment-based backend URL and coordinate CORS with the Technical Lead.

### Dependencies or blockers
- Needs the live backend URL environment variables and CORS headers to be opened on the FastAPI side.

### Commit / push
- Commit: None
- Pushed to main: No

---

## 2026-08-08 — Frontend & Deployment Engineer (API Integration)

### Role
Frontend & Deployment Engineer

### Work completed
- Configured `.env.local` to point to the FastAPI backend (`NEXT_PUBLIC_API_URL`).
- Replaced the `mock-api.ts` file with a real `api.ts` client that uses `fetch` and `FormData` to POST PDFs.
- Confirmed CORS is correctly set up in the backend `config.py` for `http://localhost:3000`.
- Merged the real backend extraction result with placeholder blocks for pending ML/Citation modules so the UI remains stable.
- Updated `app/analyser/page.tsx` to use the real API client.

### Files changed
- `frontend/.env.local` (NEW)
- `frontend/lib/api.ts` (NEW)
- `frontend/app/analyser/page.tsx`
- `docs/project-status.md`

### Tests run
- `npm run lint` — Pass
- `npm run build` — Pass

### Current state
- The frontend `/analyser` route successfully communicates with the live backend for PDF extraction.

### Next recommended task
- The Technical Lead or Citation Integrity Engineer should build the next backend module, as the frontend is now fully wired up for the MVP extraction.

### Dependencies or blockers
- None.

### Commit / push
- Commit: Frontend API Integration and UI Components
- Pushed to main: Yes

---

## 2026-08-12 — Technical Lead, Backend & PDF Processing Engineer (Phase 1)

### Role
Technical Lead, Backend & PDF Processing Engineer

### Work completed
- Phase 1 mini-phases, executed in isolated sub-phases and now fully verified:
  - **Title extraction:** conservative `_detect_title` on front matter before the Abstract/Summary heading; first plausible title line plus wrapped-title continuation; rejects metadata/decorative labels, headers/footers, DOI/URL/email/ORCID/copyright tokens, digit-led and prose lines; `null` + `TITLE_UNCERTAIN_WARNING` when uncertain, no warning for empty front matter. (9 new tests)
  - **Author extraction:** `_detect_authors` anchored on the title block; supports single/comma/`and`/`&`/multi-line/`Doe, J. R.` forms; strips superscripts (`Doe1,2`); ignores emails, URLs, DOIs, ORCID, affiliation-numbered lines, departments/universities/institutes/hospitals/labs; order preserved, case-insensitive dedupe; `[]` never fabrication; `AUTHOR_UNCERTAIN_WARNING` only for a non-empty unparseable region. (13 new tests)
  - **Abstract boundary cleanup:** abstract stops at bare headings and colon-prefixed labels `Keywords`/`Index Terms`/`Funding`/`Citation`/`Received`/`Accepted`; case-insensitive, whitespace-tolerant, colon-aware; structural matching so `Received wisdom suggests...` prose never truncates the abstract; references path unchanged (`stop_colon_pattern` default). (15 new tests)
  - **Schema + API + tests:** `PaperExtraction` exposes additive `title: str | None = None` and `authors: list[str] = Field(default_factory=list)`; `extract_paper` maps `parsed.title` / `parsed.authors` end to end; end-to-end API tests assert response values equal parser output. (3 new API tests)
  - **Docs + samples:** `docs/api-contract.md` and `sample-responses/sample-paper-analysis.json` updated with `title`/`authors`; `docs/project-status.md` and `docs/session-handoff.md` logged.
- No new dependencies; warn-not-fabricate behaviour preserved; no OCR/plagiarism/scoring work.

### Files changed
- `backend/app/services/pdf_parser.py` — title, authors, abstract boundary cleanup
- `backend/app/schemas/paper.py` — `title`/`authors` fields
- `backend/app/api/routes/papers.py` — field mapping
- `backend/tests/test_pdf_parser.py`, `backend/tests/test_papers_api.py` — tests (46 → 86)
- `docs/api-contract.md`, `docs/project-status.md`, `docs/session-handoff.md`
- `sample-responses/sample-paper-analysis.json`

### Tests run
- Backend: `.\backend\.venv\Scripts\python.exe -m pytest -q` → **86 passed** (1 pre-existing StarletteDeprecationWarning)
- Compile: `.\backend\.venv\Scripts\python.exe -m compileall -q app tests` → clean
- `git diff --check` → clean

### Current state
- Branch: `main`; base commit: `36cb002` (unchanged — Phase-1 work uncommitted)
- Phase-1 implementation, tests and documentation all present in the working tree; nothing staged, committed or pushed
- `docs/api-contract.md` and the sample response now match the schema

### Known limitations
- Title/authors anchored only when an `Abstract`/`Summary` heading exists
- `Received`/`Accepted`/etc. bare headings are exact-line matches; a same-line affiliation with an author name drops the whole line conservatively
- No keywords/index-terms or section-heading extraction yet; no page-number evidence tracking; two-column layouts not layout-aware; no OCR

### Next recommended task
- Keywords / index-terms extraction with regression tests, then section-heading detection and page-number/evidence tracking.

### Dependencies or blockers
- None. Phase-1 work is uncommitted; the team should coordinate commit/push of the whole Phase-1 set together (main-only workflow).

### Commit / push
- Commit: none (not requested)
- Pushed to main: No

---

## 2026-08-18 — Citation Integrity, Metadata Verification & Fake Review Engineer

### Role
Citation Integrity, Metadata Verification & Fake Review Engineer

### Work completed
- Built the local consistency rules engine `backend/app/services/consistency_checker.py` (no external API calls):
  - **Date consistency:** flags any cited reference whose year is after the paper's own year (`Received:`/`Accepted:`/`Published`/`Copyright`/`©` markers, most-recent-abstract-year fallback; check skipped when no paper year found)
  - **Figure reference consistency:** flags figures referenced in text but never defined (`Figure N`, `Fig. N`, `Fig N` vs colon definitions)
  - **Author name consistency:** flags listed authors whose last name never appears in the paper text
  - **Section structure consistency:** missing Abstract/Introduction/Conclusion/References reported as soft warnings (not flags)
  - **Reference number continuity:** flags `[N]` citations (incl. `[1, 3]`, `[1-3]` ranges) with no matching reference-list entry
  - Returns typed `ConsistencyReport` (flags, warnings, passed_checks, consistency_score 0.0–1.0)
- New schema `backend/app/schemas/consistency.py`: `ConsistencyFlag`, `ConsistencyReport`, `ConsistencyCheckRequest` (reuses `ReferenceEntry`/`PageText` from `schemas/paper.py`).
- New endpoint `POST /api/v1/integrity/check` in `backend/app/api/routes/integrity.py`, wired into `main.py`.
- `docs/api-contract.md`: added `keywords` to the `/papers/extract` response example and documented the new `/integrity/check` endpoint with request/response shapes.
- 13 new tests covering all five rules, scoring and endpoint wiring.

### Files changed
- `backend/app/services/consistency_checker.py` (NEW)
- `backend/app/schemas/consistency.py` (NEW)
- `backend/app/api/routes/integrity.py` (NEW)
- `backend/app/main.py` — router wiring
- `backend/tests/test_consistency_checker.py` (NEW)
- `docs/api-contract.md`, `docs/project-status.md`, `docs/session-handoff.md`

### Tests run
- Backend: `..\.venv\Scripts\python.exe -m pytest -q` → **110 passed** (13 new; 1 pre-existing StarletteDeprecationWarning)
- Compile: `..\.venv\Scripts\python.exe -m compileall -q app tests` → clean

### Current state
- Note: no `.git` directory exists in this workspace — Git workflow commands cannot run here.
- `POST /api/v1/integrity/check` is live; consistency flags are explainable screening signals, never fraud verdicts.
- Existing tests untouched; no new dependency added.

### Next recommended task
- Crossref DOI lookup service with mocked tests (timeout/429 paths), then OpenAlex title fallback and the metadata comparison output.

### Dependencies or blockers
- None for the consistency engine. Metadata-verification module depends on extracted DOI/title/author fields (already available from the parser).

### Commit / push
- Commit: none (not requested; also blocked by missing `.git`)
- Pushed to main: No

---

## 2026-08-18 — Technical Lead, Backend & PDF Processing Engineer (Report Generator)

### Role
Technical Lead, Backend & PDF Processing Engineer (orchestrator work)

### Work completed
- Built the final combiner `backend/app/services/report_generator.py`:
  - `generate_report(ReportInput) -> RiskReport`; citation/metadata/ML module outputs are optional placeholders (`None` allowed)
  - Scoring: high flag = 15 points, medium = 8, low = 3, capped at 100.0
  - Risk levels: 0–25 low, 26–50 medium, 51–75 high, 76–100 critical
  - Confidence: 0.0 with no modules; base 0.4 plus 0.15 per extra module, capped at 0.95; capped at 0.6 when only the consistency module contributes
  - Template summaries per score/level; `signals` carry source/severity/message/evidence/weight; `passed_checks`, `modules_used`, `generated_at` (UTC)
- New schemas `backend/app/schemas/report.py`: `ReportInput`, `RiskSignal`, `RiskReport` (reuses `ConsistencyReport`).
- New endpoints in `backend/app/api/routes/report.py`, wired into `main.py`:
  - `POST /api/v1/report/generate` — combines module outputs into a `RiskReport`
  - `POST /api/v1/analyze/full` — all-in-one: PDF upload → extraction → consistency rules → `RiskReport` (same upload validation as `/papers/extract`, reusing its helpers)
- 16 new tests; full backend suite 126/126 passing; no new dependency; existing tests untouched.

### Files changed
- `backend/app/services/report_generator.py` (NEW)
- `backend/app/schemas/report.py` (NEW)
- `backend/app/api/routes/report.py` (NEW)
- `backend/app/main.py` — router wiring
- `backend/tests/test_report_generator.py` (NEW)
- `docs/api-contract.md`, `docs/project-status.md`, `docs/session-handoff.md`

### Tests run
- Backend: `..\.venv\Scripts\python.exe -m pytest -q` → **126 passed** (16 new; 1 pre-existing StarletteDeprecationWarning)
- Compile: `..\.venv\Scripts\python.exe -m compileall -q app tests` → clean

### Current state
- `POST /api/v1/report/generate` and `POST /api/v1/analyze/full` live; `analyze/full` is the endpoint the frontend will call for one-request analysis.
- Risk report remains an explainable screening signal — no fraud verdicts.

### Next recommended task
- Citation Integrity: Crossref DOI lookup service with mocked tests (timeout/429 paths), then wire `citation_results`/`metadata_results`/`ml_results` into the report generator so `modules_used` grows and confidence can exceed 0.6.

### Dependencies or blockers
- None. Report generator accepts the not-yet-built module outputs as `None` by design.

### Commit / push
- Commit: none (not requested)
- Pushed to main: No

---

## 2026-08-18 — Frontend & Deployment Engineer (UI polish + VeriScholar branding)

### Role
Frontend & Deployment Engineer

### Work completed
- Rebranded the website to **VeriScholar** (per user decision; frontend only — backend service name and docs still say Mini Project):
  - `frontend/app/layout.tsx`: metadata title "VeriScholar" + description
  - `frontend/app/page.tsx`: header with logo mark, hero (badge, gradient headline, CTAs), feature cards with honest Live / "Coming soon" tags, disclaimer footer
  - `frontend/app/analyser/page.tsx`: sticky blurred header with VeriScholar branding
- Made analyser progress stages honest: removed the fake "Verifying metadata with Crossref…" and "Running ML models…" steps (those modules are not wired yet); stages now Upload → Extract → Generate, and `frontend/lib/api.ts` emits matching stage strings
- Polished `ReportDashboard`: analysis ID displayed, title/authors added to Document Details, module status rows now show plain-language module descriptions; status badges got dots
- Updated `frontend/lib/api-types.ts` `PaperData` with `title`, `authors`, `keywords` (fields the backend already returns)
- Analyser hero copy corrected (no longer claims citation verification runs)

### Files changed
- `frontend/app/layout.tsx`
- `frontend/app/page.tsx`
- `frontend/app/analyser/page.tsx`
- `frontend/components/progress/AnalysisProgress.tsx`
- `frontend/components/report/ReportDashboard.tsx`
- `frontend/lib/api.ts`
- `frontend/lib/api-types.ts`
- `docs/project-status.md`, `docs/session-handoff.md`

### Tests run
- Frontend: `npm run lint` → clean; `npm run build` → success (3 static routes: `/`, `/_not-found`, `/analyser`)
- Backend untouched in this session (no tests rerun needed)

### Current state
- Website branded VeriScholar in the UI; Review Detector / Methodology remain `#` placeholders (team decision pending)
- Frontend still calls `/papers/extract` and merges pending module blocks; `/analyze/full` exists in the backend and is the next integration target

### Next recommended task
- Wire the analyser to `POST /api/v1/analyze/full` and render the real `RiskReport` (risk score, level, confidence, summary, signals) in the dashboard.

### Dependencies or blockers
- None. Backend `/analyze/full` endpoint is already live and tested.

### Commit / push
- Commit: none (not requested)
- Pushed to main: No

---

## 2026-08-19 — Research Paper ML & Dataset Engineer

### Role
Research Paper ML & Dataset Engineer

### Work completed
- Phase 1 — rule-based NLP text feature extraction (`feature_extractor.py`)
  - Group 1 readability (Flesch reading ease, Flesch-Kincaid grade, Gunning fog, ARI) via textstat
  - Group 2 vocabulary (unique_word_ratio, avg_word_length, rare_word_ratio)
  - Group 3 sentence structure (avg_sentence_length, sentence_length_variance, totals)
  - Group 4 section consistency (abstract-to-body Jaccard similarity, section_style_variance over 4 sentence chunks)
  - Group 5 academic writing (citation_density per 1000 words, passive_voice_ratio, hedge_word_ratio)
  - Typed `TextFeatures` Pydantic schema in `backend/app/schemas/ml.py`
  - NLTK data bootstrap (`punkt`, `punkt_tab`, `averaged_perceptron_tagger`) with offline-safe regex tokenizer fallback
  - Edge cases: empty/whitespace text, single-sentence variance, empty abstract, division-by-zero, short text under 4 chunks, textstat failures
  - Added `nltk` + `textstat` to `backend/requirements.txt` and installed them in the Python 3.13 environment
- Wired nothing into `report_generator` — `ml_results` placeholder unchanged, no API contract change

### Files changed
- `backend/requirements.txt` (added `nltk>=3.9.0`, `textstat>=0.7.4`)
- `backend/app/schemas/ml.py` (new — `TextFeatures`)
- `backend/app/services/ml/__init__.py` (new package)
- `backend/app/services/ml/feature_extractor.py` (new)
- `backend/tests/test_feature_extractor.py` (new — 17 tests)
- `docs/project-status.md`

### Tests run
- `python -m pytest` (Python 3.13) → **143 passed** (126 existing + 17 new), 1 pre-existing Starlette deprecation warning
- All new tests local-only: no network calls, no file reads

### Current state
- ML text feature extraction Phase 1 complete and green
- Still nothing produces `ml_results`; risk scoring/thresholding from features is the next step

### Next recommended task
- Phase 2: threshold logic mapping `TextFeatures` to explainable ML signals (e.g. low abstract-to-body similarity, high section-style variance) plus a `ml_results` producer matching the shared `ml_analysis` contract.

### Dependencies or blockers
- None. Extraction schema (full_text, abstract, pages) already available from the Technical Lead.
- Note: two Python installs on this machine — the project env is Python 3.13 (`AppData\Local\Programs\Python\Python313`); `C:\Python314` does not have the project deps.

### Commit / push
- Commit: none (not requested)
- Pushed to main: No

---

## 2026-08-19 — Research Paper ML & Dataset Engineer (Phase 2)

### Role
Research Paper ML & Dataset Engineer

### Work completed
- Phase 2 — anomaly scoring engine `backend/app/services/ml/anomaly_scorer.py`
  - `analyze_text(features: TextFeatures) -> MLAnalysisResult` running all 10 threshold rules:
    uniform_sentence_length (<5.0 variance, medium), vocabulary_inflation (>0.80, medium), abstract_body_mismatch (<0.15, high), style_shifting (>50.0, high), missing_hedging (<0.002, low), missing_citations (<0.5/1000 words, medium), low_readability (<10, low), high_readability (>80, low), passive_voice_absent (<0.05, low), short_paper (<1000 words, high)
  - Scoring: high=15 / medium=8 / low=3, `ml_risk_contribution` capped at 100; confidence 0.3 (<500 words) / 0.5 (<1000) / 0.8 (>=1000); summary templates for 0 / 1-2 / 3-4 / 5+ signals; `passed_rules` for non-triggered rules
- New schemas in `backend/app/schemas/ml.py`: `MLSignal` (rule/severity/message/evidence/weight + points property) and `MLAnalysisResult` (signals, passed_rules, ml_risk_contribution, confidence, features_used, summary)
- Report generator integration:
  - `ReportInput.ml_results` changed from `Optional[dict]` to `Optional[MLAnalysisResult]` (`backend/app/schemas/report.py`)
  - `generate_report`: ML signals converted to `RiskSignal(source="ml")`, `ml_risk_contribution` added to the total score before the 100 cap, `passed_rules` appended to `passed_checks`, `"ml"` in `modules_used`
  - Confidence: only ML ran → ML confidence; consistency + ML → `min(0.85, avg(consistency_score, ml confidence))`; consistency-only path unchanged (still ≤0.6)
- `docs/api-contract.md` updated: `/report/generate` request example now shows a full `MLAnalysisResult`, and scoring/confidence rules documented

### Files changed
- `backend/app/schemas/ml.py` (added `MLSignal`, `MLAnalysisResult`)
- `backend/app/services/ml/anomaly_scorer.py` (new)
- `backend/app/schemas/report.py` (`ml_results` type change)
- `backend/app/services/report_generator.py` (ML wiring + confidence logic)
- `backend/tests/test_anomaly_scorer.py` (new — 33 tests: 10 rule triggers + non-triggers, contributions, confidence tiers, summaries, completeness, report-generator integration)
- `docs/api-contract.md`, `docs/project-status.md`, `docs/session-handoff.md`

### Tests run
- `python -m pytest` (Python 3.13) → **176 passed** (143 existing + 33 new), 1 pre-existing Starlette deprecation warning
- No existing tests modified

### Current state
- ML module produces `MLAnalysisResult` and the report generator consumes it; `ml_results` is still not populated by any endpoint (extractor + scorer not yet chained end to end)
- Notes: rules 7 and 8 (low/high readability) are mutually exclusive, so the maximum achievable real contribution is 78.0 — the 100 cap is defensive

### Next recommended task
- Chain `extract_features` → `analyze_text` and expose the result (either a new `/api/v1/ml/analyze` endpoint or wiring into `/analyze/full`), coordinated with the Technical Lead.

### Dependencies or blockers
- None. `ReportInput.ml_results` type change is a coordinated schema change — documented in `docs/api-contract.md`; frontend currently sends `ml_results: null` so it is unaffected.

### Commit / push
- Commit: none (not requested)
- Pushed to main: No

---

## 2026-08-19 — Research Paper ML & Dataset Engineer (Phase 3)

### Role
Research Paper ML & Dataset Engineer

### Work completed
- Phase 3 — wired the ML module into the live pipeline
  - `backend/app/services/ml/ml_pipeline.py` — `run_ml_analysis(full_text, abstract, pages)` orchestrator chaining `extract_features` → `analyze_text`; catches any exception and returns a safe fallback `MLAnalysisResult` (empty signals/passed_rules, 0.0 contribution, 0.0 confidence, summary "ML analysis unavailable due to an internal error.") so the pipeline never crashes on ML failure
  - New standalone endpoint `POST /api/v1/ml/analyze` (`backend/app/api/routes/ml.py`) taking `MLAnalysisRequest` (`full_text` required, `abstract`/`pages` optional) and returning `MLAnalysisResult`; registered in `main.py`
  - `/api/v1/analyze/full` now runs extraction → consistency → ML → report; `ml_results` is populated with the ML analysis (full_text built by joining page texts), so `modules_used` is now `["consistency", "ml"]`
  - No new dependencies
- `docs/api-contract.md` updated: new `/ml/analyze` endpoint spec, `/analyze/full` response example showing `modules_used: ["consistency", "ml"]` and an ML signal

### Files changed
- `backend/app/services/ml/ml_pipeline.py` (new)
- `backend/app/api/routes/ml.py` (new)
- `backend/app/schemas/ml.py` (added `MLAnalysisRequest`)
- `backend/app/api/routes/report.py` (ML wired into `/analyze/full`)
- `backend/app/main.py` (registered ML router)
- `backend/tests/test_ml_pipeline.py` (new — 6 tests), `backend/tests/test_ml_endpoint.py` (new — 6 tests), `backend/tests/test_analyze_full_ml.py` (new — 3 tests)
- `backend/tests/test_report_generator.py` (updated 1 existing assertion — see note)
- `docs/api-contract.md`, `docs/project-status.md`, `docs/session-handoff.md`

### Tests run
- `python -m pytest` (Python 3.13) → **191 passed** (176 prior + 15 new), 1 pre-existing Starlette deprecation warning
- Confirmed `/analyze/full` returns `"ml" in modules_used` with source="ml" signals and positive confidence

### Current state
- ML is now a first-class pipeline stage: standalone endpoint + integrated into `/analyze/full`
- Note: one existing test was updated — `test_analyze_full_endpoint_accepts_pdf` previously asserted `risk_score == 0.0`/`risk_level == "low"`; with ML wired in the sample paper now scores > 0, so the assertion now checks `risk_score >= 0.0` and `"ml" in modules_used`. This was a required, coordinated change caused by the intended behaviour change, not a regression.

### Next recommended task
- Frontend: display ML signals in the report dashboard (reuse the module-status rows); optional threshold tuning on real sample papers.

### Dependencies or blockers
- None. `ReportInput.ml_results` schema change is already coordinated; frontend currently sends `ml_results: null` in `/report/generate` and is unaffected.

### Commit / push
- Commit: none (not requested)
- Pushed to main: No
