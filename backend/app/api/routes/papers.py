"""Paper upload and extraction endpoint."""

import uuid

from fastapi import APIRouter, File, HTTPException, UploadFile, status

from app.core.config import get_settings
from app.schemas.paper import ExtractionResponse, PaperExtraction
from app.services.pdf_parser import (
    PDFCorruptError,
    PDFParseError,
    PDFPasswordProtectedError,
    parse_pdf_bytes,
)

router = APIRouter()


def _validate_pdf_upload(file: UploadFile | None, size_bytes: int, max_size_bytes: int) -> None:
    """Raise an HTTPException when the upload is not an acceptable PDF."""
    if file is None or not file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A PDF file must be provided as multipart form data.",
        )

    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=f"File '{file.filename}' is not a PDF. Only .pdf files are accepted.",
        )

    if size_bytes == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File '{file.filename}' is empty.",
        )

    if size_bytes > max_size_bytes:
        raise HTTPException(
            status_code=status.HTTP_413_CONTENT_TOO_LARGE,
            detail=f"File '{file.filename}' exceeds the maximum upload size of {max_size_bytes} bytes.",
        )

    if file.content_type is not None and file.content_type.lower() not in ("application/pdf", "application/x-pdf"):
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=f"File '{file.filename}' has MIME type '{file.content_type}', expected 'application/pdf'.",
        )


def _read_upload(file: UploadFile, max_size_bytes: int) -> tuple[bytes, str]:
    """Read the upload body, rejecting files larger than the configured limit."""
    settings = get_settings()
    filename = file.filename or "upload.pdf"
    data = file.file.read(max_size_bytes + 1)
    if len(data) > max_size_bytes:
        raise HTTPException(
            status_code=status.HTTP_413_CONTENT_TOO_LARGE,
            detail=f"File '{filename}' exceeds the maximum upload size of {max_size_bytes} bytes.",
        )
    return data, filename


@router.post(
    "/papers/extract",
    response_model=ExtractionResponse,
    status_code=status.HTTP_200_OK,
    tags=["papers"],
)
def extract_paper(file: UploadFile | None = File(default=None)) -> ExtractionResponse:
    """Extract structured content from an uploaded research-paper PDF."""
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

    paper = PaperExtraction(
        filename=parsed.filename,
        file_size_bytes=parsed.file_size_bytes,
        page_count=parsed.page_count,
        doi=parsed.best_doi,
        doi_candidates=parsed.doi_candidates,
        abstract=parsed.abstract,
        references_text=parsed.references_text,
        references=parsed.references,
        pages=parsed.pages,
    )

    return ExtractionResponse(
        analysis_id=str(uuid.uuid4()),
        status="completed",
        paper=paper,
        warnings=parsed.warnings,
    )
