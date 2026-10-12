"""Product review scraper service using ScraperAPI."""

import logging
import re
import urllib.parse
from typing import Optional

from bs4 import BeautifulSoup
import httpx

from app.core.config import get_settings
from app.schemas.reviews import ScrapedReview, ScrapedReviewData

logger = logging.getLogger("mini-project.reviews.scraper")


class UnsupportedSiteError(Exception):
    """Raised when the product URL is from an unsupported domain."""


class ScraperTimeoutError(Exception):
    """Raised when ScraperAPI times out fetching the target URL."""


class ScraperAPIError(Exception):
    """Raised when ScraperAPI returns a non-200 response or gateway error."""


class ConfigurationError(Exception):
    """Raised when required scraper configuration (e.g. API key) is missing."""


SUPPORTED_DOMAINS = (
    "amazon.",
    "flipkart.com",
    "meesho.com",
    "ajio.com",
    "shopsy.in",
)


def detect_source_site(product_url: str) -> Optional[str]:
    """Detect the e-commerce source platform from URL hostname."""
    try:
        parsed = urllib.parse.urlparse(product_url.strip())
        hostname = (parsed.hostname or "").lower()
        if "amazon." in hostname:
            return "amazon"
        if "flipkart.com" in hostname:
            return "flipkart"
        if "meesho.com" in hostname:
            return "meesho"
        if "ajio.com" in hostname:
            return "ajio"
        if "shopsy.in" in hostname:
            return "shopsy"
    except Exception:
        pass
    return None


def validate_product_url(product_url: str) -> str:
    """Validate URL syntax and supported domains.

    Raises:
        ValueError: If URL is empty, not a string, or lacks valid scheme/domain.
        UnsupportedSiteError: If domain is not in supported list.
    """
    if not product_url or not isinstance(product_url, str) or not product_url.strip():
        raise ValueError("Product URL cannot be empty.")

    cleaned_url = product_url.strip()
    parsed = urllib.parse.urlparse(cleaned_url)
    if not parsed.scheme or not parsed.netloc:
        raise ValueError("Malformed URL: Missing scheme or host domain.")

    hostname = (parsed.hostname or "").lower()
    if not any(domain in hostname for domain in SUPPORTED_DOMAINS):
        raise UnsupportedSiteError(
            f"Unsupported domain '{hostname}'. Supported domains include Amazon, Flipkart, Meesho, Ajio, and Shopsy."
        )

    return cleaned_url


def _extract_product_title(soup: BeautifulSoup) -> Optional[str]:
    """Attempt to extract product title using common e-commerce selectors."""
    title_selectors = [
        "#productTitle",
        "h1#title",
        "span#productTitle",
        "h1.a-size-large",
        "span.B_NuCI",
        "h1._6EBuvT",
        "span.VU-ZEz",
        "h1[class*='ProductTitle']",
        "span[class*='ProductTitle']",
        "h1[class*='prod-title']",
        "h1[class*='prod-name']",
        "div[class*='prod-name']",
        "h1",
    ]
    for sel in title_selectors:
        elem = soup.select_one(sel)
        if elem:
            text = elem.get_text(strip=True)
            if text:
                return text
    return None


def _parse_rating(rating_str: str) -> Optional[int]:
    """Parse integer 1-5 rating from text like '5.0 out of 5 stars', '4/5', or '4'."""
    if not rating_str:
        return None
    match = re.search(r"\b([1-5])(?:\.0)?\b", rating_str)
    if match:
        try:
            return int(match.group(1))
        except ValueError:
            return None
    return None


# --- Modular Per-Site HTML Parsers ---


def _parse_amazon_reviews(soup: BeautifulSoup) -> list[ScrapedReview]:
    """Extract review cards from Amazon product pages."""
    cards = soup.select('[data-hook="review"]') or soup.select("div.review")
    reviews: list[ScrapedReview] = []

    for card in cards:
        text_elem = (
            card.select_one('[data-hook="review-body"]')
            or card.select_one(".review-text-content")
            or card.select_one(".review-text")
            or card.select_one("p")
        )
        if not text_elem:
            continue
        review_text = text_elem.get_text(" ", strip=True)
        if not review_text:
            continue

        author_elem = (
            card.select_one('[data-hook="review-author"]')
            or card.select_one(".a-profile-name")
            or card.select_one(".review-author")
        )
        reviewer_name = author_elem.get_text(strip=True) if author_elem else None

        rating_elem = (
            card.select_one('[data-hook="review-star-rating"]')
            or card.select_one('[data-hook="cmps-review-star-rating"]')
            or card.select_one("i.a-icon-star")
            or card.select_one("i.review-rating")
        )
        rating_raw = rating_elem.get_text(strip=True) if rating_elem else ""
        rating = _parse_rating(rating_raw)

        date_elem = card.select_one('[data-hook="review-date"]') or card.select_one(".review-date")
        review_date = date_elem.get_text(strip=True) if date_elem else None

        card_text = card.get_text(" ", strip=True).lower()
        vp_elem = card.select_one('[data-hook="avp-badge"]')
        verified_purchase = bool(vp_elem or "verified purchase" in card_text)

        reviews.append(
            ScrapedReview(
                review_text=review_text,
                reviewer_name=reviewer_name,
                rating=rating,
                review_date=review_date,
                verified_purchase=verified_purchase,
            )
        )
    return reviews


def _parse_flipkart_or_shopsy_reviews(soup: BeautifulSoup) -> list[ScrapedReview]:
    """Extract review cards from Flipkart and Shopsy product pages."""
    cards = (
        soup.select("div._16PBlm")
        or soup.select("div.cPHDOP div._27M-vq")
        or soup.select("div.col._2wzgFH")
        or soup.select("div._2wzgFH")
        or soup.select("div.EPCmJX")
    )
    reviews: list[ScrapedReview] = []

    for card in cards:
        text_elem = (
            card.select_one("div.t-ZTKy")
            or card.select_one("div._1mXcCf")
            or card.select_one("div.ZmyHeo")
            or card.select_one("p")
        )
        if not text_elem:
            continue
        review_text = text_elem.get_text(" ", strip=True)
        if not review_text:
            continue

        author_elem = (
            card.select_one("p._2sc7ZR")
            or card.select_one("p._2V5EHH")
            or card.select_one("p._2NsDsF")
            or card.select_one(".reviewer-name")
        )
        reviewer_name = author_elem.get_text(strip=True) if author_elem else None

        rating_elem = (
            card.select_one("div._3LWZlK")
            or card.select_one("div.XQDdHH")
            or card.select_one("div._1BLPMq")
            or card.select_one("div.hGSR34")
        )
        rating_raw = rating_elem.get_text(strip=True) if rating_elem else ""
        rating = _parse_rating(rating_raw)

        date_elem = card.select_one("p._2sc7ZR + p") or card.select_one("p._2NsDsF + p")
        review_date = date_elem.get_text(strip=True) if date_elem else None

        card_text = card.get_text(" ", strip=True).lower()
        verified_purchase = bool(
            "certified buyer" in card_text or "verified purchase" in card_text
        )

        reviews.append(
            ScrapedReview(
                review_text=review_text,
                reviewer_name=reviewer_name,
                rating=rating,
                review_date=review_date,
                verified_purchase=verified_purchase,
            )
        )
    return reviews


def _parse_meesho_reviews(soup: BeautifulSoup) -> list[ScrapedReview]:
    """Extract review cards from Meesho product pages using flexible multi-selectors."""
    cards = (
        soup.select('div[class*="ReviewCard"]')
        or soup.select('div[class*="review-card"]')
        or soup.select('div[class*="Comment__"]')
        or soup.select('div[class*="ReviewItem"]')
        or soup.select('div[class*="UserReview"]')
        or soup.select("div.review-item")
        or soup.select(".review-card")
    )
    reviews: list[ScrapedReview] = []

    for card in cards:
        text_elem = (
            card.select_one('p[class*="ReviewDescription"]')
            or card.select_one('span[class*="ReviewText"]')
            or card.select_one('p[class*="comment"]')
            or card.select_one('div[class*="review-text"]')
            or card.select_one("p")
        )
        if not text_elem:
            continue
        review_text = text_elem.get_text(" ", strip=True)
        if not review_text:
            continue

        author_elem = (
            card.select_one('span[class*="ReviewAuthor"]')
            or card.select_one('span[class*="UserName"]')
            or card.select_one('p[class*="author"]')
            or card.select_one(".reviewer-name")
        )
        reviewer_name = author_elem.get_text(strip=True) if author_elem else None

        rating_elem = (
            card.select_one('div[class*="RatingBadge"]')
            or card.select_one('span[class*="Rating"]')
            or card.select_one('span[class*="Badge"]')
            or card.select_one('div[class*="rating"]')
        )
        rating_raw = rating_elem.get_text(strip=True) if rating_elem else ""
        rating = _parse_rating(rating_raw)

        date_elem = (
            card.select_one('span[class*="ReviewDate"]')
            or card.select_one('span[class*="Date"]')
            or card.select_one('span[class*="time"]')
        )
        review_date = date_elem.get_text(strip=True) if date_elem else None

        card_text = card.get_text(" ", strip=True).lower()
        verified_purchase = bool(
            "verified" in card_text or "certified" in card_text
        )

        reviews.append(
            ScrapedReview(
                review_text=review_text,
                reviewer_name=reviewer_name,
                rating=rating,
                review_date=review_date,
                verified_purchase=verified_purchase,
            )
        )
    return reviews


def _parse_ajio_reviews(soup: BeautifulSoup) -> list[ScrapedReview]:
    """Extract review cards from Ajio product pages using flexible multi-selectors."""
    cards = (
        soup.select('div[class*="review-card"]')
        or soup.select('div[class*="ReviewCard"]')
        or soup.select('div[class*="user-review"]')
        or soup.select("div.customer-review")
        or soup.select('div[class*="feedback-card"]')
        or soup.select(".review-card")
    )
    reviews: list[ScrapedReview] = []

    for card in cards:
        text_elem = (
            card.select_one('div[class*="review-desc"]')
            or card.select_one('p[class*="review-body"]')
            or card.select_one('div[class*="comment-text"]')
            or card.select_one("div.review-text")
            or card.select_one("p")
        )
        if not text_elem:
            continue
        review_text = text_elem.get_text(" ", strip=True)
        if not review_text:
            continue

        author_elem = (
            card.select_one('span[class*="reviewer-name"]')
            or card.select_one('span[class*="author-name"]')
            or card.select_one('div[class*="user-name"]')
            or card.select_one("span.author")
        )
        reviewer_name = author_elem.get_text(strip=True) if author_elem else None

        rating_elem = (
            card.select_one('span[class*="rating-star"]')
            or card.select_one('div[class*="rating-badge"]')
            or card.select_one('div[class*="star-rating"]')
            or card.select_one("span.rating")
        )
        rating_raw = rating_elem.get_text(strip=True) if rating_elem else ""
        rating = _parse_rating(rating_raw)

        date_elem = (
            card.select_one('span[class*="review-date"]')
            or card.select_one('span[class*="date-posted"]')
        )
        review_date = date_elem.get_text(strip=True) if date_elem else None

        card_text = card.get_text(" ", strip=True).lower()
        verified_purchase = bool(
            "verified buyer" in card_text or "verified purchase" in card_text
        )

        reviews.append(
            ScrapedReview(
                review_text=review_text,
                reviewer_name=reviewer_name,
                rating=rating,
                review_date=review_date,
                verified_purchase=verified_purchase,
            )
        )
    return reviews


def _parse_generic_reviews(soup: BeautifulSoup) -> list[ScrapedReview]:
    """Fallback review extractor for general markup."""
    cards = (
        soup.select('[data-hook="review"]')
        or soup.select("div.review")
        or soup.select(".review-card")
        or soup.select('[itemprop="review"]')
        or soup.select(".user-review")
    )
    reviews: list[ScrapedReview] = []

    for card in cards:
        text_elem = (
            card.select_one('[data-hook="review-body"]')
            or card.select_one('[itemprop="reviewBody"]')
            or card.select_one(".review-text")
            or card.select_one("p")
        )
        if not text_elem:
            continue
        review_text = text_elem.get_text(" ", strip=True)
        if not review_text:
            continue

        author_elem = (
            card.select_one('[data-hook="review-author"]')
            or card.select_one('[itemprop="author"]')
            or card.select_one(".reviewer-name")
            or card.select_one(".author")
        )
        reviewer_name = author_elem.get_text(strip=True) if author_elem else None

        rating_elem = (
            card.select_one('[data-hook="review-star-rating"]')
            or card.select_one('[itemprop="ratingValue"]')
            or card.select_one(".rating")
        )
        rating_raw = rating_elem.get_text(strip=True) if rating_elem else ""
        rating = _parse_rating(rating_raw)

        date_elem = (
            card.select_one('[data-hook="review-date"]')
            or card.select_one('[itemprop="datePublished"]')
            or card.select_one(".review-date")
        )
        review_date = date_elem.get_text(strip=True) if date_elem else None

        card_text = card.get_text(" ", strip=True).lower()
        verified_purchase = bool("verified" in card_text)

        reviews.append(
            ScrapedReview(
                review_text=review_text,
                reviewer_name=reviewer_name,
                rating=rating,
                review_date=review_date,
                verified_purchase=verified_purchase,
            )
        )
    return reviews


def parse_reviews_from_html(html: str, product_url: str) -> ScrapedReviewData:
    """Parse product reviews and metadata from rendered HTML of a single product page."""
    soup = BeautifulSoup(html, "html.parser")
    product_title = _extract_product_title(soup)
    source_site = detect_source_site(product_url)

    scraped_reviews: list[ScrapedReview] = []

    # Route parsing through modular site functions with generic fallback
    if source_site == "amazon":
        scraped_reviews = _parse_amazon_reviews(soup) or _parse_generic_reviews(soup)
    elif source_site in ("flipkart", "shopsy"):
        scraped_reviews = _parse_flipkart_or_shopsy_reviews(soup) or _parse_generic_reviews(soup)
    elif source_site == "meesho":
        scraped_reviews = _parse_meesho_reviews(soup) or _parse_generic_reviews(soup)
    elif source_site == "ajio":
        scraped_reviews = _parse_ajio_reviews(soup) or _parse_generic_reviews(soup)
    else:
        scraped_reviews = _parse_generic_reviews(soup)

    if len(scraped_reviews) == 0:
        warning = (
            "No reviews were found on the product page. "
            "Could not parse reviews from this page. The site's structure may have changed "
            "or reviews may load dynamically after page load."
        )
    else:
        warning = (
            "Showing reviews from the product page preview. "
            "This product may have additional reviews not shown here."
        )

    return ScrapedReviewData(
        product_url=product_url,
        product_title=product_title,
        source_site=source_site,
        reviews=scraped_reviews,
        total_reviews_found=len(scraped_reviews),
        scrape_successful=True,
        warning=warning,
    )


# Alias for backward compatibility
parse_reviews_html = parse_reviews_from_html


def scrape_product_reviews(product_url: str) -> ScrapedReviewData:
    """Scrape reviews for an e-commerce product from its product page preview.

    Args:
        product_url: Valid e-commerce product URL (Amazon, Flipkart, Meesho, Ajio, Shopsy).

    Returns:
        ScrapedReviewData containing parsed reviews and preview warning.

    Raises:
        ValueError: If product_url is empty or malformed.
        UnsupportedSiteError: If product_url domain is not supported.
        ConfigurationError: If SCRAPERAPI_KEY is not configured.
        ScraperTimeoutError: If ScraperAPI times out.
        ScraperAPIError: If ScraperAPI returns non-200.
    """
    valid_url = validate_product_url(product_url)
    settings = get_settings()

    if not settings.scraperapi_key or not settings.scraperapi_key.strip():
        raise ConfigurationError(
            "SCRAPERAPI_KEY is not configured. Please set SCRAPERAPI_KEY in your environment or .env file."
        )

    endpoint = "http://api.scraperapi.com"
    params = {
        "api_key": settings.scraperapi_key,
        "url": valid_url,
        "render": "true",
    }

    try:
        # Note: Do NOT log params or URL containing api_key to preserve security
        with httpx.Client(timeout=30.0) as client:
            response = client.get(endpoint, params=params)

        if response.status_code != 200:
            raise ScraperAPIError(f"ScraperAPI returned status code {response.status_code}")

        html_content = response.text
        return parse_reviews_from_html(html_content, valid_url)

    except httpx.TimeoutException as exc:
        raise ScraperTimeoutError(
            f"ScraperAPI request timed out while fetching reviews for {valid_url}"
        ) from exc
    except (httpx.RequestError, httpx.HTTPError) as exc:
        # Avoid embedding raw request info that might expose api_key
        raise ScraperAPIError(f"ScraperAPI network request failed: {type(exc).__name__}") from exc
