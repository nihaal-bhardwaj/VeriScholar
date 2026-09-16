import httpx
from httpx import AsyncClient
import asyncio
from app.schemas.citation import CitationVerifyRequest, CitationAnalysisResult
from app.services.citations.crossref import verify_by_doi
from app.services.citations.openalex import verify_by_title

async def verify_citations(request: CitationVerifyRequest) -> CitationAnalysisResult:
    """Orchestrates citation verification across references."""
    verified = 0
    unresolved = 0
    warnings = []

    # Simple concurrency with httpx Client
    async with httpx.AsyncClient() as client:
        tasks = []
        for ref in request.references:
            if not isinstance(ref, dict):
                continue
            
            # If DOI is present, use Crossref
            doi = ref.get("doi")
            if doi:
                tasks.append(verify_by_doi(doi, client))
            else:
                # Fallback to OpenAlex with title
                raw_text = ref.get("raw_text", "")
                if raw_text:
                    tasks.append(verify_by_title(raw_text, client))
                else:
                    unresolved += 1
        
        if tasks:
            # Gather all results asynchronously
            results = await asyncio.gather(*tasks)
            for res in results:
                if res.get("exists"):
                    verified += 1
                else:
                    unresolved += 1

    return CitationAnalysisResult(
        status="completed",
        verified=verified,
        unresolved=unresolved,
        warnings=warnings
    )
