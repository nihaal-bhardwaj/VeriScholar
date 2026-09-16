import httpx
from httpx import AsyncClient
from app.core.config import get_settings
import urllib.parse

async def verify_by_title(title: str, client: AsyncClient) -> dict:
    """Verifies a paper by title using the OpenAlex API."""
    settings = get_settings()
    
    clean_title = title.strip()
    if not clean_title:
        return {"exists": False, "reason": "Empty title"}
        
    url = f"https://api.openalex.org/works"
    params = {
        "filter": f"title.search:{clean_title}",
        "select": "id,title,doi",
        "mailto": settings.api_user_agent_email
    }
    
    try:
        response = await client.get(url, params=params, timeout=5.0)
        
        if response.status_code == 200:
            data = response.json()
            if data.get("meta", {}).get("count", 0) > 0:
                # Found at least one match
                results = data.get("results", [])
                return {"exists": True, "title": results[0].get("title")}
            else:
                return {"exists": False, "reason": "No matches found in OpenAlex"}
                
    except httpx.RequestError as e:
        return {"exists": False, "reason": f"Request failed: {str(e)}"}
        
    return {"exists": False, "reason": f"Unexpected status {response.status_code}"}
