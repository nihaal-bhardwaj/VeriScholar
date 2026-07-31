# VeriScholar

VeriScholar is a research-integrity screening tool (college mini-project). It analyses uploaded research papers and product reviews for suspicious signals and produces explainable, evidence-backed reports.

**Important disclaimer:** VeriScholar reports screening signals, not proof of misconduct. The system does not declare a paper "fake" — it surfaces risk indicators (metadata gaps, citation issues, formatting anomalies) so a human can make an informed judgement.

## Modules

1. **Research Paper Integrity Risk Detector (primary)** — extracts structure from PDFs, later verifies metadata and citations, runs ML-based anomaly detection and produces an explainable risk report.
2. **Fake Review Detector (secondary)** — flags likely fake or bot-generated product reviews.

## Repository structure

```text
verischolar/
├── backend/          FastAPI application (PDF parsing, extraction API)
├── frontend/         Next.js + TypeScript + Tailwind application
├── ml/               Datasets, notebooks, saved models (future work)
├── docs/             Scope, API contract, team workflow, architecture
├── sample-papers/    Placeholder for permissively licensed sample PDFs
└── sample-responses/ Example API responses
```

## Backend setup

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate          # Windows
pip install -r requirements-dev.txt
cp ../.env.example .env         # adjust as needed
uvicorn app.main:app --reload
```

The API runs at `http://localhost:8000`, interactive docs at `http://localhost:8000/docs`.

## Frontend setup

```bash
cd frontend
npm install
npm run dev
```

The app runs at `http://localhost:3000`.

## Current implementation status

- [x] FastAPI backend with health endpoint (`GET /api/v1/health`)
- [x] PDF upload + extraction endpoint (`POST /api/v1/papers/extract`)
- [x] Initial PDF parser (pages, text, DOI candidates, abstract/references detection)
- [x] Backend test suite
- [x] Frontend scaffold (Next.js + TypeScript + Tailwind, placeholder pages)
- [ ] Metadata and citation verification (future)
- [ ] ML risk models (future)
- [ ] Consistency rules and explainable risk report (future)
- [ ] Fake review detector (future)

## Team workflow

The team works sequentially on a single `main` branch: one member works at a time, pulls the latest `main` before starting, pulls with rebase before pushing, and notifies the group before and after. No separate branches are used at this stage. See `docs/team-workflow.md` for the full procedure.

## Disclaimer

VeriScholar is an educational project. Its outputs are screening signals that may help detect papers warranting closer inspection. They are not proof of misconduct, plagiarism, or fabrication. Always confirm findings against primary sources before drawing conclusions.
