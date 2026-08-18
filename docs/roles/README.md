# Role Manuals

These documents are permanent role-reference manuals for the Mini Project team. They define what each member owns, which technologies and official sources to use, what each module must accept and return, and how to verify and hand off work. They are **not** progress trackers, timelines or status reports — current progress lives in `docs/project-status.md` and `docs/session-handoff.md`.

## The four official roles

| Role | Role document | Main ownership |
| --- | --- | --- |
| Technical Lead, Backend & PDF Processing Engineer | `01-technical-lead-backend-pdf.md` | Backend, PDF extraction and integration |
| Research Paper ML & Dataset Engineer | `02-research-paper-ml-dataset.md` | Dataset, paper-risk model and evaluation |
| Citation Integrity, Metadata Verification & Fake Review Engineer | `03-citation-integrity-metadata-review.md` | Metadata, citations, rules and fake-review model |
| Frontend & Deployment Engineer | `04-frontend-deployment.md` | UI, API integration, reports and deployment |

## Starting a coding-assistant session

1. Pull the latest main branch.
2. Open the repository in the coding assistant.
3. State your official role.
4. Ask the assistant to read AGENTS.md and the matching role manual.
5. Work only within the responsibilities of that role unless coordination is required.

Example:

```text
My role is Frontend & Deployment Engineer. Read AGENTS.md and docs/roles/04-frontend-deployment.md before suggesting changes.
```

Before any code change, the assistant must read:

- `AGENTS.md`
- `docs/project-status.md`
- `docs/api-contract.md`
- The member's role manual listed above

## Shared rules

- The repository uses a sequential `main`-only workflow — see `docs/team-workflow.md`. No permanent member branches.
- Only one member works and pushes at a time; the working member announces before starting and after pushing.
- All shared API outputs must follow `docs/api-contract.md`.
- Every role must update `docs/project-status.md` and append to `docs/session-handoff.md` after meaningful work.
- Results are screening signals that require human review — never proof that a paper is fake.
