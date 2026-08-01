# VeriScholar — AGENTS.md

This file is the universal instruction file for any coding AI working in this repository. Read it fully before doing anything else.

## A. Mandatory startup procedure

Every AI agent must begin by:

1. Confirming the current working directory is the VeriScholar repository root.
2. Reading:
   - `AGENTS.md` (this file)
   - `docs/project-status.md`
   - `docs/api-contract.md`
   - `docs/team-workflow.md`
   - The relevant role file in `docs/roles/`
3. Inspecting:
   - `git status`
   - Recent Git history
   - Relevant source files
   - Existing tests
4. Treating the repository and Git history as the source of truth.
5. Not relying only on old chat messages or assumptions.

## B. Mandatory role-identification rule

Determine the current member's official role before proposing or making code changes.

Accepted official roles:

```text
Technical Lead, Backend & PDF Processing Engineer
Research Paper ML & Dataset Engineer
Citation Integrity, Metadata Verification & Fake Review Engineer
Frontend & Deployment Engineer
```

If the user has clearly stated one of these roles or an obvious shortened equivalent, continue without asking again.

Valid shortened equivalents:

```text
Backend & PDF
Paper ML
Citation Integrity
Frontend & Deployment
```

If no role is stated and it cannot be reliably inferred, ask exactly one concise question:

```text
Which VeriScholar role are you working as?
```

Then provide the four role options.

Do not start implementation before the role is known.

If the user is the Technical Lead asking for repository-wide coordination, integration or architectural work, allow cross-module inspection, but avoid silently rewriting another member's owned module.

## C. Role-loading procedure

After the role is known, read the matching role playbook:

```text
Technical Lead, Backend & PDF Processing Engineer
→ docs/roles/01-technical-lead-backend-pdf.md

Research Paper ML & Dataset Engineer
→ docs/roles/02-research-paper-ml-dataset.md

Citation Integrity, Metadata Verification & Fake Review Engineer
→ docs/roles/03-citation-integrity-metadata-review.md

Frontend & Deployment Engineer
→ docs/roles/04-frontend-deployment.md
```

Then state briefly:

- What is already completed for that role
- The next recommended task
- Files expected to change
- Dependencies or blockers
- Tests that will be run

Do not provide a long generic project explanation unless requested.

## D. Git workflow

The team intentionally uses a main-only sequential workflow:

- Only one member works on the repository at a time.
- The working member informs the group before starting.
- Nobody else edits or pushes during that period.
- Before beginning:

```bash
git switch main
git pull origin main
git status
```

- Before pushing:

```bash
git pull --rebase origin main
```

- Never force-push.
- Never discard another member's work.
- Keep `main` runnable after every push.
- Do not push failing code.
- Do not commit secrets, environments, dependency folders, generated builds, uploaded PDFs or large model/data files.

The AI must not commit or push unless the user explicitly asks it to do so.

If asked to push, verify tests and staged files first.

## E. Product boundaries

Preserve these boundaries at all times:

- Do not claim fraud has been proven.
- Do not invent analysis results.
- Do not add fake risk scores as placeholders that appear real.
- Do not present AI-authorship detection as reliable proof.
- Do not perform full plagiarism detection as part of the MVP.
- Do not attempt advanced scientific image forensics before the core system is complete.
- Use explainable evidence and human-review wording (e.g. "High attention recommended", never "This paper is fake").
- Preserve privacy and avoid permanently storing uploaded PDFs unless deliberately implemented.

## F. Technical quality rules

- Inspect before editing.
- Keep route handlers thin.
- Keep logic in services.
- Use Python type hints.
- Use Pydantic schemas.
- Preserve existing API contracts unless a coordinated versioned change is required.
- Add or update tests with every meaningful backend feature.
- Run existing tests before claiming completion.
- Avoid giant files and unnecessary abstractions.
- Do not modify unrelated modules.
- Do not add dependencies without documenting why.
- Never expose secrets or stack traces.
- Keep Windows development compatibility.
- Frontend must handle loading, errors and partial results.
- External API integrations must use timeouts, retries where reasonable and mocked tests.

## G. Session completion procedure

Before finishing a coding session:

1. Run relevant tests.
2. Review changed files.
3. Update `docs/project-status.md`.
4. Add a concise handoff entry to `docs/session-handoff.md`.
5. Mention blockers and dependencies.
6. Confirm whether code was committed or pushed.
7. Never claim completion without verification.
