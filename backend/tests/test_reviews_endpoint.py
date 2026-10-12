"""Tests for review analysis API endpoints."""

from unittest.mock import patch
from fastapi.testclient import TestClient

from app.main import app
from app.schemas.reviews import ScrapedReview, ScrapedReviewData
from app.services.reviews.scraper import (
    ScraperAPIError,
    ScraperTimeoutError,
    UnsupportedSiteError,
)

client = TestClient(app)


def test_post_analyze_valid_url_mocked_success():
    """POST /api/v1/reviews/analyze with valid URL returns 200 and ProductReviewReport."""
    mock_scraped = ScrapedReviewData(
        product_url="https://www.amazon.com/dp/B08N5WRWNW",
        product_title="Mocked Product",
        reviews=[
            ScrapedReview(
                review_text="The battery life is stellar and packaging was neat.",
                reviewer_name="User1",
                rating=5,
                verified_purchase=True,
            )
        ],
        total_reviews_found=1,
        scrape_successful=True,
    )

    with patch("app.api.routes.reviews.scrape_product_reviews", return_value=mock_scraped):
        response = client.post(
            "/api/v1/reviews/analyze",
            json={"product_url": "https://www.amazon.com/dp/B08N5WRWNW"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["product_url"] == "https://www.amazon.com/dp/B08N5WRWNW"
        assert data["total_reviews_analyzed"] == 1
        assert "overall_trust_score" in data
        assert "trust_level" in data
        assert len(data["reviews"]) == 1


def test_post_analyze_unsupported_url_returns_400():
    """POST /api/v1/reviews/analyze with unsupported site returns 400 Bad Request."""
    response = client.post(
        "/api/v1/reviews/analyze",
        json={"product_url": "https://www.ebay.com/itm/123456789"},
    )

    assert response.status_code == 400
    err = response.json()
    assert "Unsupported domain" in err.get("detail", "") or "Unsupported domain" in err.get("error", "")


def test_post_analyze_missing_field_returns_422():
    """POST /api/v1/reviews/analyze with missing product_url field returns 422 Unprocessable Entity."""
    response = client.post(
        "/api/v1/reviews/analyze",
        json={"wrong_field": "test"},
    )

    assert response.status_code == 422


def test_post_analyze_timeout_returns_504():
    """POST /api/v1/reviews/analyze returns 504 Gateway Timeout when scraper times out."""
    with patch(
        "app.api.routes.reviews.scrape_product_reviews",
        side_effect=ScraperTimeoutError("Timed out"),
    ):
        response = client.post(
            "/api/v1/reviews/analyze",
            json={"product_url": "https://www.amazon.com/dp/B08N5WRWNW"},
        )

        assert response.status_code == 504
        assert "timed out" in response.json().get("detail", "").lower()


def test_post_analyze_scraper_api_error_returns_502():
    """POST /api/v1/reviews/analyze returns 502 Bad Gateway when ScraperAPI fails."""
    with patch(
        "app.api.routes.reviews.scrape_product_reviews",
        side_effect=ScraperAPIError("ScraperAPI returned status code 403"),
    ):
        response = client.post(
            "/api/v1/reviews/analyze",
            json={"product_url": "https://www.amazon.com/dp/B08N5WRWNW"},
        )

        assert response.status_code == 502
        assert "ScraperAPI returned status code 403" in response.json().get("detail", "")


def test_post_analyze_manual_valid_reviews_returns_200():
    """POST /api/v1/reviews/analyze-manual returns 200 and analyzed report."""
    payload = {
        "reviews": [
            {
                "review_text": "Great battery life and clear screen. The delivery was on time.",
                "reviewer_name": "John Doe",
                "rating": 5,
                "review_date": "2024-03-01",
                "verified_purchase": True,
            },
            {
                "review_text": "Average material quality and slightly loose fit.",
                "reviewer_name": "Jane Smith",
                "rating": 3,
                "review_date": "2024-03-02",
                "verified_purchase": True,
            },
        ]
    }

    response = client.post("/api/v1/reviews/analyze-manual", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["total_reviews_analyzed"] == 2
    assert len(data["reviews"]) == 2
    assert "overall_trust_score" in data
    assert "trust_level" in data


def test_post_analyze_manual_empty_reviews_returns_200_insufficient_data():
    """POST /api/v1/reviews/analyze-manual with empty list returns 200 with insufficient_data report."""
    response = client.post(
        "/api/v1/reviews/analyze-manual",
        json={"reviews": []},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["total_reviews_analyzed"] == 0
    assert data["overall_trust_score"] == 0.0
    assert data["trust_level"] == "insufficient_data"
    assert "No reviews were found" in data["summary"]
