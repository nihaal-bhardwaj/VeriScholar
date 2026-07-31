# Project Scope

## Purpose

VeriScholar helps reviewers and students screen research papers for integrity-risk signals. It never declares a paper "fake"; it produces explainable screening reports that a human can act on.

## MVP scope (current)

| Item | Status |
| --- | --- |
| PDF upload via multipart form data | Implemented |
| Structured extraction (pages, text, DOI, abstract, references) | Implemented |
| Metadata verification (journal, authors, publisher via Crossref/OpenAlex) | Later |
| Citation verification (references resolve to real works) | Later |
| Research-paper ML risk signals | Later |
| Consistency rules (dates, claims, figures vs text) | Later |
| Explainable risk report | Later |
| Fake-review detector (secondary module) | Later |

## Explicitly excluded from the MVP

The following are **out of scope** for the MVP and will not be claimed as capabilities:

- Full internet plagiarism detection
- Proof of fabricated experiments
- Reliable AI-authorship detection
- Advanced image-manipulation forensics
- Scientific truth verification (whether a paper's conclusions are correct)

Any analysis output must be presented as a **screening signal** with evidence and uncertainty, never as a verdict.

## Design principles

- Modular: each future module (ML, metadata, citations, consistency) plugs into the shared analysis contract.
- No fake analysis: modules that are not implemented report `status: "pending"` rather than fabricated results.
- Typed, readable code; environment-driven configuration.
