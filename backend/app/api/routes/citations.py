from fastapi import APIRouter
from app.schemas.citation import CitationVerifyRequest, CitationAnalysisResult
from app.services.citations.verifier import verify_citations

router = APIRouter(tags=["citations"])

@router.post("/citations/verify", response_model=CitationAnalysisResult)
async def verify_citations_endpoint(request: CitationVerifyRequest) -> CitationAnalysisResult:
    """Verifies a batch of references using external Academic APIs."""
    result = await verify_citations(request)
    return result
