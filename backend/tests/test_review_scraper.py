"""Tests for the product review scraper service."""

from unittest.mock import MagicMock, patch
import httpx
import pytest

from app.core.config import Settings
from app.services.reviews.scraper import (
    ConfigurationError,
    ScraperAPIError,
    ScraperTimeoutError,
    UnsupportedSiteError,
    detect_source_site,
    parse_reviews_from_html,
    parse_reviews_html,
    scrape_product_reviews,
)

SAMPLE_AMAZON_HTML = """
<html>
<head><title>Amazon.com: Wireless Headphones</title></head>
<body>
    <span id="productTitle">Wireless Noise-Canceling Over-Ear Headphones</span>
    <div data-hook="review" id="rev-1">
        <span class="a-profile-name" data-hook="review-author">Alice M.</span>
        <i data-hook="review-star-rating" class="a-icon-star">5.0 out of 5 stars</i>
        <span data-hook="review-date">January 15, 2024</span>
        <span data-hook="avp-badge">Verified Purchase</span>
        <span data-hook="review-body">
            The battery life is exceptional and the audio quality exceeded my expectations.
        </span>
    </div>
    <div data-hook="review" id="rev-2">
        <span class="a-profile-name" data-hook="review-author">Bob T.</span>
        <i data-hook="review-star-rating" class="a-icon-star">4.0 out of 5 stars</i>
        <span data-hook="review-date">January 16, 2024</span>
        <span data-hook="review-body">
            Great headphones for travel, though the fit was slightly snug on my ears.
        </span>
    </div>
</body>
</html>
"""

SAMPLE_EMPTY_HTML = """
<html>
<head><title>Amazon.com: Empty Product</title></head>
<body>
    <span id="productTitle">New Unreviewed Product</span>
    <div id="no-reviews-section">There are currently no customer reviews.</div>
</body>
</html>
"""

SAMPLE_MEESHO_HTML = """
<html>
<head><title>Meesho Product</title></head>
<body>
    <h1 class="ProductTitle">Comfort Cotton Kurti</h1>
    <div class="ReviewCard">
        <span class="ReviewAuthor">Priya S.</span>
        <div class="RatingBadge">5</div>
        <span class="ReviewDate">10 days ago</span>
        <span>Verified</span>
        <p class="ReviewDescription">Fabric quality is super soft and breathable for summer.</p>
    </div>
</body>
</html>
"""

SAMPLE_AJIO_HTML = """
<html>
<head><title>Ajio Product</title></head>
<body>
    <h1 class="prod-title">Denim Casual Jacket</h1>
    <div class="review-card">
        <span class="reviewer-name">Rahul K.</span>
        <span class="rating-star">4</span>
        <span class="review-date">2 weeks ago</span>
        <span>Verified Buyer</span>
        <div class="review-desc">Great fit and stylish design, perfect for winter evenings.</div>
    </div>
</body>
</html>
"""

SAMPLE_SHOPSY_HTML = """
<html>
<head><title>Shopsy Product</title></head>
<body>
    <h1 class="_6EBuvT">Everyday Running Shoes</h1>
    <div class="_16PBlm">
        <p class="_2sc7ZR">Vikram R.</p>
        <div class="_3LWZlK">5</div>
        <p class="_2sc7ZR + p">2024-02-10</p>
        <span>Certified Buyer</span>
        <div class="t-ZTKy">Lightweight shoes with excellent grip and arch support.</div>
    </div>
</body>
</html>
"""


def test_parse_reviews_html_extracts_fields_correctly():
    """Verify parse_reviews_html extracts title, authors, ratings, and body text."""
    url = "https://www.amazon.com/dp/B08N5WRWNW"
    data = parse_reviews_html(SAMPLE_AMAZON_HTML, url)

    assert data.product_url == url
    assert data.product_title == "Wireless Noise-Canceling Over-Ear Headphones"
    assert data.source_site == "amazon"
    assert data.total_reviews_found == 2
    assert len(data.reviews) == 2

    rev1 = data.reviews[0]
    assert rev1.reviewer_name == "Alice M."
    assert rev1.rating == 5
    assert rev1.review_date == "January 15, 2024"
    assert rev1.verified_purchase is True
    assert "battery life is exceptional" in rev1.review_text

    rev2 = data.reviews[1]
    assert rev2.reviewer_name == "Bob T."
    assert rev2.rating == 4
    assert rev2.verified_purchase is False
    assert "preview" in (data.warning or "").lower()


def test_parse_reviews_html_zero_reviews():
    """Verify HTML with zero reviews returns empty list and clean warning."""
    url = "https://www.amazon.com/dp/B08N5WRWNW"
    data = parse_reviews_html(SAMPLE_EMPTY_HTML, url)

    assert data.total_reviews_found == 0
    assert len(data.reviews) == 0
    assert data.scrape_successful is True
    assert data.warning is not None
    assert "No reviews" in data.warning


def test_parse_reviews_meesho():
    """Verify Meesho mock HTML parsing extracts review and metadata."""
    url = "https://www.meesho.com/comfort-cotton-kurti/p/12345"
    data = parse_reviews_from_html(SAMPLE_MEESHO_HTML, url)

    assert data.source_site == "meesho"
    assert data.product_title == "Comfort Cotton Kurti"
    assert data.total_reviews_found == 1
    rev = data.reviews[0]
    assert rev.reviewer_name == "Priya S."
    assert rev.rating == 5
    assert rev.verified_purchase is True
    assert "Fabric quality is super soft" in rev.review_text


def test_parse_reviews_ajio():
    """Verify Ajio mock HTML parsing extracts review and metadata."""
    url = "https://www.ajio.com/denim-casual-jacket/p/46012345"
    data = parse_reviews_from_html(SAMPLE_AJIO_HTML, url)

    assert data.source_site == "ajio"
    assert data.product_title == "Denim Casual Jacket"
    assert data.total_reviews_found == 1
    rev = data.reviews[0]
    assert rev.reviewer_name == "Rahul K."
    assert rev.rating == 4
    assert rev.verified_purchase is True
    assert "Great fit and stylish design" in rev.review_text


def test_parse_reviews_shopsy():
    """Verify Shopsy mock HTML parsing extracts review and metadata."""
    url = "https://www.shopsy.in/running-shoes/p/itm123456"
    data = parse_reviews_from_html(SAMPLE_SHOPSY_HTML, url)

    assert data.source_site == "shopsy"
    assert data.product_title == "Everyday Running Shoes"
    assert data.total_reviews_found == 1
    rev = data.reviews[0]
    assert rev.reviewer_name == "Vikram R."
    assert rev.rating == 5
    assert rev.verified_purchase is True
    assert "Lightweight shoes with excellent grip" in rev.review_text


def test_detect_source_site():
    """Verify source site detector recognizes all 5 platforms."""
    assert detect_source_site("https://www.amazon.in/dp/B08N5WRWNW") == "amazon"
    assert detect_source_site("https://www.flipkart.com/item/p/itm123") == "flipkart"
    assert detect_source_site("https://www.meesho.com/kurti/p/456") == "meesho"
    assert detect_source_site("https://www.ajio.com/jacket/p/789") == "ajio"
    assert detect_source_site("https://www.shopsy.in/shoes/p/012") == "shopsy"
    assert detect_source_site("https://www.randomstore.com/item") is None


def test_scrape_product_reviews_valid_amazon_mocked():
    """Valid Amazon URL with mocked successful response returns parsed reviews."""
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.text = SAMPLE_AMAZON_HTML

    dummy_settings = Settings(scraperapi_key="test_api_key_12345")

    with patch("app.services.reviews.scraper.get_settings", return_value=dummy_settings), \
         patch("httpx.Client.get", return_value=mock_resp) as mock_get:
        result = scrape_product_reviews("https://www.amazon.com/dp/B08N5WRWNW")

        assert result.scrape_successful is True
        assert result.total_reviews_found == 2
        mock_get.assert_called_once()
        args, kwargs = mock_get.call_args
        assert kwargs["params"]["api_key"] == "test_api_key_12345"


def test_scrape_product_reviews_unsupported_domain():
    """Unsupported domain raises UnsupportedSiteError listing all 5 supported platforms."""
    dummy_settings = Settings(scraperapi_key="test_key")
    with patch("app.services.reviews.scraper.get_settings", return_value=dummy_settings):
        with pytest.raises(UnsupportedSiteError) as exc_info:
            scrape_product_reviews("https://www.ebay.com/itm/123456789")

        msg = str(exc_info.value)
        assert "Unsupported domain" in msg
        assert "Amazon" in msg
        assert "Flipkart" in msg
        assert "Meesho" in msg
        assert "Ajio" in msg
        assert "Shopsy" in msg


def test_scrape_product_reviews_empty_or_malformed_url():
    """Empty or malformed URL raises ValueError before calling API."""
    with pytest.raises(ValueError):
        scrape_product_reviews("")

    with pytest.raises(ValueError):
        scrape_product_reviews("   ")

    with pytest.raises(ValueError):
        scrape_product_reviews("not-a-url")


def test_scrape_product_reviews_missing_api_key():
    """Missing SCRAPERAPI_KEY raises ConfigurationError."""
    empty_settings = Settings(scraperapi_key="")
    with patch("app.services.reviews.scraper.get_settings", return_value=empty_settings):
        with pytest.raises(ConfigurationError) as exc_info:
            scrape_product_reviews("https://www.amazon.com/dp/B08N5WRWNW")

        assert "SCRAPERAPI_KEY is not configured" in str(exc_info.value)


def test_scrape_product_reviews_timeout_error():
    """ScraperAPI timeout raises ScraperTimeoutError."""
    dummy_settings = Settings(scraperapi_key="test_key")
    with patch("app.services.reviews.scraper.get_settings", return_value=dummy_settings), \
         patch("httpx.Client.get", side_effect=httpx.TimeoutException("Read timed out")):
        with pytest.raises(ScraperTimeoutError) as exc_info:
            scrape_product_reviews("https://www.amazon.com/dp/B08N5WRWNW")

        assert "timed out" in str(exc_info.value)
        assert "test_key" not in str(exc_info.value)


def test_scrape_product_reviews_non_200_status():
    """ScraperAPI returning non-200 raises ScraperAPIError with status code."""
    mock_resp = MagicMock()
    mock_resp.status_code = 403
    mock_resp.text = "Forbidden - monthly quota exceeded"

    dummy_settings = Settings(scraperapi_key="test_key")
    with patch("app.services.reviews.scraper.get_settings", return_value=dummy_settings), \
         patch("httpx.Client.get", return_value=mock_resp):
        with pytest.raises(ScraperAPIError) as exc_info:
            scrape_product_reviews("https://www.amazon.com/dp/B08N5WRWNW")

        assert "403" in str(exc_info.value)
        assert "test_key" not in str(exc_info.value)
