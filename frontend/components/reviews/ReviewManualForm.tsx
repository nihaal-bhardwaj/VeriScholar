"use client";

import React, { useState } from "react";
import { ManualReview } from "../../lib/review-types";

interface ReviewManualFormProps {
  onSubmit: (reviews: ManualReview[]) => void;
  disabled?: boolean;
}

interface EditableReviewBlock {
  id: string;
  review_text: string;
  rating: number | null;
  verified_purchase: boolean;
}

export default function ReviewManualForm({ onSubmit, disabled }: ReviewManualFormProps) {
  const [blocks, setBlocks] = useState<EditableReviewBlock[]>([
    {
      id: "block-1",
      review_text: "",
      rating: 5,
      verified_purchase: false,
    },
  ]);
  const [submittedAttempt, setSubmittedAttempt] = useState(false);

  const addBlock = () => {
    setBlocks((prev) => [
      ...prev,
      {
        id: `block-${Date.now()}-${Math.random().toString(36).substring(2, 7)}`,
        review_text: "",
        rating: 5,
        verified_purchase: false,
      },
    ]);
  };

  const removeBlock = (index: number) => {
    if (blocks.length <= 1) return;
    setBlocks((prev) => prev.filter((_, i) => i !== index));
  };

  const updateField = <K extends keyof EditableReviewBlock>(
    index: number,
    field: K,
    value: EditableReviewBlock[K]
  ) => {
    setBlocks((prev) => {
      const next = [...prev];
      next[index] = { ...next[index], [field]: value };
      return next;
    });
  };

  // Check whether at least 1 block has non-empty review_text
  const hasAtLeastOneReview = blocks.some((b) => b.review_text.trim().length > 0);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setSubmittedAttempt(true);

    if (!hasAtLeastOneReview) return;

    // Filter down to non-empty reviews or send all valid reviews
    const validReviews: ManualReview[] = blocks
      .filter((b) => b.review_text.trim().length > 0)
      .map((b) => ({
        review_text: b.review_text.trim(),
        rating: b.rating,
        verified_purchase: b.verified_purchase,
      }));

    onSubmit(validReviews);
  };

  return (
    <form onSubmit={handleSubmit} className="w-full space-y-5 font-sans" noValidate>
      <div className="space-y-4">
        {blocks.map((block, index) => (
          <div
            key={block.id}
            className="p-4 sm:p-5 bg-[var(--rc-card)] border border-[var(--rc-border)] rounded-xl shadow-xs space-y-4 transition-all"
          >
            <div className="flex items-center justify-between gap-2 border-b border-[var(--rc-border)] pb-3">
              <span className="text-xs font-semibold uppercase tracking-wider text-[var(--rc-text-muted)]">
                Review #{index + 1}
              </span>
              {blocks.length > 1 && (
                <button
                  type="button"
                  onClick={() => removeBlock(index)}
                  disabled={disabled}
                  className="text-[var(--rc-text-muted)] hover:text-[var(--rc-danger)] p-1 rounded-md transition-colors cursor-pointer disabled:opacity-50"
                  aria-label={`Remove review #${index + 1}`}
                  title="Remove review"
                >
                  <svg
                    className="w-4 h-4"
                    viewBox="0 0 24 24"
                    fill="none"
                    stroke="currentColor"
                    strokeWidth="2"
                    strokeLinecap="round"
                    strokeLinejoin="round"
                  >
                    <line x1="18" y1="6" x2="6" y2="18" />
                    <line x1="6" y1="6" x2="18" y2="18" />
                  </svg>
                </button>
              )}
            </div>

            {/* Review Textarea */}
            <div>
              <label
                htmlFor={`review-text-${block.id}`}
                className="block text-xs sm:text-sm font-medium text-[var(--rc-text)] mb-1.5"
              >
                Review Text <span className="text-[var(--rc-danger)]">*</span>
              </label>
              <textarea
                id={`review-text-${block.id}`}
                rows={3}
                value={block.review_text}
                onChange={(e) => updateField(index, "review_text", e.target.value)}
                placeholder="Paste the full review comment here..."
                disabled={disabled}
                className="w-full px-3.5 py-2.5 bg-white text-[var(--rc-text)] placeholder-[var(--rc-text-muted)] border border-[var(--rc-border)] rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-[var(--rc-primary)] focus:border-[var(--rc-primary)] transition-all resize-y disabled:opacity-60"
              />
            </div>

            {/* Rating & Verified Purchase Row */}
            <div className="flex flex-wrap items-center justify-between gap-4 pt-1">
              {/* Star Rating */}
              <div>
                <label
                  id={`rating-label-${block.id}`}
                  className="block text-xs font-medium text-[var(--rc-text-muted)] mb-1"
                >
                  Star Rating (optional)
                </label>
                <div
                  role="radiogroup"
                  aria-labelledby={`rating-label-${block.id}`}
                  className="flex items-center gap-1"
                >
                  {[1, 2, 3, 4, 5].map((star) => {
                    const isSelected = (block.rating ?? 0) >= star;
                    return (
                      <button
                        key={star}
                        type="button"
                        role="radio"
                        aria-checked={block.rating === star}
                        aria-label={`${star} star${star > 1 ? "s" : ""}`}
                        disabled={disabled}
                        onClick={() => {
                          // Clicking the same star toggles to null if desired, or sets to star
                          updateField(
                            index,
                            "rating",
                            block.rating === star ? null : star
                          );
                        }}
                        onKeyDown={(e) => {
                          if (e.key === "ArrowRight" || e.key === "ArrowUp") {
                            e.preventDefault();
                            updateField(index, "rating", Math.min(5, (block.rating ?? 0) + 1));
                          } else if (e.key === "ArrowLeft" || e.key === "ArrowDown") {
                            e.preventDefault();
                            updateField(index, "rating", Math.max(1, (block.rating ?? 1) - 1));
                          }
                        }}
                        className="p-1 rounded text-amber-400 hover:text-amber-500 focus-visible:ring-2 focus-visible:ring-[var(--rc-primary)] transition-colors cursor-pointer disabled:opacity-60"
                      >
                        <svg
                          className="w-5 h-5"
                          viewBox="0 0 24 24"
                          fill={isSelected ? "currentColor" : "none"}
                          stroke="currentColor"
                          strokeWidth="1.8"
                          strokeLinecap="round"
                          strokeLinejoin="round"
                        >
                          <polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2" />
                        </svg>
                      </button>
                    );
                  })}
                  {block.rating !== null && (
                    <span className="text-xs text-[var(--rc-text-muted)] ml-1.5 font-medium">
                      {block.rating}/5
                    </span>
                  )}
                </div>
              </div>

              {/* Verified Purchase Checkbox */}
              <div className="flex items-center gap-2 pt-3 sm:pt-0">
                <input
                  id={`verified-${block.id}`}
                  type="checkbox"
                  checked={block.verified_purchase}
                  onChange={(e) => updateField(index, "verified_purchase", e.target.checked)}
                  disabled={disabled}
                  className="w-4 h-4 text-[var(--rc-primary)] border-[var(--rc-border)] rounded focus:ring-[var(--rc-primary)] cursor-pointer disabled:opacity-60"
                />
                <label
                  htmlFor={`verified-${block.id}`}
                  className="text-xs sm:text-sm text-[var(--rc-text)] font-medium cursor-pointer select-none"
                >
                  Verified purchase
                </label>
              </div>
            </div>
          </div>
        ))}
      </div>

      {submittedAttempt && !hasAtLeastOneReview && (
        <p role="alert" className="text-sm font-medium text-[var(--rc-danger)] flex items-center gap-1.5">
          <svg className="w-4 h-4 shrink-0" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <circle cx="12" cy="12" r="10" />
            <line x1="12" y1="8" x2="12" y2="12" />
            <line x1="12" y1="16" x2="12.01" y2="16" />
          </svg>
          <span>Please enter text for at least one review before analyzing.</span>
        </p>
      )}

      {/* Action Buttons */}
      <div className="flex flex-col sm:flex-row items-stretch sm:items-center justify-between gap-3 pt-2">
        <button
          type="button"
          onClick={addBlock}
          disabled={disabled}
          className="px-4 py-2.5 bg-white hover:bg-gray-50 text-[var(--rc-text)] border border-[var(--rc-border)] rounded-xl text-sm font-medium shadow-2xs hover:shadow-xs transition-all flex items-center justify-center gap-2 cursor-pointer disabled:opacity-60"
        >
          <svg
            className="w-4 h-4 text-[var(--rc-primary)]"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2.5"
            strokeLinecap="round"
          >
            <line x1="12" y1="5" x2="12" y2="19" />
            <line x1="5" y1="12" x2="19" y2="12" />
          </svg>
          <span>Add another review</span>
        </button>

        <button
          type="submit"
          disabled={disabled || !hasAtLeastOneReview}
          className="px-6 py-3 bg-[var(--rc-primary)] hover:bg-[var(--rc-primary-dark)] text-white font-medium rounded-xl shadow-md hover:shadow-lg transition-all flex items-center justify-center gap-2 text-sm sm:text-base cursor-pointer disabled:opacity-50 disabled:cursor-not-allowed focus-visible:ring-2 focus-visible:ring-[var(--rc-primary)] focus-visible:ring-offset-2"
        >
          <span>Analyze Reviews</span>
          <svg
            className="w-4 h-4"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2.2"
            strokeLinecap="round"
            strokeLinejoin="round"
          >
            <line x1="5" y1="12" x2="19" y2="12" />
            <polyline points="12 5 19 12 12 19" />
          </svg>
        </button>
      </div>
    </form>
  );
}
