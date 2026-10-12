export interface ReviewSignal {
  rule: string;
  severity: "high" | "medium" | "low";
  message: string;
}

export interface ReviewAnalysisResult {
  review_text: string;
  reviewer_name: string | null;
  rating: number | null;
  review_date?: string | null;
  verified_purchase: boolean | null;
  authenticity_score: number; // 0-100
  classification: "likely_genuine" | "uncertain" | "likely_fake";
  signals: ReviewSignal[];
  analyzed_by?: "llm" | "heuristics" | "llm+heuristics";
  reasoning?: string | null;
}

export interface ProductReviewReport {
  product_url: string;
  product_title: string | null;
  source_site?: string | null;
  total_reviews_analyzed: number;
  overall_trust_score: number; // 0-100, higher = more concern
  trust_level:
    | "low_trust_concern"
    | "moderate_concern"
    | "high_concern"
    | "critical_concern"
    | "insufficient_data";
  reviews: ReviewAnalysisResult[];
  batch_signals: ReviewSignal[];
  duplicate_review_count: number;
  summary: string;
  generated_at: string;
}

export interface ManualReview {
  review_text: string;
  rating: number | null;
  verified_purchase: boolean | null;
  reviewer_name?: string | null;
  review_date?: string | null;
}

export interface ReviewApiError extends Error {
  status?: number;
}
