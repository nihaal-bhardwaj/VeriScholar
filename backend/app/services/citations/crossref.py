import httpx
from httpx import AsyncClient
from app.core.config import get_settings
import urllib.parse
import re

async def verify_by_doi(doi: str, client: AsyncClient) -> dict:
    """Verifies a DOI using the Crossref API."""
    settings = get_settings()
    
    # Strip any extra URL bits from DOI if needed
    clean_doi = re.sub(r'https?://(?:dx\.)?doi\.org/', '', doi.strip())
    
    headers = {
        "User-Agent": f"MiniProject/1.0 (mailto:{settings.api_user_agent_email})"
    }
    
    url = f"https://api.crossref.org/works/{urllib.parse.quote(clean_doi, safe='')}"
    
    try:
        response = await client.get(url, headers=headers, timeout=5.0)
        
        if response.status_code == 200:
            data = response.json()
            if "message" in data:
                return {"exists": True, "title": data["message"].get("title", [""])[0]}
        elif response.status_code == 404:
            return {"exists": False, "reason": "Not found in Crossref"}
            
    except httpx.RequestError as e:
        return {"exists": False, "reason": f"Request failed: {str(e)}"}
        
    return {"exists": False, "reason": f"Unexpected status {response.status_code}"}
