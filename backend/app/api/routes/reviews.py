"""API routes for the Fake Review Detector."""

import logging
from fastapi import APIRouter, HTTPException, status

from app.schemas.reviews import (
    AnalyzeManualRequest,
    AnalyzeProductRequest,
    ProductReviewReport,
    ScrapedReview,
    ScrapedReviewData,
)
from app.services.reviews.review_report_generator import generate_review_report
from app.services.reviews.scraper import (
    ConfigurationError,
    ScraperAPIError,
    ScraperTimeoutError,
    UnsupportedSiteError,
    scrape_product_reviews,
)

logger = logging.getLogger("mini-project.reviews")

router = APIRouter(prefix="/reviews", tags=["reviews"])


@router.post(
    "/analyze",
    response_model=ProductReviewReport,
    status_code=status.HTTP_200_OK,
    summary="Scrape and analyze product reviews from e-commerce URL",
)
def analyze_product_reviews(payload: AnalyzeProductRequest) -> ProductReviewReport:
    """Scrape reviews from Amazon or Flipkart URL and generate an authenticity report."""
    try:
        scraped_data = scrape_product_reviews(payload.product_url)
        return generate_review_report(scraped_data)

    except (ValueError, UnsupportedSiteError) as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc

    except ScraperTimeoutError as exc:
        logger.warning("Scraper timeout for URL: %s", payload.product_url)
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail="The review scraper timed out while fetching reviews.",
        ) from exc

    except ScraperAPIError as exc:
        logger.error("ScraperAPI error: %s", str(exc))
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"External review scraping service failed: {str(exc)}",
        ) from exc

    except ConfigurationError as exc:
        logger.error("Review scraper configuration error: %s", str(exc))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Review scraping service is not properly configured.",
        ) from exc

    except Exception as exc:
        logger.exception("Unexpected error during review analysis")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred while analyzing reviews.",
        ) from exc


@router.post(
    "/analyze-manual",
    response_model=ProductReviewReport,
    status_code=status.HTTP_200_OK,
    summary="Analyze manually supplied product reviews",
)
def analyze_manual_reviews(payload: AnalyzeManualRequest) -> ProductReviewReport:
    """Analyze a batch of manually submitted reviews without scraping."""
    try:
        scraped_reviews = [
            ScrapedReview(
                review_text=item.review_text,
                reviewer_name=item.reviewer_name,
                rating=item.rating,
                review_date=item.review_date,
                verified_purchase=item.verified_purchase,
            )
            for item in payload.reviews
        ]

        scraped_data = ScrapedReviewData(
            product_url="manual-input",
            product_title=None,
            reviews=scraped_reviews,
            total_reviews_found=len(scraped_reviews),
            scrape_successful=True,
            warning=None if scraped_reviews else "No reviews submitted.",
        )

        return generate_review_report(scraped_data)

    except Exception as exc:
        logger.exception("Unexpected error during manual review analysis")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred while processing reviews.",
        ) from exc
