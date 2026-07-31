# Role Playbook — Technical Lead, Backend & PDF Processing Engineer

## Role purpose

Own the FastAPI backend, PDF upload/extraction, research-paper structure parsing, and the future orchestrator that combines all analysis modules into the final risk report. Also coordinate integration across modules.

## Owned directories

```text
backend/app/api/
backend/app/core/
backend/app/schemas/
backend/app/services/pdf_parser.py
backend/tests/
docs/api-contract.md
```

May later create:

```text
backend/app/services/orchestrator/
backend/app/services/scoring/
backend/app/database/
```

## Files requiring coordination

- `docs/api-contract.md` — shared with all roles; any response-shape change requires schema + docs + tests + sample-response updates and frontend coordination.
- `docs/project-status.md` and `docs/session-handoff.md` — update after every session.
- The shared future analysis contract (see `docs/api-contract.md` — combined analysis shape) is the integration contract every module must follow.

## Current state

- FastAPI app with health and extraction endpoints (see `docs/api-contract.md`).
- Initial parser extracts: pages, combined text, DOI candidates (with punctuation cleanup), best DOI, basic abstract, references section, numbered reference entries.
- 21 passing backend tests.
- Title, authors, keywords, section detection and evidence locations are not yet extracted.

## Immediate next task

Test and improve the PDF parser.

## Ordered task backlog

1. Create a documented test matrix using several academic PDF styles.
2. Extract title with confidence and warnings.
3. Extract authors conservatively.
4. Extract keywords/index terms.
5. Identify section headings.
6. Extract introduction, methodology, results, discussion and conclusion.
7. Attach page numbers or evidence locations where practical.
8. Improve reference parsing without fabricating entries.
9. Stabilise the typed extraction schema.
10. Prepare future analysis-orchestrator interfaces.

Advanced scoring, database history and full integration come later — do not build them yet.

## Input contract

Multipart form upload `file` (PDF) → `POST /api/v1/papers/extract`.

## Output contract

Current extraction response: `docs/api-contract.md` (`/papers/extract` section). The expected paper structure should eventually support fields such as:

```json
{
  "filename": "paper.pdf",
  "page_count": 8,
  "title": {
    "value": "Example title",
    "confidence": 0.86,
    "page_number": 1
  },
  "authors": [],
  "doi": "10.xxxx/example",
  "keywords": [],
  "sections": {
    "abstract": "",
    "introduction": "",
    "methodology": "",
    "results": "",
    "discussion": "",
    "conclusion": ""
  },
  "references": [],
  "warnings": []
}
```

This is a target contract, not permission to break the existing endpoint without updating schemas, tests, API documentation and the sample response together.

## Acceptance criteria

- Every new extraction field is added to the Pydantic schema, the API docs, tests and `sample-responses/` in the same change.
- New parser capabilities are covered by tests using programmatically generated PDFs (no copyrighted papers).
- Missing sections produce `warnings`, never fabricated content.
- Page-level evidence (page numbers) is preserved where practical.

## Required tests

```bash
cd backend
python -m pytest
```

Add a test with every meaningful parser feature. Keep tests offline.

## Common mistakes to avoid

- Breaking the API contract for a future feature — update schema, docs, tests and sample together.
- Claiming parser output is accurate without testing against real layouts.
- Fabricating references or sections when detection fails (warn instead).
- Silently rewriting ML, citation or frontend modules.

## Handoff requirements

Update `docs/project-status.md` (completed/current/next, blockers, tests run, API changes) and append to `docs/session-handoff.md` (bottom of file).

## Definition of done

- Parser change works on multiple tested layouts.
- Tests added and full suite green.
- API contract, sample response and docs updated in the same commit.
- Status and handoff documents updated.
