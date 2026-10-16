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

  const hasAtLeastOneReview = blocks.some((b) => b.review_text.trim().length > 0);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setSubmittedAttempt(true);

    if (!hasAtLeastOneReview) return;

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
      <div className="text-xs text-[var(--text-faint)]">
        <span>Enter custom review texts below</span>
      </div>

      <div className="space-y-4">
        {blocks.map((block, index) => (
          <div
            key={block.id}
            className="p-4 sm:p-5 bg-zinc-900/80 border border-white/[0.08] rounded-xl shadow-md space-y-4 transition-all"
          >
            <div className="flex items-center justify-between gap-2 border-b border-white/[0.06] pb-3">
              <span className="text-xs font-semibold uppercase tracking-wider text-[var(--text-muted)] font-mono">
                Review #{index + 1}
              </span>
              {blocks.length > 1 && (
                <button
                  type="button"
                  onClick={() => removeBlock(index)}
                  disabled={disabled}
                  className="text-[var(--text-faint)] hover:text-rose-400 p-1 rounded-md transition-colors cursor-pointer disabled:opacity-50"
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
                className="block text-xs sm:text-sm font-medium text-[var(--text)] mb-1.5"
              >
                Review Text <span className="text-rose-400">*</span>
              </label>
              <textarea
                id={`review-text-${block.id}`}
                rows={3}
                value={block.review_text}
                onChange={(e) => updateField(index, "review_text", e.target.value)}
                placeholder="Paste review comment text here..."
                disabled={disabled}
                className="w-full px-3.5 py-2.5 bg-zinc-950/80 text-[var(--text)] placeholder-[var(--text-faint)] border border-white/[0.08] rounded-lg text-sm focus:outline-none focus:border-zinc-400 transition-all resize-y disabled:opacity-60"
              />
            </div>

            {/* Rating & Verified Purchase Row */}
            <div className="flex flex-wrap items-center justify-between gap-4 pt-1">
              {/* Star Rating */}
              <div>
                <label
                  id={`rating-label-${block.id}`}
                  className="block text-xs font-medium text-[var(--text-muted)] mb-1"
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
                          updateField(index, "rating", block.rating === star ? null : star);
                        }}
                        className="p-1 rounded text-amber-400 hover:text-amber-300 transition-colors cursor-pointer disabled:opacity-60"
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
                    <span className="text-xs text-[var(--text-muted)] ml-1.5 font-mono font-medium">
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
                  className="w-4 h-4 text-zinc-100 border-zinc-700 bg-zinc-900 rounded focus:ring-zinc-400 cursor-pointer disabled:opacity-60"
                />
                <label
                  htmlFor={`verified-${block.id}`}
                  className="text-xs sm:text-sm text-[var(--text-muted)] font-medium cursor-pointer select-none"
                >
                  Verified purchase
                </label>
              </div>
            </div>
          </div>
        ))}
      </div>

      {submittedAttempt && !hasAtLeastOneReview && (
        <p role="alert" className="text-xs font-medium text-rose-400 flex items-center gap-1.5">
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
          className="btn-secondary text-xs sm:text-sm py-2 px-4 cursor-pointer"
        >
          <svg
            className="w-4 h-4 text-zinc-300"
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
          className="btn-primary py-2.5 px-6 text-xs sm:text-sm cursor-pointer disabled:opacity-50"
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
