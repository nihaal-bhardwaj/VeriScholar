# AI-Assisted Onboarding Guide

This guide explains how a Mini Project team member works with a coding AI (OpenCode, Cline, Claude Code, Gemini CLI, Cursor, Copilot, or similar).

## What Mini Project does

Mini Project is a research-integrity screening tool with two modules:

1. **Research Paper Integrity Risk Detector (primary)** — screens uploaded PDFs for suspicious signals (DOI/metadata mismatches, unverifiable citations, missing or inconsistent sections, conflicting numbers, suspicious text) and produces explainable risk reports.
2. **Fake Review Detector (secondary)** — flags likely fake or bot-generated product reviews.

## Why "risk signals" and never "fake"

The system reports screening signals that warrant human review (wording such as "High attention recommended"). It never declares a paper fake, because no single automated signal proves misconduct. AI output on this project must follow that boundary.

## Current architecture

```text
Frontend (Next.js, scaffolded)
   ↓  /api/v1
FastAPI backend
   ↓
PDF parser (implemented: pages, text, DOI, abstract, references)
   ├── Paper ML model            (future)
   ├── Metadata & citation verifier (future)
   ├── Consistency rule engine   (future)
   └── Risk report generator     (future)
```

Full detail: `docs/architecture.md` and `docs/api-contract.md`.

## Team roles

| Role | Main directories |
| --- | --- |
| Technical Lead, Backend & PDF Processing Engineer | `backend/app/`, `backend/tests/`, `docs/api-contract.md` |
| Research Paper ML & Dataset Engineer | `ml/`, `backend/app/services/paper_ml/` (future) |
| Citation Integrity, Metadata Verification & Fake Review Engineer | `backend/app/services/metadata/`, `citations/`, `integrity_rules/`, `review_detector/` (future) |
| Frontend & Deployment Engineer | `frontend/` |

## How a member starts an AI session

1. Pull the latest `main`:

```bash
git switch main
git pull origin main
git status
```

2. Open the repository in the coding AI (the repository root, not a subfolder).
3. State your official role as your first message.

### Example prompts

**Example 1 — role stated:**

```text
My role is Frontend & Deployment Engineer. Read the project context and tell me the next task.
```

The AI reads `AGENTS.md`, `docs/project-status.md`, `docs/api-contract.md`, `docs/team-workflow.md` and `docs/roles/04-frontend-deployment.md`, then summarises your state and next task.

**Example 2 — role stated, continuing work:**

```text
I am the Research Paper ML & Dataset Engineer. Continue from the latest project status and do not modify other modules.
```

The AI picks up from `docs/project-status.md` and `docs/session-handoff.md` and stays inside your owned directories.

**Example 3 — no role stated:**

```text
I have not told you my role yet.
```

In this case the AI must ask for the official role before coding. Answer with one of:

```text
Technical Lead, Backend & PDF Processing Engineer
Research Paper ML & Dataset Engineer
Citation Integrity, Metadata Verification & Fake Review Engineer
Frontend & Deployment Engineer
```

## What the AI reads automatically

- `AGENTS.md` — universal rules (startup, roles, quality, product boundaries)
- `docs/project-status.md` — what is done and what is next per role
- `docs/api-contract.md` — the API contract all modules must follow
- `docs/team-workflow.md` — the main-only sequential Git workflow
- `docs/roles/<your-role>.md` — your role playbook

## How work is handed off

After finishing a session:

1. Run the relevant tests (see your role playbook).
2. Update `docs/project-status.md` (completed items, current/next task, blockers, tests run).
3. Add an entry at the **bottom** of `docs/session-handoff.md` (append-only log).
4. If authorised, commit and push, then notify the team group.

## How Git is used remotely

- One member works at a time on `main`.
- Pull latest `main` before starting; pull with rebase before pushing.
- Never force-push. Never delete another member's work.

## Where contracts and status live

| Information | Location |
| --- | --- |
| API contract (current + future combined shape) | `docs/api-contract.md` |
| Current status and per-role priorities | `docs/project-status.md` |
| Session handoff log | `docs/session-handoff.md` |
| Git workflow | `docs/team-workflow.md` |
| Scope and exclusions | `docs/project-scope.md` |
| Architecture | `docs/architecture.md` |
