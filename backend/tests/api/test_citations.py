import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_citations_verify_endpoint_missing_payload():
    """Test standard 422 error on missing request body."""
    response = client.post("/api/v1/citations/verify", json={})
    assert response.status_code == 422

def test_citations_verify_endpoint_empty_references():
    """Test successful 200 response when no references are provided."""
    payload = {
        "analysis_id": "test-1234",
        "references": []
    }
    response = client.post("/api/v1/citations/verify", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "completed"
    assert data["verified"] == 0
    assert data["unresolved"] == 0
