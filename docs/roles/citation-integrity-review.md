# Role Playbook — Citation Integrity, Metadata Verification & Fake Review Engineer

## Role purpose

Build the modules that verify a paper's metadata against external scholarly APIs, check citations, apply integrity/consistency rules, and build the secondary fake-review detector. Results must be typed, explainable and honest about unresolved checks.

## Owned directories

```text
backend/app/services/metadata/
backend/app/services/citations/
backend/app/services/integrity_rules/
backend/app/services/review_detector/
backend/tests/
```

These directories do not exist yet and must be created as part of the work.

## Files requiring coordination

- `docs/api-contract.md` — `metadata_analysis`, `citation_analysis` and `consistency_analysis` blocks of the shared contract define your output shapes.
- Accept extracted data (DOI, title, authors, references) through the documented extraction schema — do not redesign the PDF parser.
- Frontend must be informed of new fields they need to display.

## Current state

- No code in these modules yet.
- Extracted paper fields available from the parser: DOI (best + candidates), abstract, references (numbered entries with DOIs), page texts.
- `docs/api-contract.md` defines the future combined analysis contract including `metadata_analysis` and `citation_analysis` blocks.

## Immediate next task

Implement metadata verification before full bibliography auditing.

## Ordered task backlog

1. Crossref lookup by DOI.
2. Crossref lookup by title when DOI is absent.
3. OpenAlex fallback.
4. Metadata normalisation.
5. Title similarity.
6. Author matching.
7. Publication-year and venue comparison.
8. Retraction or update status.
9. Typed metadata-verification result.
10. Reference-by-reference matching.
11. Duplicate, invalid DOI, future-year and unresolved rules.
12. Structural and numerical consistency rules.
13. Fake-review baseline classifier.
14. Mocked external-API tests.

## Input contract

Extracted paper data from `docs/api-contract.md` (`/papers/extract` response), especially `doi`, `doi_candidates`, `abstract`, and `references` entries.

## Output contract

Target metadata output:

```json
{
  "status": "completed",
  "match_status": "matched",
  "confidence": 0.93,
  "official_metadata": {},
  "mismatches": [],
  "warnings": [],
  "source": "crossref"
}
```

`match_status` may be `matched`, `mismatched` or `unresolved`. Unresolved is a valid honest state — never fabricate a match.

## Acceptance criteria

- External APIs are never called without timeouts, readable failure handling, rate-limit awareness and mocked tests.
- Every mismatch carries evidence (field, extracted value, official value).
- Retraction/correction checks return status with source and date when known.
- Unresolved lookups produce `warnings`, not fabricated matches.
- Fake-review classifier follows the same explainability rules as the paper ML module.

## Required tests

```bash
cd backend
python -m pytest
```

Every external-API integration needs mocked tests (no internet during tests). Include tests for: valid DOI match, mismatched title/year, unresolved DOI, duplicate/invalid/future-year citations, retraction status.

## Common mistakes to avoid

- Calling external APIs without timeouts/retries/mocks.
- Reporting a match when only partial fields agree — record field-level matches and mismatches.
- Treating an unresolved lookup as a mismatch.
- Renaming shared contract fields without coordination (see `docs/api-contract.md` rules).
- Redesigning the PDF parser to suit your needs.

## Handoff requirements

Update `docs/project-status.md` and append to `docs/session-handoff.md` (bottom of file), including API changes, endpoint names, and new contract fields.

## Definition of done

- Metadata-verification service returns typed result with evidence and confidence.
- Known valid and mismatched citations tested with mocks.
- Contract fields documented in `docs/api-contract.md`.
- Tests green; status and handoff documents updated.
