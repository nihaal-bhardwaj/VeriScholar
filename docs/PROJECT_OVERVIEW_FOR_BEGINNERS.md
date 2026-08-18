# Mini Project — Complete Project Overview for Beginners

## What is this project?

**Mini Project** is a research-integrity screening tool built as a college mini-project. Think of it as a detector that helps find suspicious things in academic research papers and fake product reviews.

**Important:** It never says "this paper is fake." Instead, it finds warning signs (called "screening signals") that a human reviewer should look into. It's like a red flag, not a conviction.

The project has two main parts:
1. **Research Paper Integrity Risk Detector** (primary focus, currently being built)
2. **Fake Review Detector** (secondary, not started yet)

---

## What is the system supposed to do? (The Goal)

When someone uploads a research paper as a PDF file, the system should:

1. **Extract structure** — pull out the title, authors, abstract, references, keywords, and the full text from the PDF
2. **Verify metadata** — check if the authors, journal, publisher actually exist (using databases like Crossref and OpenAlex)
3. **Verify citations** — check if the references cited in the paper are real papers that actually exist
4. **Run ML analysis** — train machine learning models to detect unusual patterns that might indicate fake papers
5. **Check for inconsistencies** — look for conflicts between the dates, claims, figures, and text in the paper
6. **Produce a report** — generate a clear, human-readable report listing all the warning signs found with confidence levels

The system gives a **risk score** (not a verdict) based on how many warning signs were found.

---

## Project Structure — How is it organized?

```
mini-project/
├── backend/              ← Python FastAPI server (the brain)
├── frontend/             ← Next.js + TypeScript website (the interface)
├── ml/                   ← Machine learning code and datasets (future)
├── docs/                 ← Documentation and guides
├── sample-papers/        ← Example PDF files for testing
└── sample-responses/     ← Example outputs the API should produce
```

### Backend (Python with FastAPI)
- Accepts PDF uploads from the frontend
- Parses PDFs to extract text, DOIs, abstract, references, title, authors
- Provides APIs (endpoints) that the frontend calls
- Will later orchestrate all the analysis modules and combine their results

### Frontend (Next.js + TypeScript)
- The website/web app users interact with
- Has a form to upload PDFs
- Shows progress while the backend analyzes the paper
- Displays the final analysis report

### ML Module (Python notebooks and models)
- Machine learning models to detect suspicious patterns
- Not started yet; will be trained on labeled datasets
- Will produce risk probabilities

### Docs
- Project status, team workflow, API contract, architecture diagrams
- Role descriptions for each team member
- Handoff notes between team members

---

## What has been COMPLETED so far?

### ✅ Backend Foundation (Python)

**What works:**
- FastAPI server is set up and running
- Health check endpoint (`GET /api/v1/health`) — tells you if the server is alive
- PDF upload and extraction endpoint (`POST /api/v1/papers/extract`) — accepts PDF files and returns extracted data

**What the PDF parser can do:**
- Extract all text from every page of the PDF
- Extract one combined text (all pages merged)
- Find DOI numbers (digital object identifiers) in the text
- Detect the abstract section (the summary at the start of academic papers)
- Detect the references section (the bibliography at the end)
- Parse numbered references into structured entries (e.g. `[1] Author Name, ...` becomes a reference object)
- Extract the title conservatively (carefully — doesn't guess when uncertain)
- Extract author names conservatively (won't make up names)
- Detect when the abstract ends and other sections begin (stops at keywords, funding info, etc.)

**Error handling:**
- Returns code 400 if no file or empty file uploaded
- Returns code 415 if not a PDF file
- Returns code 413 if the file is too large
- Returns code 422 if the PDF is corrupt, password-protected, or has no readable text
- Returns code 500 only for unexpected server errors (never exposes error details)

**Tests:**
- 86 unit and integration tests all passing
- Tests verify correct extraction, error codes, and edge cases

### ✅ Frontend Scaffold (Next.js + TypeScript)

**What works:**
- Landing page with navigation
- Basic styling with Tailwind CSS
- "Paper Analyser" link that goes to upload page (but the page is a placeholder)
- TypeScript type safety configured
- Linter passes (no syntax errors)
- Production build succeeds

**What doesn't work yet:**
- PDF upload form doesn't actually connect to the backend yet
- Analysis progress display is a mock (shows fake progress)
- No real analysis results are shown
- Navigation links are mostly placeholders

### ✅ Documentation

- README explaining the whole project
- API contract document specifying exactly what endpoints exist and what they return
- Project scope document explaining what's in the MVP and what's explicitly out of scope
- Architecture diagram showing how all modules fit together
- Team workflow guide (how members coordinate and push code)
- AI onboarding guide (how to help contributors get up to speed)
- Role playbooks (what each team member is responsible for)
- Project status document (updated after each work session)
- Session handoff document (notes from previous team members)

### ✅ Repository Setup

- Git configured with main-only workflow (one person works at a time)
- `.env.example` file showing what environment variables need to be set
- `.gitignore` configured to avoid uploading secrets, uploads, or dependencies
- Sample response file showing what the API should return

---

## What is NOT done yet? (The Remaining Work)

### ❌ Metadata Verification Module
- **What it should do:** Check if the authors, journal, and publisher actually exist using Crossref and OpenAlex databases
- **Current status:** Not started
- **Owner:** Citation Integrity, Metadata Verification & Fake Review Engineer

### ❌ Citation Verification Module
- **What it should do:** For each reference cited in the paper, verify that the reference actually exists (using DOI lookup or title search)
- **Current status:** Not started
- **Owner:** Citation Integrity, Metadata Verification & Fake Review Engineer

### ❌ ML Risk Detection Module
- **What it should do:** Train machine learning models on labeled datasets to detect unusual patterns (writing style, reference patterns, formatting oddities, etc.)
- **Current status:** No code yet, only a placeholder directory
- **Owner:** Research Paper ML & Dataset Engineer

### ❌ Consistency Rules Engine
- **What it should do:** Check for conflicts (dates that don't make sense, figure numbers that are referenced but don't exist, author names that change between sections, etc.)
- **Current status:** Not started
- **Owner:** Technical Lead, Backend & PDF Processing Engineer

### ❌ Risk Report Generator
- **What it should do:** Combine signals from all analysis modules into one final explainable report with a risk score
- **Current status:** Not started
- **Owner:** Technical Lead, Backend & PDF Processing Engineer

### ❌ Frontend Integration
- **What needs to happen:** Connect the frontend form to the real backend API (right now it's using fake data)
- **What's needed:** Real progress indicators, loading states, error handling
- **Current status:** Scaffold complete but not integrated
- **Owner:** Frontend & Deployment Engineer

### ❌ Fake Review Detector (Secondary Module)
- **What it should do:** Detect fake or bot-generated product reviews
- **Current status:** Not started at all
- **Owner:** Citation Integrity Engineer (secondary responsibility)

### ❌ PDF Keywords/Index Terms Extraction
- **What it should do:** Extract the keywords or index terms from the PDF when available
- **Current status:** Parser can detect where "Keywords:" appears, but doesn't extract the actual keyword list yet
- **Owner:** Technical Lead, Backend & PDF Processing Engineer

---

## How much work is done and how much is left? (Rough Progress)

```
OVERALL PROJECT COMPLETION: ~20%

Breaking it down by component:

Backend:
  ✅ Server setup and health:            100%
  ✅ PDF upload endpoint:                100%
  ✅ PDF extraction and parsing:         85% (basic extraction works, advanced features like keywords extraction missing)
  ❌ Metadata verification:              0%
  ❌ Citation verification:              0%
  ❌ Consistency rules:                  0%
  ❌ Report generator:                   0%
  ❌ ML orchestration:                   0%

Frontend:
  ✅ Page scaffold and layout:           100%
  ✅ Placeholder styling:                100%
  ⚠️  PDF upload form:                   50% (form exists, but not connected to backend)
  ❌ Real backend integration:           0%
  ❌ Analysis report display:            0%

ML Module:
  ❌ Baseline model:                     0%
  ❌ Dataset pipeline:                   0%
  ❌ Training infrastructure:            0%

Documentation:
  ✅ Complete:                           100%
```

---

## The Team and Their Roles

The project is divided into four roles (each person owns one area):

### 1. Technical Lead, Backend & PDF Processing Engineer
**What they do:**
- Own the main Python backend
- Improve the PDF parser (extract keywords, section headings, page numbers, evidence tracking)
- Build the orchestrator that combines results from other modules
- Oversee architecture and integration

**What's done:**
- FastAPI setup, health endpoint, extraction endpoint
- PDF parser (basic title, authors, abstract, references)
- 86 passing tests

**What's next:**
- Extract keywords/index terms
- Add page number and evidence tracking
- Write regression tests for new features

**Files they own:**
- `backend/app/main.py`
- `backend/app/api/`
- `backend/app/services/pdf_parser.py`
- `backend/app/schemas/`
- `backend/tests/`

---

### 2. Research Paper ML & Dataset Engineer
**What they do:**
- Build machine learning models to detect suspicious patterns in papers
- Create and manage training datasets
- Define what patterns should trigger a risk score

**What's done:**
- Nothing yet (only a placeholder `ml/` folder)

**What's next:**
- Define labels for training data (e.g. "legitimate paper", "suspicious writing style", "fabricated references")
- Build a basic TF-IDF + Logistic Regression baseline model
- Create notebooks showing the dataset and evaluation metrics

**Files they'll own:**
- `ml/datasets/`
- `ml/notebooks/`
- `ml/saved_models/`
- `backend/app/services/paper_ml/`

---

### 3. Citation Integrity, Metadata Verification & Fake Review Engineer
**What they do:**
- Build metadata verification (check if authors/journal/publisher exist)
- Build citation verification (check if references are real)
- Build the fake review detector (secondary module)

**What's done:**
- Nothing yet (no code)

**What's next:**
- Build a Crossref DOI lookup service (verify real papers by DOI)
- Build OpenAlex fallback (verify papers by title when DOI not available)
- Define what the metadata comparison output should look like (matched fields, mismatches, confidence, warnings)
- Test against known valid and invalid citations

**Files they'll own:**
- `backend/app/services/metadata/`
- `backend/app/services/citations/`
- `backend/app/services/review_detector/`

---

### 4. Frontend & Deployment Engineer
**What they do:**
- Build the web interface users interact with
- Connect frontend to backend API
- Handle loading states and errors
- Deploy the system

**What's done:**
- Landing page scaffold
- Placeholder page layout
- Styling with Tailwind CSS
- Navigation structure

**What's next:**
- Build real PDF upload form
- Call the backend API for real
- Display analysis progress (once backend supports it)
- Display the analysis report results
- Handle errors gracefully

**Files they own:**
- `frontend/app/`
- `frontend/components/`
- `frontend/lib/`

---

## How does the system currently work? (The flow)

### Right now (20% complete):

1. User goes to the frontend website
2. Frontend shows a landing page
3. User clicks "Paper Analyser"
4. Frontend shows a placeholder page (doesn't do anything yet)

### What should happen when done (100% complete):

1. User goes to the frontend website
2. User clicks "Paper Analyser"
3. User uploads a PDF file
4. Frontend shows progress bar while analyzing
5. Backend:
   - Receives the PDF
   - Extracts structure (title, authors, abstract, references, text)
   - Checks if metadata is real (author/journal verification)
   - Checks if citations are real (reference verification)
   - Runs ML model to detect suspicious patterns
   - Checks for inconsistencies
   - Produces a combined report
6. Frontend displays a detailed report showing:
   - Extracted paper info (title, authors, abstract)
   - Metadata quality (which fields checked out, which are suspicious)
   - Citation status (how many references are real)
   - ML risk signals (what unusual patterns were found)
   - Final risk score (from 0-100)
   - Confidence level (how certain the system is)
   - Main reasons for the risk score

---

## The API Contract (How frontend talks to backend)

### What the frontend can currently do:

**1. Check if backend is alive:**
```
GET http://localhost:8000/api/v1/health
→ Returns: {"status": "healthy", "service": "mini-project-api", "version": "0.1.0"}
```

**2. Upload a PDF and extract it:**
```
POST http://localhost:8000/api/v1/papers/extract
Content-Type: multipart/form-data
Body: file=<PDF file bytes>

→ Returns: {
    "analysis_id": "unique-id",
    "status": "completed",
    "paper": {
        "filename": "paper.pdf",
        "file_size_bytes": 123456,
        "page_count": 10,
        "title": "Paper Title Here",
        "authors": ["John Doe", "Jane Smith"],
        "abstract": "Abstract text...",
        "doi": "10.1234/example",
        "doi_candidates": ["10.1234/example"],
        "references_text": "Full references section text",
        "references": [
            {"number": 1, "raw_text": "Author, A. (2020). ...", "doi": null},
            {"number": 2, "raw_text": "Author, B. (2019). ...", "doi": "10.5555/example"}
        ],
        "pages": [
            {"page_number": 1, "text": "Page 1 content"},
            {"page_number": 2, "text": "Page 2 content"}
        ]
    },
    "warnings": []
}
```

### What the frontend will be able to do in the future:

```
POST http://localhost:8000/api/v1/metadata/verify
→ Will verify author/journal/publisher existence

POST http://localhost:8000/api/v1/citations/verify
→ Will verify each reference exists

POST http://localhost:8000/api/v1/ml/analyze
→ Will run ML risk detection

POST http://localhost:8000/api/v1/integrity/check
→ Will check for consistency issues

POST http://localhost:8000/api/v1/report/generate
→ Will combine everything into final report
```

---

## Important Boundaries (What the system does NOT do)

These are **explicitly excluded** from the scope:

- ❌ **Full plagiarism detection** — doesn't check if the paper is copied from other papers
- ❌ **Proof of fabrication** — can't prove experiments are fake (only detects suspicious patterns)
- ❌ **AI-authorship detection** — can't reliably determine if ChatGPT wrote it
- ❌ **Image forensics** — doesn't analyze if figures/images are manipulated
- ❌ **Truth verification** — can't check if a paper's scientific claims are actually true

**Remember:** The system finds warning signs, not proof. A human always has to review and decide.

---

## How is the team organized? (The Workflow)

**One person works at a time** on the shared `main` branch (no separate branches).

Before each person starts:
1. Pull the latest code: `git pull origin main`
2. Tell the team you're starting
3. Nobody else edits or pushes
4. Work on your module only

Before pushing:
1. Run tests to make sure nothing broke
2. Pull again with rebase: `git pull --rebase origin main`
3. Commit with clear message describing what you did
4. Push: `git push origin main`
5. Tell the team the push is complete

This ensures the code is never broken and members never lose each other's work.

---

## Current Status Summary

| Area | Status | Done | Remaining |
|------|--------|------|-----------|
| Backend server | Active | Health endpoint, PDF extraction | Metadata verification, citation verification |
| PDF parser | Active | Title, authors, abstract, references | Keywords, page tracking, evidence attribution |
| Frontend | Stalled | Landing page scaffold | Real API integration, progress UI, report display |
| ML module | Not started | - | Dataset, baseline model, training pipeline |
| Metadata verification | Not started | - | Crossref/OpenAlex integration |
| Citation verification | Not started | - | DOI/title lookup service |
| Report generator | Not started | - | Combine signals, produce risk score |
| Fake review detector | Not started | - | Detection model, integration |

**Latest stable code commit:** `36cb002`
**Backend tests passing:** 86 / 86 ✅
**Frontend linting:** Passing ✅
**Frontend production build:** Passing ✅

---

## Key Technical Concepts (Simplified)

### PyMuPDF (fitz)
- Python library that reads PDF files and extracts text
- Used by the backend to pull text from uploaded papers

### FastAPI
- Python web framework that creates APIs (endpoints)
- Each endpoint is a URL that the frontend can call
- Returns JSON responses

### Next.js + TypeScript
- JavaScript framework for building websites
- TypeScript adds type-checking (helps catch bugs)
- Tailwind CSS is used for styling

### Pydantic
- Python library that defines and validates data structures
- Ensures all responses have the right fields with the right types

### Pytest
- Python testing framework
- Runs automated tests to verify nothing is broken

### Git
- Version control system
- Tracks all code changes
- Allows team to work together without overwriting each other

---

## What needs to happen next? (Priority Order)

1. **Frontend Integration** — Connect the frontend upload form to the real backend API (blocking all user-facing features)
2. **PDF Keywords Extraction** — Add keyword/index-terms extraction to the parser
3. **ML Dataset & Baseline** — Create labeled dataset and train first ML model
4. **Metadata Verification** — Build Crossref/OpenAlex lookup
5. **Citation Verification** — Verify each reference is real
6. **Consistency Rules** — Detect date/figure/claim conflicts
7. **Report Generator** — Combine all signals into final risk score
8. **Fake Review Detector** — Build secondary module
9. **Deployment** — Set up hosting so others can use it

---

## How to Run the Project Locally

### Backend
```bash
cd backend
python -m venv .venv
.venv\Scripts\activate          # Windows
pip install -r requirements-dev.txt
uvicorn app.main:app --reload   # Starts at http://localhost:8000
```

### Frontend
```bash
cd frontend
npm install
npm run dev                      # Starts at http://localhost:3000
```

### Run tests
```bash
cd backend
python -m pytest                 # Run all tests
```

### Check frontend quality
```bash
cd frontend
npm run lint                     # Check for errors
npm run build                    # Build for production
```

---

## Common Questions Answered

### Q: Is this finished?
**A:** No. About 20% done. The PDF extraction works, but most analysis features are not built yet.

### Q: Can it actually detect fake papers?
**A:** Not yet. Right now it only extracts text. When the ML module is finished, it will detect suspicious patterns, but it never declares anything "fake."

### Q: What does "incomplete" mean in the test results?
**A:** The parser found something useful but is not confident. It still returns the result but includes a warning.

### Q: Why does it have warnings instead of errors?
**A:** The goal is to never fabricate data. If something is uncertain, it's better to warn the user than make something up.

### Q: Can I run the frontend without the backend?
**A:** Yes, currently it only shows a placeholder. Once real integration is done, the frontend will need the backend running.

### Q: What database does it use?
**A:** None yet. Currently, uploads are temporary and not stored. Storage is planned for future phases.

### Q: Who is working on this?
**A:** Four people, each owning one area: Backend & PDF, ML & Data, Citations & Metadata, Frontend & Deployment. Plus a Technical Lead.

### Q: Can I add a new feature?
**A:** Yes, but coordinate with the team first. Don't edit another person's module without asking. Update the docs when you're done.

### Q: What if I find a bug?
**A:** Tell the team immediately. Don't commit broken code. Add a test that reproduces the bug before fixing it.

---

## Files You Should Know About

```
docs/project-status.md           ← Read this to see what's currently being worked on
docs/api-contract.md             ← Read this to understand what API endpoints do
docs/architecture.md             ← Read this to see how all modules fit together
backend/app/services/pdf_parser.py ← Core PDF extraction logic
backend/tests/                   ← Test files (read these to understand what works)
frontend/app/page.tsx            ← Main landing page
frontend/app/analyser/page.tsx   ← Paper analyzer page (placeholder)
AGENTS.md                        ← Rules for how team members should work
```

---

## Done. Questions?

This document explains the entire project from scratch. Share it with anyone who needs context.

**Key takeaways:**
- It's a system to detect suspicious research papers
- Backend: ~85% done (extraction works)
- Frontend: ~50% done (needs real integration)
- ML/Citations/Metadata: 0% done
- Team works sequentially on one branch
- Never ships broken code
- All decisions documented and discoverable

