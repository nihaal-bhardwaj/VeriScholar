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
git diff --stat
```
