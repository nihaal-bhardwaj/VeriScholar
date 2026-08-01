# Role Manual — Citation Integrity, Metadata Verification & Fake Review Engineer

## 1. Role name

- **Official role name:** Citation Integrity, Metadata Verification & Fake Review Engineer
- **Short role name:** Citation Integrity Engineer
- **Purpose:** Build the modules that verify a paper's metadata against external scholarly APIs, check citations reference by reference, apply structural and numerical consistency rules, and build the secondary fake-review detector. Results must be typed, explainable and honest about unresolved checks.

## 2. Position in the system

```text
PDF upload
→ PDF extraction           (Technical Lead, Backend & PDF Processing Engineer)
→ Metadata and citation checks  ← this role owns this stage
→ ML analysis                    (Paper ML Engineer)
→ Combined result                (Technical Lead orchestrates)
→ Frontend report                (Frontend Engineer)
```

This role consumes the structured extraction output (DOI, title, authors, year, references) and produces the `metadata_analysis`, `citation_analysis` and `consistency_analysis` blocks of the shared combined contract in `docs/api-contract.md`. The fake-review detector shares the explainability rules of the paper ML module.

## 3. Main responsibilities

### Core responsibilities

- Verify the paper's metadata (title, authors, publication year, venue) against Crossref, with OpenAlex as fallback.
- Normalise DOIs before any lookup or comparison.
- Check retraction, correction and publication-update status from official sources.
- Verify each extracted reference against the APIs and classify it as verified, probable-match, mismatch, unresolved or retracted.
- Detect duplicate references, invalid DOIs and future publication years.
- Preserve the original reference text as evidence in every per-reference result.
- Apply structural and numerical consistency rules (reference counts, numbering, page and section sanity).
- Build the fake-review dataset and a TF-IDF + Logistic Regression / Linear SVM baseline classifier with honest evaluation.
- Never fabricate a scholarly match; unresolved is a valid honest state.

### Documentation responsibilities

- Keep the `metadata_analysis`, `citation_analysis` and `consistency_analysis` shapes in `docs/api-contract.md` in sync (coordinated changes only).
- Update `docs/project-status.md` and append to `docs/session-handoff.md` after meaningful work.

### Testing responsibilities

- Mocked external-API tests for every integration (no internet during tests).
- Unit, integration and edge-case tests as described in section 13.

## 4. Owned files and directories

### Primary ownership

```text
backend/app/services/metadata/
backend/app/services/citations/
backend/app/services/integrity_rules/
backend/app/services/review_detector/
backend/tests/
```

### Shared files requiring coordination

- `docs/api-contract.md` — the `metadata_analysis`, `citation_analysis` and `consistency_analysis` blocks define the output shapes.
- The extraction schema (Technical Lead) — accept extracted data (DOI, title, authors, references); do not redesign the PDF parser.
- `backend/requirements*.txt` — document any dependency additions.
- Frontend must be informed of new fields they need to display.

### Other members' areas (do not casually edit)

```text
backend/app/ (api/, core/, schemas/, pdf_parser.py) → Technical Lead
backend/app/services/paper_ml/ and ml/ → Paper ML Engineer
frontend/ → Frontend Engineer
```

## 5. Programming languages

| Language | Why it is needed | Expected level |
| --- | --- | --- |
| Python | All services, API clients and tests | Advanced |
| JSON | External-API payloads, typed responses, contract examples | Intermediate |
| Markdown | Documentation and contract updates | Basic |
| SQL | Optional later persistence and report queries | Basic (optional) |

## 6. Technologies and libraries

| Technology | Purpose in VeriScholar | Required or optional |
| --- | --- | --- |
| httpx | External-API calls with timeouts and retries | Required |
| Pydantic | Typed request/response schemas for all results | Required |
| Pytest | Test suite with mocked API clients | Required |
| JSON | Parsing and building Crossref/OpenAlex payloads | Required |
| difflib / rapidfuzz | Title and author similarity (normalised comparison) | Required |
| Regular expressions | DOI validation and normalisation, year extraction | Required |
| scikit-learn | Fake-review classifier: TF-IDF, Logistic Regression, LinearSVC, metrics | Required |
| joblib | Saving/loading the fake-review pipeline | Required |
| pandas | Fake-review dataset cleaning and summaries | Required |
| NumPy | Evaluation math | Required |
| Matplotlib | PR curve and confusion-matrix plots for the classifier | Required |
| imbalanced-learn | Optional resampling for the fake-review classifier | Optional |

## 7. Knowledge requirements

### Must understand

- DOI syntax and normalisation: case, whitespace, `https://doi.org/` prefixes, check-digit validity for invalid-DOI detection.
- Crossref REST API: `/works/{doi}` lookup, title search via query parameters, JSON response fields (title, author, published/issued year, container-title/venue, relation/update information).
- OpenAlex `works` endpoint as fallback and when to prefer it (Crossref miss, rate limiting).
- String-similarity techniques: tokenisation, case/punctuation/stopword normalisation, similarity thresholds for title and author matching.
- Retraction taxonomy: retraction notices, corrections (erratum), expressions of concern, publication updates — and that retraction status is a fact reported from the source, not a judgment about fraud.
- HTTP timeouts, retry policies with backoff, `429` rate-limit handling and readable failure messages.
- The per-reference states and when each applies: verified, probable-match, mismatch, unresolved, retracted.
- Pydantic v2 output models and how to keep contract fields in sync.
- Class imbalance and honest evaluation (precision, recall, F1, PR-AUC) for the fake-review classifier.

### Should learn during development

- Field-level evidence formatting: every mismatch carries (field, extracted value, official value).
- Reference-parsing realities: missing DOIs in extracted references, partial or malformed entries.
- Crossref/OpenAlex metadata quirks (missing years, multiple titles, venue name variations).
- Consistency rules design: reference counts vs extracted bibliography, numbering gaps, duplicate detection heuristics.

### Optional advanced knowledge

- Retraction Watch database integration for retraction-reason context (subject to source availability).
- ORCID iD-based author matching.
- Embedding-based similarity for title matching.

## 8. Official documentation and sources

| Source | What to learn or obtain from it | Priority |
| --- | --- | --- |
| [Crossref REST API documentation](https://www.crossref.org/documentation/retrieve-metadata/rest-api/) — verified | DOI lookup, title search, metadata fields, update/relation information | Required |
| [OpenAlex documentation](https://docs.openalex.org/) — verified (docs moved to developers.openalex.org; the API now requires a free key) | Works lookup and fallback metadata | Required |
| [DOI Foundation — doi.org](https://www.doi.org/) — verified | DOI structure, normalisation, the DOI Handbook | Required |
| [httpx documentation](https://www.python-httpx.org/) — verified | Client timeouts, retries, error handling | Required |
| [Pydantic documentation](https://docs.pydantic.dev/latest/) — verified | Typed output models and validation | Required |
| [pytest documentation](https://docs.pytest.org/en/stable/) — verified | Fixtures, parametrization, mocking patterns | Required |
| [scikit-learn documentation](https://scikit-learn.org/stable/) — verified | TF-IDF, Logistic Regression, LinearSVC, metrics | Required |
| [ORCID documentation](https://info.orcid.org/documentation/) — verified | Optional author-matching via ORCID iD | Optional |
| Retraction Watch database — retractiondatabase.org — **URL could not be verified; confirm before adding** | Retraction records and reasons | Recommended |

## 9. Inputs received

- **Source:** Technical Lead's extraction pipeline via `docs/api-contract.md` (`/papers/extract` response).
- **Fields:** `doi`, `doi_candidates`, `abstract`, `references` (numbered entries with extracted DOIs where present), title and authors when extraction provides them.
- **Missing-data behaviour:** services must tolerate absent DOIs, absent abstracts and partial reference entries — produce `unresolved`/`warnings`, never fabricated values.
- **External data:** Crossref and OpenAlex responses are live inputs; treat them as untrusted, validate and normalise everything.

## 10. Outputs produced

### Metadata verification block

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

- `match_status` may be `matched`, `mismatched` or `unresolved`. Unresolved is a valid honest state — never fabricate a match.
- `mismatches` entries carry field-level evidence: field, extracted value, official value.
- `source` records which API answered (`crossref`, `openalex`) or `none`.

### Citation analysis block (per-reference verification)

- Each reference is classified as one of: `verified`, `probable-match`, `mismatch`, `unresolved`, `retracted`.
- Every reference result preserves the original extracted reference text as evidence.
- Aggregates: `verified` and `unresolved` counts matching the `citation_analysis` contract (`status`, `verified`, `unresolved`, `warnings`).
- Duplicate references, invalid DOIs and future publication years are reported per reference with evidence.
- Retracted references are reported as a fact from the source, with source and date when known — never as proof of fraud.

### Consistency analysis block

- Structural and numerical consistency rules output: `status` and `warnings`, e.g. reference-count mismatches, numbering gaps, page-range anomalies, section-number inconsistencies.

### Fake-review detector output

- Same explainable shape as the paper ML module: status, risk probability, risk level (human-review wording), explainable signals, model version, limitations.

- **Consumer:** Technical Lead (orchestrator) and Frontend Engineer (report display).
- **Contract:** `docs/api-contract.md` — any new field requires coordinated schema, tests, docs, sample-response and frontend updates.

## 11. Things to implement

### Metadata verification

1. Crossref lookup by DOI (`/works/{doi}`).
2. Crossref lookup by title when DOI is absent (query-based search).
3. OpenAlex fallback when Crossref misses or is rate-limited.
4. DOI normalisation before any lookup or comparison.
5. Metadata comparison: title similarity, author matching, publication-year and venue comparison.
6. Retraction, correction and publication-update checks with status, source and date when known.
7. Typed metadata-verification result with field-level evidence and confidence.

### Citation verification

8. Reference-by-reference verification against the APIs.
9. Classification into verified, probable-match, mismatch, unresolved and retracted states.
10. Duplicate-reference detection.
11. Invalid DOI detection (syntax and check-digit rules).
12. Future publication-year detection.
13. Preservation of the original reference text as evidence in every result.

### Consistency rules

14. Structural and numerical consistency rules (reference counts, numbering, page and section sanity) producing explainable warnings.

### Fake-review detector

15. Fake-review dataset collection and annotation (with documented label definition).
16. TF-IDF + Logistic Regression baseline classifier.
17. TF-IDF + Linear SVM baseline classifier.
18. Honest evaluation: precision, recall, F1, PR-AUC, confusion matrix.
19. Exported pipeline following the same explainability rules as the paper ML module.

### Testing

20. Mocked external-API tests for every integration (no internet during tests).

## 12. Acceptance criteria

- External APIs are never called without timeouts, readable failure handling, rate-limit awareness and mocked tests.
- Every mismatch carries evidence (field, extracted value, official value).
- Retraction/correction/update checks return status with source and date when known.
- Unresolved lookups produce `warnings`, never fabricated matches or fabricated official metadata.
- Reference results preserve the original reference text and classify into the documented states.
- Duplicate, invalid-DOI and future-year cases are detected and reported per reference.
- Fake-review classifier follows the same explainability rules as the paper ML module and reports PR-AUC, not accuracy alone.
- Contract fields are documented in `docs/api-contract.md`; frontend informed of new fields.

## 13. Testing responsibilities

### Mocked external-API tests (no internet during tests)

- Valid DOI match (Crossref and OpenAlex paths).
- Mismatched title/year — field-level evidence present.
- Unresolved DOI — `warnings`, no fabricated match.
- Duplicate, invalid and future-year citations.
- Retraction/correction status return.
- Timeout, HTTP error and `429` rate-limit behaviour with readable failures.

### Unit tests

- DOI normalisation and invalid-DOI detection.
- Title-similarity and author-matching edge cases.
- Consistency-rule warnings.

### Fake-review classifier tests

- Dataset sanity checks and leakage-free deterministic splits.
- End-to-end TF-IDF + Logistic Regression / Linear SVM pipeline with recorded metrics.

### Commands

```bash
cd backend
python -m pytest
```

### Evidence to record

- Full test output (pass/fail counts).
- Sample metadata, citation and consistency results for one paper.
- Fake-review evaluation numbers and confusion matrix.

## 14. Dependencies on other roles

### Needs from other roles

- **Technical Lead, Backend & PDF Processing Engineer:** stable extraction schema with DOI, title, authors and references; agreement on the three contract blocks; orchestrator wiring; coordination for any contract change.
- **Paper ML Engineer:** shared ML conventions; coordinated feature overlap so the fake-review detector does not duplicate or contradict `ml_analysis`.
- **Frontend Engineer:** confirmation of which new fields need display.

### What other roles need from this role

- Typed `metadata_analysis`, `citation_analysis` and `consistency_analysis` output shapes for the orchestrator.
- Readable, honest statuses (`pending`/`unavailable` never fabricated as completed).
- Updated `docs/api-contract.md` when the contract changes.

### What may be mocked temporarily

- Metadata and citation module outputs may be stubbed by the Technical Lead while building the orchestrator — clearly labelled as mocks, never presented as real analysis.

### Contract changes requiring coordination

Any output-shape change requires: schema update, backend test update, `docs/api-contract.md` update, `sample-responses/` update, frontend coordination and a `docs/project-status.md` entry.

## 15. Common mistakes to avoid

- Calling external APIs without timeouts, retries, rate-limit handling or mocked tests.
- Reporting a match when only partial fields agree — record field-level matches and mismatches with evidence.
- Treating an unresolved lookup as a mismatch.
- Fabricating official metadata or scholarly matches to fill gaps.
- Renaming shared contract fields without coordination (see `docs/api-contract.md` rules).
- Redesigning the PDF parser to suit your needs.
- Ignoring the retraction taxonomy and honest-error context when wording results.
- Dropping the original reference text from per-reference output.
- Reporting only accuracy for the fake-review classifier; ignoring PR-AUC and false-negative review.
- Blocking the whole analysis when one API fails — fail readable and continue with `unresolved`/warnings.

## 16. Definition of done

- [ ] Metadata-verification service returns a typed result with evidence and confidence.
- [ ] Citation verification classifies references into the documented states and preserves original text.
- [ ] Consistency rules produce explainable warnings.
- [ ] Known valid, mismatched and unresolved citations tested with mocks; timeout/429 paths covered.
- [ ] Fake-review dataset documented; baseline classifiers trained and evaluated honestly.
- [ ] Contract fields documented in `docs/api-contract.md`; frontend informed.
- [ ] Full backend test suite green (`cd backend && python -m pytest`).
- [ ] `docs/project-status.md` updated; handoff entry appended to `docs/session-handoff.md`.
- [ ] No unrelated files modified.
- [ ] Commit/push status reported to the team.

## 17. Handoff requirements

After meaningful changes, report:

- Files changed and new endpoints.
- API changes and new contract fields (with `docs/api-contract.md` and `sample-responses/` updates).
- External integrations used and their failure modes.
- Tests run and results (mocked API coverage, classifier metrics).
- Known limitations (reference parsing quirks, API coverage gaps).
- Dependencies introduced and why.
- Blockers and dependencies.
- Whether changes were committed and pushed.

## 18. Viva knowledge

Be able to explain:

- The VeriScholar pipeline position of metadata/citation/consistency checks and why outputs are screening signals requiring human review.
- Crossref DOI lookup vs title search and when OpenAlex fallback triggers.
- DOI normalisation rules and invalid-DOI detection.
- How title, author, year and venue comparisons work and why field-level evidence matters.
- The five reference states and when each applies; why unresolved is honest.
- How retraction/correction/update checks report source and date without claiming fraud.
- How duplicate references, invalid DOIs and future publication years are detected.
- Why original reference text is preserved as evidence.
- Timeout, retry and rate-limit (`429`) handling for external APIs.
- Why mocked external-API tests are mandatory and how they are written.
- How the fake-review dataset is defined and why the classifier follows paper-ML explainability rules.
- TF-IDF + Logistic Regression vs TF-IDF + Linear SVM trade-offs and why PR-AUC matters.
- The three contract blocks and how contract changes are coordinated.
