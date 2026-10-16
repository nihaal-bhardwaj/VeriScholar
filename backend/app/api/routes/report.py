import logging
import uuid

from fastapi import APIRouter, File, HTTPException, UploadFile, status

logger = logging.getLogger(__name__)

from app.api.routes.papers import _read_upload, _validate_pdf_upload
from app.core.config import get_settings
from app.schemas.paper import ReferenceEntry
from app.schemas.report import ReportInput, RiskReport
from app.services.consistency_checker import check_consistency
from app.services.ml.ml_pipeline import run_ml_analysis
from app.services.pdf_parser import (
    PDFCorruptError,
    PDFParseError,
    PDFPasswordProtectedError,
    parse_pdf_bytes,
)
from app.services.report_generator import generate_report

router = APIRouter()


@router.post(
    "/report/generate",
    response_model=RiskReport,
    status_code=status.HTTP_200_OK,
    tags=["report"],
)
def generate(request: ReportInput) -> RiskReport:
    """Generate the unified risk report from all module outputs."""
    return generate_report(request)


import asyncio
from app.schemas.citation import CitationVerifyRequest
from app.services.citations.paper_metadata import verify_paper_metadata
from app.services.citations.verifier import verify_citations


@router.post(
    "/analyze/full",
    response_model=RiskReport,
    status_code=status.HTTP_200_OK,
    tags=["report"],
)
async def analyze_full(file: UploadFile | None = File(default=None)) -> RiskReport:
    """Run the full pipeline on an uploaded PDF in one request.

    Extracts the paper, runs consistency checks, ML analysis, and paper-level
    metadata verification against Crossref / OpenAlex, then generates the unified risk report.
    """
    settings = get_settings()
    max_size_bytes = settings.max_upload_size_bytes

    if file is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A PDF file must be provided as multipart form data.",
        )

    data, filename = _read_upload(file, max_size_bytes)
    _validate_pdf_upload(file, len(data), max_size_bytes)

    try:
        parsed = parse_pdf_bytes(data, filename)
    except PDFPasswordProtectedError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=str(exc),
        ) from exc
    except (PDFCorruptError, PDFParseError) as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=str(exc),
        ) from exc

    references = [
        ReferenceEntry(
            number=entry.get("number"),
            raw_text=entry["raw_text"],
            doi=entry.get("doi"),
        )
        for entry in parsed.references
    ]
    consistency = check_consistency(
        full_text=parsed.raw_text,
        authors=parsed.authors,
        references=references,
        abstract=parsed.abstract,
    )

    ml_result = run_ml_analysis(
        full_text=" ".join(page.get("text", "") for page in parsed.pages),
        abstract=parsed.abstract or "",
        pages=parsed.pages,
        extraction_quality=parsed.extraction_quality,
    )

    async def _fetch_metadata() -> dict:
        try:
            return await verify_paper_metadata(
                title=parsed.title,
                authors=parsed.authors,
                doi=parsed.best_doi,
            )
        except Exception as exc:
            logger.warning(f"Paper metadata verification error: {exc}")
            return {
                "matched": False,
                "title_match": False,
                "author_match": False,
                "doi_match": False,
                "status": "unavailable",
            }

    async def _fetch_citations() -> dict:
        if not references:
            return {
                "status": "completed",
                "verified": 0,
                "unresolved": 0,
                "warnings": [],
                "details": [],
            }
        try:
            req = CitationVerifyRequest(
                analysis_id=str(uuid.uuid4()),
                references=[ref.model_dump() for ref in references],
            )
            res = await asyncio.wait_for(verify_citations(req), timeout=8.0)
            return res.model_dump()
        except Exception as exc:
            logger.warning(f"Citation verification error: {exc}")
            return {
                "status": "unavailable",
                "verified": 0,
                "unresolved": len(references),
                "warnings": [f"Citation verification unavailable or timed out: {exc}"],
                "details": [],
            }

    paper_metadata, citation_results = await asyncio.gather(
        _fetch_metadata(),
        _fetch_citations(),
    )

    return generate_report(
        ReportInput(
            analysis_id=str(uuid.uuid4()),
            paper_title=parsed.title or "",
            paper_authors=parsed.authors,
            abstract=parsed.abstract or "",
            keywords=parsed.keywords,
            consistency_report=consistency,
            ml_results=ml_result,
            extraction_quality=parsed.extraction_quality,  # type: ignore[arg-type]
            paper_metadata=paper_metadata,
            citation_results=citation_results,
        )
    )