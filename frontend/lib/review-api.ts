import { ManualReview, ProductReviewReport, ReviewApiError } from "./review-types";

const API_BASE =
  process.env.NEXT_PUBLIC_API_BASE ||
  (process.env.NEXT_PUBLIC_API_URL
    ? process.env.NEXT_PUBLIC_API_URL.replace(/\/api\/v1\/?$/, "")
    : "http://localhost:8000");

export async function analyzeProductUrl(
  url: string
): Promise<ProductReviewReport> {
  const res = await fetch(`${API_BASE}/api/v1/reviews/analyze`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ product_url: url }),
  });

  if (!res.ok) {
    let message = "Review analysis failed";
    try {
      const errorJson = await res.json();
      if (errorJson?.detail) {
        message = typeof errorJson.detail === "string"
          ? errorJson.detail
          : JSON.stringify(errorJson.detail);
      }
    } catch {
      // fallback to default message
    }
    const error: ReviewApiError = new Error(message);
    error.status = res.status;
    throw error;
  }

  return res.json();
}

export async function analyzeManualReviews(
  reviews: ManualReview[]
): Promise<ProductReviewReport> {
  const res = await fetch(`${API_BASE}/api/v1/reviews/analyze-manual`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ reviews }),
  });

  if (!res.ok) {
    let message = "Manual review analysis failed";
    try {
      const errorJson = await res.json();
      if (errorJson?.detail) {
        message = typeof errorJson.detail === "string"
          ? errorJson.detail
          : JSON.stringify(errorJson.detail);
      }
    } catch {
      // fallback to default message
    }
    const error: ReviewApiError = new Error(message);
    error.status = res.status;
    throw error;
  }

  return res.json();
}
