# Project Status

Living document. Update it at the end of every working session.

## Project summary

- **Project name:** Mini Project
- **Primary module:** Research Paper Integrity Risk Detector
- **Secondary module:** Fake Review Detector
- **Current stage:** Reference-extraction milestone complete; abstract cleanup is the next module improvement.
- **Last known stable commit:** `36cb002` — Fix npm dependency vulnerabilities via postcss and sharp overrides
- **Test status:** Backend 46/46 passing; frontend lint and production build passing

> The commit hash above is checked against Git history on every session start. If `git log` shows a newer commit, treat that newer commit as the latest and update this document.

## Completed foundation

### Backend

- FastAPI application (Python 3.11+, Pydantic, environment-driven config, CORS, uniform error responses)
- `GET /api/v1/health`
- `POST /api/v1/papers/extract` with file validation (missing/empty → 400, non-PDF → 415, oversized → 413, corrupt/password-protected/no-text → 422)
- PDF parser: page-wise text, combined raw text, DOI candidates with punctuation cleanup, best-DOI selection, basic abstract detection, references-section detection, structured reference splitting (numbered with hanging markers, conservative author-year, per-entry DOI, warnings instead of fabricating entries)
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

## Current overall milestone

```text
Reliable structured reference extraction complete; abstract boundary cleanup is the next module improvement.
```

## Per-role status

| Role | Completed | Current priority | Next deliverable | Dependencies | Known blockers |
| --- | --- | --- | --- | --- | --- |
| Technical Lead, Backend & PDF Processing Engineer | FastAPI app, health + extract endpoints, parser, tests, API contract; five-paper baseline, ground truth and parser comparison; structured reference extraction (numbered, hanging markers, conservative author-year, per-entry DOI) | Improve abstract boundary cleanup (PLOS front-matter/citation/funding noise; Keywords-block leakage) | Clean abstract sections on real papers with regression tests | None (parser runs standalone) | None |
| Research Paper ML & Dataset Engineer | Directory skeleton (`ml/`), no code yet | Finalise labels; create an initial dataset pipeline; build a TF-IDF Logistic Regression baseline | A reproducible baseline notebook with dataset summary and evaluation metrics | Extraction schema from Technical Lead for features | None |
| Citation Integrity, Metadata Verification & Fake Review Engineer | No code yet | Build Crossref DOI lookup; build OpenAlex title fallback; define metadata comparison output; test known valid and mismatched citations | A metadata-verification service that returns matched fields, mismatches, confidence and warnings | Extracted DOI/title/author fields from parser | None |
| Frontend & Deployment Engineer | Next.js scaffold, landing page, placeholder nav | Build the PDF upload screen; build analysis-progress UI; build a mock report using the existing sample response; do not wait for all backend modules | A working frontend flow from PDF selection to mock extraction/report display | `sample-responses/sample-paper-analysis.json` | None |

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
