"""Tests for the health endpoint."""


def test_health_endpoint_succeeds(client):
    response = client.get("/api/v1/health")

    assert response.status_code == 200
    body = response.json()
    assert body == {
        "status": "healthy",
        "service": "mini-project-api",
        "version": "0.1.0",
    }
