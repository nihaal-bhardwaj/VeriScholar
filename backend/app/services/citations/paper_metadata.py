"""Paper-level metadata verification against Crossref and OpenAlex.

Verifies the bibliographic identity of an extracted paper without converting
metadata presence or absence into arbitrary fraud risk points. A match increases
confidence in identity; an API failure or missing entry does not increase fraud risk.
"""

from __future__ import annotations

import logging
import urllib.parse
from difflib import SequenceMatcher
import httpx

from app.core.config import get_settings

logger = logging.getLogger("mini-project.citations")


def _title_similarity(a: str, b: str) -> float:
    """Case- and punctuation-insensitive string similarity."""
    clean_a = "".join(c.lower() for c in a if c.isalnum() or c.isspace()).strip()
    clean_b = "".join(c.lower() for c in b if c.isalnum() or c.isspace()).strip()
    if not clean_a or not clean_b:
        return 0.0
    return SequenceMatcher(None, clean_a, clean_b).ratio()


async def verify_paper_metadata(
    title: str | None,
    authors: list[str] | None = None,
    doi: str | None = None,
    client: httpx.AsyncClient | None = None,
) -> dict:
    """Verify extracted paper metadata against Crossref and OpenAlex.

    Returns a field-level match record. Never raises an exception if APIs
    are offline or unreachable.
    """
    settings = get_settings()
    headers = {
        "User-Agent": f"MiniProject/1.0 (mailto:{settings.api_user_agent_email})"
    }

    result = {
        "status": "unverified",
        "matched": False,
        "title_match": False,
        "author_match": False,
        "doi_match": False,
        "verified_doi": None,
        "venue": None,
        "year": None,
        "source": None,
        "crossref_result": None,
        "openalex_result": None,
    }

    own_client = False
    if client is None:
        client = httpx.AsyncClient(timeout=6.0)
        own_client = True

    try:
        # 1. Search by DOI if available
        if doi:
            clean_doi = doi.replace("https://doi.org/", "").replace("http://doi.org/", "").strip()
            url = f"https://api.crossref.org/works/{urllib.parse.quote(clean_doi, safe='')}"
            try:
                resp = await client.get(url, headers=headers)
                if resp.status_code == 200:
                    data = resp.json().get("message", {})
                    api_title = data.get("title", [""])[0] if data.get("title") else ""
                    result["doi_match"] = True
                    result["verified_doi"] = clean_doi
                    result["source"] = "crossref_doi"
                    result["venue"] = data.get("container-title", [""])[0] if data.get("container-title") else None
                    if title and api_title:
                        result["title_match"] = _title_similarity(title, api_title) >= 0.75
                    else:
                        result["title_match"] = True
                    result["matched"] = True
                    result["status"] = "verified"

                    # Author match
                    api_authors = data.get("author", [])
                    if authors and api_authors:
                        last_names = [a.get("family", "").lower() for a in api_authors if "family" in a]
                        for author in authors:
                            last = author.split()[-1].lower()
                            if last in last_names:
                                result["author_match"] = True
                                break

                    result["crossref_result"] = {
                        "status": "found",
                        "title": api_title,
                        "doi": clean_doi,
                        "venue": result["venue"],
                    }
                    return result
                else:
                    result["crossref_result"] = {"status": f"http_{resp.status_code}"}
            except Exception as exc:
                logger.debug(f"Crossref DOI query failed: {exc}")
                result["crossref_result"] = {"status": "unavailable", "error": str(exc)}

        # 2. Search by Title via OpenAlex
        if title and len(title.strip()) >= 10:
            url = "https://api.openalex.org/works"
            params = {
                "filter": f"title.search:{title.strip()}",
                "select": "id,title,doi,publication_year,primary_location,authorships",
                "mailto": settings.api_user_agent_email,
            }
            try:
                resp = await client.get(url, params=params)
                if resp.status_code == 200:
                    data = resp.json()
                    candidates = data.get("results", [])
                    if candidates:
                        best = candidates[0]
                        cand_title = best.get("title", "")
                        sim = _title_similarity(title, cand_title)
                        if sim >= 0.80:
                            result["matched"] = True
                            result["status"] = "verified"
                            result["title_match"] = True
                            result["source"] = "openalex_title"
                            result["verified_doi"] = best.get("doi")
                            result["year"] = best.get("publication_year")
                            loc = best.get("primary_location") or {}
                            source_info = loc.get("source") or {}
                            result["venue"] = source_info.get("display_name")
                            if doi and best.get("doi"):
                                result["doi_match"] = doi.lower() in best["doi"].lower()

                            # Check authors in OpenAlex response
                            api_authorships = best.get("authorships", [])
                            if authors and api_authorships:
                                api_names = [
                                    a.get("author", {}).get("display_name", "").lower()
                                    for a in api_authorships
                                ]
                                for author in authors:
                                    last = author.split()[-1].lower()
                                    if any(last in name for name in api_names):
                                        result["author_match"] = True
                                        break

                            result["openalex_result"] = {
                                "status": "found",
                                "title": cand_title,
                                "doi": best.get("doi"),
                                "venue": result["venue"],
                            }
                            return result
                    result["openalex_result"] = {"status": "not_found"}
                else:
                    result["openalex_result"] = {"status": f"http_{resp.status_code}"}
            except Exception as exc:
                logger.debug(f"OpenAlex title query failed: {exc}")
                result["openalex_result"] = {"status": "unavailable", "error": str(exc)}

        # 3. Fallback: Search by Title via Crossref
        if not result["matched"] and title and len(title.strip()) >= 10:
            url = "https://api.crossref.org/works"
            params = {"query.bibliographic": title.strip(), "rows": 1}
            try:
                resp = await client.get(url, params=params, headers=headers)
                if resp.status_code == 200:
                    items = resp.json().get("message", {}).get("items", [])
                    if items:
                        best = items[0]
                        api_title = best.get("title", [""])[0] if best.get("title") else ""
                        if _title_similarity(title, api_title) >= 0.75:
                            result["matched"] = True
                            result["status"] = "verified"
                            result["title_match"] = True
                            result["source"] = "crossref_title"
                            result["verified_doi"] = best.get("DOI")
                            result["venue"] = best.get("container-title", [""])[0] if best.get("container-title") else None
                            api_authors = best.get("author", [])
                            if authors and api_authors:
                                last_names = [a.get("family", "").lower() for a in api_authors if "family" in a]
                                for author in authors:
                                    last = author.split()[-1].lower()
                                    if last in last_names:
                                        result["author_match"] = True
                                        break
                            result["crossref_result"] = {
                                "status": "found",
                                "title": api_title,
                                "doi": best.get("DOI"),
                                "venue": result["venue"],
                            }
                            return result
                    result["crossref_result"] = {"status": "not_found"}
            except Exception as exc:
                logger.debug(f"Crossref title query failed: {exc}")
                result["crossref_result"] = {"status": "unavailable", "error": str(exc)}

    finally:
        if own_client:
            await client.aclose()

    if not result["matched"]:
        oa_status = (result.get("openalex_result") or {}).get("status")
        cr_status = (result.get("crossref_result") or {}).get("status")
        if oa_status == "unavailable" or cr_status == "unavailable":
            result["status"] = "unavailable"

    return result
