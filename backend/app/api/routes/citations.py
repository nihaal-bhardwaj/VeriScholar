from fastapi import APIRouter
from pydantic import BaseModel, Field
from app.schemas.citation import CitationVerifyRequest, CitationAnalysisResult
from app.services.citations.verifier import verify_citations
from app.services.citations.paper_metadata import verify_paper_metadata

router = APIRouter(tags=["citations"])


class PaperMetadataRequest(BaseModel):
    title: str | None = None
    authors: list[str] = Field(default_factory=list)
    doi: str | None = None


@router.post("/citations/verify", response_model=CitationAnalysisResult)
async def verify_citations_endpoint(request: CitationVerifyRequest) -> CitationAnalysisResult:
    """Verifies a batch of references using external Academic APIs."""
    result = await verify_citations(request)
    return result


@router.post("/citations/metadata")
async def verify_paper_metadata_endpoint(request: PaperMetadataRequest) -> dict:
    """Verifies paper-level metadata against Crossref and OpenAlex."""
    return await verify_paper_metadata(
        title=request.title,
        authors=request.authors,
        doi=request.doi,
    )
