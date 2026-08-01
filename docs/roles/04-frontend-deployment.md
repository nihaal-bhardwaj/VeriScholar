# Role Manual — Frontend & Deployment Engineer

## 1. Role name

- **Official role name:** Frontend & Deployment Engineer
- **Short role name:** Frontend & Deployment
- **Purpose:** Own the Next.js user interface: PDF upload, analysis progress, research-integrity report dashboard, citation summary and detail tables, evidence presentation, fake-review detector screen, error and partial states, and later deployment and demo assets. The frontend must never invent completed analysis stages or fake backend results.

## 2. Position in the system

```text
PDF upload
→ PDF extraction           (Technical Lead, Backend & PDF Processing Engineer)
→ Metadata and citation checks   (Citation Integrity Engineer)
→ ML analysis                    (Paper ML Engineer)
→ Combined result                (Technical Lead orchestrates)
→ Frontend report                ← this role owns this stage
```

This role owns the user-facing application. Everything displayed after extraction and analysis is produced here by consuming the typed API responses defined in `docs/api-contract.md`. Backend response fields are consumed as-is and never silently renamed or restructured.

## 3. Main responsibilities

### Core responsibilities

- Next.js application ownership: App Router structure, pages, layouts and navigation (Paper Analyser, Review Detector, Methodology).
- React and TypeScript responsibilities: typed components, typed API models matching `docs/api-contract.md`, controlled forms.
- Tailwind CSS usage for styling, responsive layouts and consistent design.
- PDF upload interface with drag-and-drop and file selection.
- Client-side PDF type and size validation before submission.
- Backend API integration using the Fetch API with an environment-based backend URL.
- Analysis-progress interface: uploading, extracting, verifying metadata, checking citations, running model, generating report.
- Extraction-result presentation and the research-integrity report dashboard.
- Citation summary and citation-detail table.
- Fake Review Detector interface.
- Methodology and limitations page.
- Loading, empty, error and partial-result states for every screen.
- Accessible labels and keyboard interaction; responsive layouts.
- Clear evidence and warning presentation with careful language and disclaimers.
- Printable or downloadable report later (after the report is stable).

### Integration responsibilities

- Consume the shared API contract (`docs/api-contract.md`) as the single source of truth for response shapes.
- Coordinate CORS and environment variables with the Technical Lead.
- Use mock data only under the documented rules (see section 10).
- Never invent completed analysis stages; modules that have not run or failed are shown honestly as pending or unavailable.

### Testing responsibilities

- `npm run lint` and `npm run build` before claiming completion.
- Component/unit tests (Vitest + React Testing Library) once a testing setup is added.
- Playwright end-to-end smoke tests for the core flow once E2E setup is added.
- Manual verification in a clean browser.

### Deployment responsibilities

- Deploy the frontend once the application is integrated and stable.
- Configure the backend URL through environment variables and coordinate CORS with the Technical Lead.
- Verify the deployed application in a clean browser (no cached data, no console errors).
- Record a demo fallback (e.g. a recorded local demo) if deployment is not yet available.
- The backend hosting provider is not yet selected; deployment documentation must be added once it is chosen.

## 4. Owned files and directories

### Primary ownership

```text
frontend/
```

### Shared coordination areas

- `docs/api-contract.md` — the source of truth for response shapes; frontend-related sections may be updated, but backend response formats are never changed without coordination with the Technical Lead.
- `sample-responses/sample-paper-analysis.json` — the mock data source for building UI before the backend is fully integrated.
- `.env.example` — documents the environment variables the frontend and backend expect.
- Deployment documentation (to be added once hosting decisions are made).
- `docs/project-status.md` and `docs/session-handoff.md` — update after every session.

### Other members' areas (do not casually edit)

```text
backend/app/ (api/, core/, schemas/, services/) → Technical Lead, Citation Integrity Engineer, Paper ML Engineer
ml/ → Paper ML Engineer
docs/roles/ and shared docs → coordinated edits only
```

## 5. Programming languages

| Language | Why it is needed | Expected level |
| --- | --- | --- |
| TypeScript | Typed application code and typed API models | Advanced |
| HTML / JSX | Component markup | Advanced |
| CSS | Tailwind utility classes, responsive styling | Intermediate |
| JavaScript / JSON | Build tooling, configuration, API payloads | Intermediate |
| Markdown | Project documentation | Basic |

## 6. Technologies and libraries

| Technology | Purpose in VeriScholar | Required or optional |
| --- | --- | --- |
| Next.js (App Router) | Application framework: routing, layouts, server/client components, build | Required |
| React | UI component model and state management | Required |
| TypeScript | Static typing for components and API models | Required |
| Tailwind CSS | Utility-first styling and responsive layouts | Required |
| Fetch API | Backend calls (upload, health, analysis) — no extra HTTP client needed | Required |
| ESLint (eslint-config-next) | Linting (`npm run lint`) | Required |
| Vitest + React Testing Library | Component/unit tests (officially recommended setup for Next.js) | Required (once testing is added) |
| Playwright | End-to-end tests of the core user flow | Required (once E2E is added) |
| Vercel | Primary frontend hosting option for Next.js deployments | Optional (when deploying) |

No unnecessary libraries: API calls use the native Fetch API; no axios or HTTP client wrapper is planned.

## 7. Knowledge requirements

### Must understand

- Next.js App Router: layouts and pages, client and server components, route structure, environment variables, production build behaviour.
- Repository rule for this codebase: the project uses a Next.js version with breaking changes relative to standard documentation. Before writing frontend code, read the relevant guide in `node_modules/next/dist/docs/` (per the frontend `AGENTS.md`) and heed deprecation notices.
- React: components, hooks, state and effects, forms, event handling, key-based lists.
- TypeScript: interfaces for API response types, strict typing, `unknown`/`never` handling for partial API data.
- Tailwind CSS: utility classes, responsive breakpoints, hover/focus states.
- Fetch API: `FormData` uploads, `response.ok` checks, JSON parsing, `AbortController` timeouts, uniform error handling.
- Loading, empty, error and partial-result state patterns.
- Accessibility: semantic HTML, labels linked to inputs (`htmlFor`/`id`), `aria` attributes, keyboard interaction, visible focus states.
- Careful language: risk-signal wording, never "this paper is fake".

### Should learn during development

- React Testing Library queries (`getByRole`, `getByLabelText`) and user-event interactions.
- Playwright test runner basics: locators, web-first assertions, mock-mode coverage.
- CORS interaction between the frontend origin and the backend, and how allowed origins are configured.

### Optional advanced knowledge

- Printable/downloadable report generation (approach not yet chosen — no library committed).
- Vercel deployment configuration when the deployment phase begins.

## 8. Official documentation and sources

| Source | What to learn or obtain from it | Priority |
| --- | --- | --- |
| [Next.js documentation](https://nextjs.org/docs) — verified | App Router, layouts, pages, environment variables, deployment, official testing guide (Jest/Vitest/Cypress/Playwright) | Required |
| [React documentation](https://react.dev/learn) — verified | Components, hooks, state, forms | Required |
| [TypeScript documentation](https://www.typescriptlang.org/docs/) — verified | Types, interfaces, project configuration | Required |
| [Tailwind CSS documentation](https://tailwindcss.com/docs) — verified | Utility classes, responsive design | Required |
| [Fetch API (MDN)](https://developer.mozilla.org/en-US/docs/Web/API/Fetch_API) — verified | Requests, FormData, error handling | Required |
| [Vitest documentation](https://vitest.dev/) — verified | Unit test runner | Required (testing) |
| [React Testing Library documentation](https://testing-library.com/react) — verified | Component queries and user-centric testing | Required (testing) |
| [Playwright documentation](https://playwright.dev/) — verified | End-to-end testing of the user flow | Required (E2E) |
| [Vercel documentation](https://vercel.com/docs) — verified | Next.js deployment, environments, previews | Recommended (deployment) |
| Bundled Next.js guides in `node_modules/next/dist/docs/` — verified locally in the repository | Version-specific breaking changes for this project's Next.js version | Required |

The backend hosting provider is not yet selected; its official documentation will be added once a provider is chosen.

## 9. Inputs received

- **Source:** Technical Lead's FastAPI backend.
- **Contract:** `docs/api-contract.md`.
- **Endpoints:** `GET /api/v1/health`; `POST /api/v1/papers/extract` (multipart `file`); future combined analysis response with `metadata_analysis`, `citation_analysis`, `ml_analysis`, `consistency_analysis` and `final_assessment` blocks.
- **Missing-data behaviour:** unimplemented modules report `pending` with `null` values, and failed modules report their status honestly. The UI must render these as loading, unavailable or failed checks — never as completed analysis.
- **Mock source:** `sample-responses/sample-paper-analysis.json`, used only under the mock-data rules in section 10.

## 10. Outputs produced

### User-facing flows

The planned user flow:

1. User selects a PDF (drag-and-drop or file selection).
2. Frontend validates the file (type and size) client-side.
3. Frontend uploads it to FastAPI (`POST /api/v1/papers/extract`).
4. Analysis status is displayed (uploading, extracting, verifying metadata, checking citations, running model, generating report).
5. Available results and warnings are shown.
6. Unavailable or failed checks are identified honestly (pending/unavailable states).
7. User reviews evidence and limitations.

### Behavioural requirements

- Loading, empty, error and partial-result states must be handled on every screen — never a crash.
- Wording must not imply proof of misconduct; risk scores and signals are screening indicators.
- Clear evidence and warning presentation: each warning is shown with its source context.
- Accessible labels and keyboard interaction for the upload control and all interactive elements.
- Responsive layouts across screen sizes.
- Printable or downloadable report later, once the report output is stable.
- A disclaimer equivalent to the following must be visible on analysis screens:

```text
This analysis highlights signals that may require human review. It does not prove research misconduct.
```

### Mock-data rules

Mock data may be used only when:

- It follows `docs/api-contract.md`.
- It is clearly labelled as mock data.
- It is not presented to users as real analysis.
- It can later be replaced cleanly with live API responses.

## 11. Ordered implementation requirements

1. Review `docs/api-contract.md` and `sample-responses/sample-paper-analysis.json`.
2. Build the Paper Analyser route.
3. Add drag-and-drop PDF selection with a file-selection fallback.
4. Validate file type and size client-side before submission.
5. Build the processing-stage UI: uploading, extracting, verifying metadata, checking citations, running model, generating report.
6. Build an extraction-result view using mock JSON (clearly labelled).
7. Build a report-dashboard shell (research-integrity report dashboard).
8. Build a citation summary and citation-detail table shell.
9. Add empty, error and partial-result states.
10. Integrate the real extraction endpoint with an environment-based backend URL and coordinated CORS.
11. Build the Fake Review Detector interface.
12. Build the Methodology and limitations page.
13. Accessibility pass: labels, keyboard interaction, focus states.
14. Responsive layout pass.
15. Add component/unit tests (Vitest + React Testing Library).
16. Add Playwright end-to-end smoke tests for the core flow.
17. Add printable/downloadable report later.
18. Deploy after the application is integrated and stable; verify in a clean browser; record a demo fallback.

## 12. Acceptance criteria

- PDF upload validates file type and size before submitting.
- Processing stages render correctly, in mock mode without a backend.
- Extraction result and report shells render from mock JSON following `docs/api-contract.md`.
- Empty, error and partial-result states are handled, not crashes.
- Disclaimers and "human review" wording are visible on analysis screens.
- Mock data is clearly labelled, never presented as real analysis, and cleanly replaceable with live responses.
- No invented completed analysis stages and no fake backend results.
- Backend URL is environment-driven; CORS coordinated with the Technical Lead.
- `npm run lint` and `npm run build` pass.
- Accessible labels, keyboard interaction and responsive layouts are in place.

## 13. Testing responsibilities

### Commands

```bash
cd frontend
npm run lint
npm run build
```

### Component/unit tests (once a testing setup is added)

- Client-side file validation (wrong type, oversized file).
- Processing-stage rendering.
- Empty, error and partial-result states.
- Disclaimer and risk-signal wording rendering.

### End-to-end tests (Playwright, once added)

- PDF selection → validation → upload → progress → report display (mock mode).

### Manual verification

- Clean browser session (no cached data or stale service workers), console free of errors, network tab showing the expected API calls.
- Demo fallback: record a local demo if deployment is not yet available.

## 14. Dependencies on other roles

### Needs from other roles

- **Technical Lead, Backend & PDF Processing Engineer:** stable API contract, CORS allowed origins, environment-variable documentation, backend deployment status, and coordination for any contract change.
- **Paper ML Engineer:** the `ml_analysis` block shape for the report dashboard.
- **Citation Integrity Engineer:** the `metadata_analysis`, `citation_analysis` and `consistency_analysis` block shapes for the citation tables and report.

### What other roles need from this role

- Feedback on which backend fields the UI requires for display.
- Early integration feedback on the contract before release.
- A deployed or recorded demo of the interface for the team.

### Mocked backend behaviour

- The backend modules may be mocked while they are being built — only with labelled mock data following `docs/api-contract.md`, never presented as real analysis.

### Contract changes requiring coordination

Any response-shape change requires: schema update, backend test update, `docs/api-contract.md` update, `sample-responses/` update, frontend coordination and a `docs/project-status.md` entry.

## 15. Common mistakes to avoid

- Claiming "This paper is fake" or presenting risk scores as proof of misconduct.
- Hard-coding backend response shapes not yet in `docs/api-contract.md`.
- Silently renaming or restructuring backend response fields.
- Waiting for all backend modules before building UI (use clearly labelled mock JSON).
- Presenting mock data as real analysis.
- Committing `node_modules`, `.next`, environment files or API keys.
- Changing backend response formats without coordination with the Technical Lead.
- Ignoring partial-result states (modules reporting `pending` or `unavailable`).
- Building the upload control without accessible labels and keyboard interaction.
- Ignoring CORS and environment-variable coordination until deployment.
- Adding unnecessary libraries (e.g. an HTTP client when Fetch API suffices).

## 16. Definition of done

- [ ] Working frontend flow from PDF selection to extraction/report display (mock mode first, then live backend).
- [ ] Empty, error and partial-result states handled.
- [ ] Disclaimers and "human review" wording visible on analysis screens.
- [ ] Mock data follows the mock-data rules and is clearly labelled.
- [ ] `npm run lint` and `npm run build` pass.
- [ ] Tests added where the testing setup exists; results recorded.
- [ ] Backend URL environment-driven; CORS coordinated.
- [ ] `docs/project-status.md` updated; handoff entry appended to `docs/session-handoff.md`.
- [ ] No unrelated files modified.
- [ ] Commit/push status reported to the team.

## 17. Handoff requirements

After meaningful changes, report:

- Pages and routes added or changed.
- Mock integration status and which mock data was used.
- Any API fields needed from the backend.
- Environment variables added and CORS changes coordinated.
- Tests run and results (lint, build, component tests, E2E).
- Deployment status and demo-fallback recording location.
- Blockers and dependencies.
- Whether changes were committed and pushed.

## 18. Viva knowledge

Be able to explain:

- The VeriScholar pipeline position of the frontend and why outputs are risk signals requiring human review.
- The Next.js App Router structure of the application and why it is organised that way.
- How the PDF upload interface works: drag-and-drop, file selection and client-side type/size validation.
- How the processing stages map to the backend modules and how `pending`/`unavailable` states are shown honestly.
- How the Fetch API is used for uploads and how errors are handled uniformly.
- The mock-data policy: when mock data is allowed and why it is always labelled.
- Why the frontend never invents completed analysis stages or fake backend results.
- How the disclaimer wording protects the product boundary.
- How the citation summary and citation-detail table render from the citation contract blocks.
- Accessibility choices: labels, keyboard interaction, focus management.
- Responsive layout approach with Tailwind CSS.
- Environment-based backend URL and CORS coordination with the backend.
- The deployment plan: clean-browser verification and demo-fallback recording.
- Why backend response fields are never renamed or restructured in the frontend.
