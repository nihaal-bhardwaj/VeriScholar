"""Integrity consistency-check endpoint."""

from fastapi import APIRouter, status

from app.schemas.consistency import ConsistencyCheckRequest, ConsistencyReport
from app.services.consistency_checker import check_consistency

router = APIRouter()


@router.post(
    "/integrity/check",
    response_model=ConsistencyReport,
    status_code=status.HTTP_200_OK,
    tags=["integrity"],
)
def check_integrity(request: ConsistencyCheckRequest) -> ConsistencyReport:
    """Run local consistency rules over an already-extracted paper.

    The check is fully local: no external API is called and no fake-paper
    verdict is produced, only explainable screening signals.
    """
    return check_consistency(
        full_text=request.full_text,
        authors=request.authors,
        references=request.references,
    )