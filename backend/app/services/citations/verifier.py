import asyncio
import logging
import re
from typing import Optional

import httpx
from httpx import AsyncClient

from app.schemas.citation import CitationAnalysisResult, CitationVerifyRequest
from app.services.citations.crossref import verify_by_doi
from app.services.citations.openalex import verify_by_title

logger = logging.getLogger("mini-project.citations.verifier")

MAX_EVALUATED_REFERENCES = 25
CONCURRENCY_LIMIT = 5


def _extract_title_candidate(raw_text: str) -> str:
    """Extract a plausible paper title candidate from an unstructured reference string."""
    text = (raw_text or "").strip()
    # Strip leading reference markers: [1], 1., 1)
    text = re.sub(r"^(?:\[\d+\]|\d+[\.)]|\(\d+\))\s*", "", text).strip()

    # Check for quoted title: "Title..." or “Title...” or 'Title...'
    quote_match = re.search(r'["“\']([^"”\']{10,250})["”\']', text)
    if quote_match:
        return quote_match.group(1).strip()

    # Look for title segments between punctuation (Author, A. Title. Journal...)
    parts = re.split(r"\.\s+|\s*,\s*", text)
    for p in parts:
        cleaned = p.strip()
        words = cleaned.split()
        if len(words) >= 3 and not re.match(
            r"^(?:pp?\.|vol\.|no\.|https?://|doi:|isbn|\d{4})", cleaned, re.IGNORECASE
        ):
            return cleaned

    return text[:100].strip()


async def verify_citations(
    request: CitationVerifyRequest,
    client: Optional[AsyncClient] = None,
) -> CitationAnalysisResult:
    """Orchestrates citation verification across references with bounded concurrency."""
    verified = 0
    unresolved = 0
    warnings: list[str] = []
    details: list[dict] = []

    all_refs = [r for r in request.references if isinstance(r, dict)]
    sampled_refs = all_refs[:MAX_EVALUATED_REFERENCES]
    if len(all_refs) > MAX_EVALUATED_REFERENCES:
        warnings.append(
            f"Only the first {MAX_EVALUATED_REFERENCES} of {len(all_refs)} references were verified."
        )

    if not sampled_refs:
        return CitationAnalysisResult(
            status="completed",
            verified=0,
            unresolved=0,
            warnings=warnings,
            details=details,
        )

    sem = asyncio.Semaphore(CONCURRENCY_LIMIT)

    async def _verify_single(ref: dict, http_client: AsyncClient) -> dict:
        async with sem:
            doi = ref.get("doi")
            raw_text = ref.get("raw_text", "")
            title_candidate = _extract_title_candidate(raw_text)

            result = {
                "number": ref.get("number"),
                "raw_text": raw_text,
                "doi": doi,
                "verified": False,
                "title": title_candidate,
                "source": None,
                "note": None,
            }

            try:
                if doi:
                    res = await verify_by_doi(doi, http_client)
                    if res.get("exists"):
                        result["verified"] = True
                        result["source"] = "crossref"
                        result["title"] = res.get("title") or title_candidate
                    else:
                        result["note"] = res.get("reason", "Not found in Crossref")
                elif title_candidate and len(title_candidate) >= 8:
                    res = await verify_by_title(title_candidate, http_client)
                    if res.get("exists"):
                        result["verified"] = True
                        result["source"] = "openalex"
                        result["title"] = res.get("title") or title_candidate
                    else:
                        result["note"] = res.get("reason", "Not found in OpenAlex")
                else:
                    result["note"] = "Insufficient title data for search"
            except Exception as exc:
                logger.debug("Citation query failed for '%s': %s", title_candidate, exc)
                result["note"] = f"Lookup error: {exc}"

            return result

    own_client = False
    if client is None:
        client = httpx.AsyncClient(timeout=2.0)
        own_client = True

    ref_tasks = [
        (ref, asyncio.create_task(_verify_single(ref, client)))
        for ref in sampled_refs
    ]

    try:
        tasks = [t for _, t in ref_tasks]
        if tasks:
            done, pending = await asyncio.wait(tasks, timeout=6.5)
            for p in pending:
                p.cancel()

            if pending:
                warnings.append(
                    f"Citation verification deadline reached; {len(pending)} reference lookups could not complete in time."
                )

            for ref, task in ref_tasks:
                if task in done and not task.cancelled():
                    try:
                        res = task.result()
                        if isinstance(res, Exception):
                            unresolved += 1
                            details.append({
                                "number": ref.get("number"),
                                "raw_text": ref.get("raw_text", ""),
                                "verified": False,
                                "note": f"Lookup error: {str(res)}",
                            })
                        elif isinstance(res, dict):
                            details.append(res)
                            if res.get("verified"):
                                verified += 1
                            else:
                                unresolved += 1
                    except Exception as e:
                        unresolved += 1
                        details.append({
                            "number": ref.get("number"),
                            "raw_text": ref.get("raw_text", ""),
                            "verified": False,
                            "note": f"Lookup error: {str(e)}",
                        })
                else:
                    unresolved += 1
                    details.append({
                        "number": ref.get("number"),
                        "raw_text": ref.get("raw_text", ""),
                        "verified": False,
                        "note": "Verification timed out",
                    })
    finally:
        if own_client:
            await client.aclose()

    return CitationAnalysisResult(
        status="completed",
        verified=verified,
        unresolved=unresolved,
        warnings=warnings,
        details=details,
    )
