# Role Playbook — Frontend & Deployment Engineer

## Role purpose

Own the Next.js user interface: PDF upload, analysis progress, research-integrity report dashboard, citation tables, evidence presentation, fake-review detector screen, error/partial states, and later deployment and demo assets.

## Owned directories

```text
frontend/
```

May update frontend-related sections of `docs/api-contract.md` when needed, but must not change backend response formats without coordination with the Technical Lead.

## Files requiring coordination

- `docs/api-contract.md` — the source of truth for response shapes you consume.
- `sample-responses/sample-paper-analysis.json` — the mock data for building UI before the backend is fully integrated.
- `docs/project-status.md` and `docs/session-handoff.md` — update after every session.

## Current state

- Next.js 16 + TypeScript + Tailwind CSS v4 scaffold.
- Landing page titled VeriScholar, one short description, placeholder navigation: Paper Analyser, Review Detector, Methodology.
- Lint and production build pass.
- No backend integration yet; no upload UI, progress UI or report UI.

## Immediate next task

Build the PDF upload and mock report flow.

## Ordered task backlog

1. Review `sample-responses/sample-paper-analysis.json`.
2. Build the Paper Analyser route.
3. Add drag-and-drop PDF selection.
4. Validate file type and size in the UI.
5. Build processing stages:
   - Uploading
   - Extracting
   - Verifying metadata
   - Checking citations
   - Running model
   - Generating report
6. Build an extraction-result view using mock JSON.
7. Build a report-dashboard shell.
8. Build a citation table shell.
9. Add empty, error and partial-result states.
10. Integrate the real extraction endpoint.
11. Build fake-review screen later.
12. Add printable/downloadable report later.
13. Deploy after the application is integrated and stable.

## Input contract

API responses defined in `docs/api-contract.md`:

- `GET /api/v1/health`
- `POST /api/v1/papers/extract`
- Future combined analysis contract (all modules report `pending` until implemented)

## Output contract

- UI must handle loading, errors and partial results.
- Frontend must use wording that does not imply proof of misconduct.
- Display a disclaimer such as:

```text
This analysis highlights signals that may require human review. It does not prove research misconduct.
```

## Acceptance criteria

- PDF upload validates file type and size before submitting.
- Processing stages render correctly (mock mode without backend).
- Extraction result and report shell render from mock JSON.
- Empty, error and partial-result states are handled, not crashes.
- Disclaimers and "human review" wording are visible on analysis screens.

## Required tests

```bash
cd frontend
npm run lint
npm run build
```

Add component/unit tests when a testing setup is added to the project.

## Common mistakes to avoid

- Claiming "This paper is fake" or risk scores presented as proof.
- Hard-coding backend response shapes not yet in `docs/api-contract.md`.
- Waiting for all backend modules before building UI (use mock JSON).
- Committing `node_modules`, `.next`, or API keys.
- Changing backend response formats without coordination with the Technical Lead.

## Handoff requirements

Update `docs/project-status.md` and append to `docs/session-handoff.md` (bottom of file), including pages/routes added, mock integration status, and any API fields needed from the backend.

## Definition of done

- Working frontend flow from PDF selection to mock extraction/report display.
- Lint and build pass.
- Empty/error/partial states handled.
- Status and handoff documents updated.
