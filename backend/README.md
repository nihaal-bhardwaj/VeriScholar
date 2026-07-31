# VeriScholar backend

FastAPI application providing paper-integrity screening APIs.

## Setup

```bash
python -m venv .venv
.venv\Scripts\activate        # Windows
pip install -r requirements-dev.txt
```

## Run

```bash
uvicorn app.main:app --reload
```

- API: `http://localhost:8000`
- Interactive docs: `http://localhost:8000/docs`
- Health: `GET /api/v1/health`
- Extraction: `POST /api/v1/papers/extract` (multipart field `file`)

## Configuration

Configuration is read from environment variables or a `.env` file; see `../.env.example`.

## Tests

```bash
pytest
```

## Layout

```text
app/
├── api/routes/     route handlers (thin)
├── core/           configuration
├── schemas/        Pydantic response models
├── services/       pdf_parser.py (all PDF logic)
└── main.py         app wiring
tests/              pytest suite with programmatic PDF fixtures
uploads/            unused; uploads are processed in memory
```
