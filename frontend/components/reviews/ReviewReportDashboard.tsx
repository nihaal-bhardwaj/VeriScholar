"use client";

import React, { useMemo, useState } from "react";
import {
  ProductReviewReport,
  ReviewAnalysisResult,
  ReviewSignal,
} from "../../lib/review-types";

interface ReviewReportDashboardProps {
  data: ProductReviewReport;
  onReset: () => void;
}

type FilterClassification = "all" | "likely_genuine" | "uncertain" | "likely_fake";

export default function ReviewReportDashboard({
  data,
  onReset,
}: ReviewReportDashboardProps) {
  const [filter, setFilter] = useState<FilterClassification>("all");
  const [visibleCount, setVisibleCount] = useState(10);
  const [expandedReviews, setExpandedReviews] = useState<Record<number, boolean>>({});
  const [expandedSignals, setExpandedSignals] = useState<Record<number, boolean>>({});

  // Calculations for circular progress ring
  const isInsufficient = data.trust_level === "insufficient_data";
  const trustPercent = isInsufficient
    ? 0
    : Math.max(0, Math.min(100, Math.round(100 - data.overall_trust_score)));

  // SVG dimensions
  const size = 150;
  const strokeWidth = 10;
  const radius = (size - strokeWidth) / 2;
  const circumference = 2 * Math.PI * radius;
  const strokeDashoffset = isInsufficient
    ? circumference
    : circumference - (trustPercent / 100) * circumference;

  // Ring & badge style mappings
  const getThemeConfig = () => {
    switch (data.trust_level) {
      case "low_trust_concern":
        return {
          strokeColor: "#16A34A",
          badgeBg: "bg-emerald-100 text-emerald-800 border-emerald-200",
          label: "Looks Trustworthy",
        };
      case "moderate_concern":
        return {
          strokeColor: "#F59E0B",
          badgeBg: "bg-amber-100 text-amber-800 border-amber-200",
          label: "Some Concerns",
        };
      case "high_concern":
        return {
          strokeColor: "#DC2626",
          badgeBg: "bg-red-100 text-red-800 border-red-200",
          label: "Many Red Flags",
        };
      case "critical_concern":
        return {
          strokeColor: "#991B1B",
          badgeBg: "bg-rose-100 text-rose-900 border-rose-200",
          label: "Highly Suspicious",
        };
      case "insufficient_data":
      default:
        return {
          strokeColor: "#9CA3AF",
          badgeBg: "bg-gray-100 text-gray-700 border-gray-200",
          label: "Not Enough Data",
        };
    }
  };

  const themeConfig = getThemeConfig();

  // Filtered reviews
  const filteredReviews = useMemo(() => {
    if (filter === "all") return data.reviews;
    return data.reviews.filter((r) => r.classification === filter);
  }, [data.reviews, filter]);

  const displayedReviews = filteredReviews.slice(0, visibleCount);

  const toggleExpandReview = (idx: number) => {
    setExpandedReviews((prev) => ({ ...prev, [idx]: !prev[idx] }));
  };

  const toggleExpandSignals = (idx: number) => {
    setExpandedSignals((prev) => ({ ...prev, [idx]: !prev[idx] }));
  };

  const getSeverityBadge = (sev: "high" | "medium" | "low") => {
    if (sev === "high") {
      return { dot: "bg-red-500", label: "High" };
    }
    if (sev === "medium") {
      return { dot: "bg-amber-500", label: "Medium" };
    }
    return { dot: "bg-blue-500", label: "Low" };
  };

  const getClassificationPill = (cls: ReviewAnalysisResult["classification"]) => {
    switch (cls) {
      case "likely_genuine":
        return (
          <span className="px-2.5 py-1 text-xs font-semibold rounded-full bg-emerald-100 text-emerald-800 border border-emerald-200">
            Likely Genuine
          </span>
        );
      case "uncertain":
        return (
          <span className="px-2.5 py-1 text-xs font-semibold rounded-full bg-amber-100 text-amber-800 border border-amber-200">
            Uncertain
          </span>
        );
      case "likely_fake":
      default:
        return (
          <span className="px-2.5 py-1 text-xs font-semibold rounded-full bg-red-100 text-red-800 border border-red-200">
            Likely Fake
          </span>
        );
    }
  };

  return (
    <div className="w-full max-w-4xl mx-auto font-sans space-y-8 pb-12">
      {/* Top Header Controls */}
      <div className="flex items-center justify-between gap-4">
        <div>
          <h2 className="text-xl sm:text-2xl font-bold text-[var(--rc-text)] tracking-tight">
            Review Authenticity Report
          </h2>
          {data.product_title && (
            <p className="text-sm text-[var(--rc-text-muted)] line-clamp-1 mt-0.5">
              {data.product_title}
            </p>
          )}
        </div>
        <button
          type="button"
          onClick={onReset}
          className="px-4 py-2 bg-white hover:bg-gray-50 text-[var(--rc-text)] border border-[var(--rc-border)] rounded-xl text-xs sm:text-sm font-medium shadow-2xs hover:shadow-xs transition-all flex items-center gap-1.5 cursor-pointer shrink-0"
        >
          <svg
            className="w-3.5 h-3.5 text-[var(--rc-primary)]"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
            strokeLinecap="round"
            strokeLinejoin="round"
          >
            <polyline points="1 4 1 10 7 10" />
            <path d="M3.51 15a9 9 0 1 0 2.13-9.36L1 10" />
          </svg>
          <span>Check Another</span>
        </button>
      </div>

      {/* TOP SECTION — Trust Score Hero Card */}
      <section
        aria-label="Overall Trust Score"
        className="p-6 sm:p-8 bg-[var(--rc-card)] border border-[var(--rc-border)] rounded-2xl shadow-md text-center space-y-6"
      >
        {/* Animated Circular Progress Ring */}
        <div className="relative w-[150px] h-[150px] mx-auto flex items-center justify-center">
          <svg className="w-full h-full -rotate-90 transform" viewBox={`0 0 ${size} ${size}`}>
            {/* Background track */}
            <circle
              cx={size / 2}
              cy={size / 2}
              r={radius}
              stroke="#E5E7EB"
              strokeWidth={strokeWidth}
              fill="transparent"
            />
            {/* Progress Stroke */}
            <circle
              cx={size / 2}
              cy={size / 2}
              r={radius}
              stroke={themeConfig.strokeColor}
              strokeWidth={strokeWidth}
              strokeDasharray={circumference}
              strokeDashoffset={strokeDashoffset}
              strokeLinecap="round"
              fill="transparent"
              className="transition-[stroke-dashoffset] duration-1000 ease-out"
            />
          </svg>

          {/* Value Display */}
          <div className="absolute inset-0 flex flex-col items-center justify-center text-center">
            {isInsufficient ? (
              <span className="text-3xl font-extrabold text-[var(--rc-text-muted)] tracking-tight">
                --
              </span>
            ) : (
              <>
                <span className="text-3xl sm:text-4xl font-extrabold text-[var(--rc-text)] tracking-tight">
                  {trustPercent}%
                </span>
                <span className="text-[11px] uppercase font-semibold text-[var(--rc-text-muted)] tracking-wider">
                  Trust Score
                </span>
              </>
            )}
          </div>
        </div>

        {/* Badge & Summary */}
        <div className="space-y-3 max-w-xl mx-auto">
          <div>
            <span
              className={`inline-block px-4 py-1.5 rounded-full text-sm font-semibold border ${themeConfig.badgeBg}`}
            >
              {themeConfig.label}
            </span>
          </div>

          <p className="text-sm sm:text-base text-[var(--rc-text)] leading-relaxed font-normal">
            {data.summary}
          </p>

          {/* Small Stat Row */}
          <div className="flex flex-wrap items-center justify-center gap-4 text-xs font-medium text-[var(--rc-text-muted)] pt-2 border-t border-[var(--rc-border)]">
            <span className="flex items-center gap-1.5">
              <svg className="w-4 h-4 text-[var(--rc-primary)]" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z" />
              </svg>
              {data.total_reviews_analyzed} {data.total_reviews_analyzed === 1 ? "review" : "reviews"} analyzed
            </span>
            {data.duplicate_review_count > 0 && (
              <>
                <span aria-hidden="true">•</span>
                <span className="text-[var(--rc-danger)] flex items-center gap-1.5">
                  <svg className="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <rect x="9" y="9" width="13" height="13" rx="2" ry="2" />
                    <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1" />
                  </svg>
                  {data.duplicate_review_count} flagged as duplicate
                </span>
              </>
            )}
          </div>
        </div>
      </section>

      {/* MIDDLE SECTION — Batch Signals (if any) */}
      {data.batch_signals && data.batch_signals.length > 0 && (
        <section aria-labelledby="batch-signals-heading" className="space-y-3">
          <h3
            id="batch-signals-heading"
            className="text-base sm:text-lg font-bold text-[var(--rc-text)] tracking-tight flex items-center gap-2"
          >
            <span>Pattern-level findings</span>
            <span className="text-xs px-2 py-0.5 rounded-full bg-amber-100 text-amber-800 font-semibold">
              {data.batch_signals.length}
            </span>
          </h3>

          <div className="space-y-2.5">
            {data.batch_signals.map((signal: ReviewSignal, idx: number) => {
              const isHighOrMed = signal.severity === "high" || signal.severity === "medium";
              const borderClass =
                signal.severity === "high"
                  ? "border-l-red-500 bg-red-50/70"
                  : signal.severity === "medium"
                  ? "border-l-amber-500 bg-amber-50/70"
                  : "border-l-blue-500 bg-blue-50/70";

              return (
                <div
                  key={`batch-signal-${idx}`}
                  className={`p-3.5 sm:p-4 rounded-lg border border-[var(--rc-border)] border-l-4 ${borderClass} flex items-start gap-3 transition-all`}
                >
                  <div className="shrink-0 pt-0.5">
                    {isHighOrMed ? (
                      <svg
                        className="w-5 h-5 text-amber-600"
                        viewBox="0 0 24 24"
                        fill="none"
                        stroke="currentColor"
                        strokeWidth="2"
                        strokeLinecap="round"
                        strokeLinejoin="round"
                      >
                        <path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z" />
                        <line x1="12" y1="9" x2="12" y2="13" />
                        <line x1="12" y1="17" x2="12.01" y2="17" />
                      </svg>
                    ) : (
                      <svg
                        className="w-5 h-5 text-blue-600"
                        viewBox="0 0 24 24"
                        fill="none"
                        stroke="currentColor"
                        strokeWidth="2"
                        strokeLinecap="round"
                        strokeLinejoin="round"
                      >
                        <circle cx="12" cy="12" r="10" />
                        <line x1="12" y1="16" x2="12" y2="12" />
                        <line x1="12" y1="8" x2="12.01" y2="8" />
                      </svg>
                    )}
                  </div>
                  <div className="flex-1 text-sm text-[var(--rc-text)] font-medium leading-relaxed">
                    {signal.message}
                  </div>
                </div>
              );
            })}
          </div>
        </section>
      )}

      {/* BOTTOM SECTION — Individual Reviews List */}
      <section aria-labelledby="individual-reviews-heading" className="space-y-4">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
          <h3
            id="individual-reviews-heading"
            className="text-base sm:text-lg font-bold text-[var(--rc-text)] tracking-tight"
          >
            Review-by-review breakdown
          </h3>

          {/* Filter Pills */}
          <div className="flex flex-wrap items-center gap-1.5" role="group" aria-label="Filter reviews by classification">
            {(
              [
                { id: "all", label: "All" },
                { id: "likely_genuine", label: "Likely Genuine" },
                { id: "uncertain", label: "Uncertain" },
                { id: "likely_fake", label: "Likely Fake" },
              ] as const
            ).map((tab) => {
              const count =
                tab.id === "all"
                  ? data.reviews.length
                  : data.reviews.filter((r) => r.classification === tab.id).length;

              const active = filter === tab.id;
              return (
                <button
                  key={tab.id}
                  type="button"
                  onClick={() => {
                    setFilter(tab.id);
                    setVisibleCount(10);
                  }}
                  className={`px-3 py-1.5 rounded-full text-xs font-semibold transition-all cursor-pointer flex items-center gap-1.5 ${
                    active
                      ? "bg-[var(--rc-primary)] text-white shadow-xs"
                      : "bg-white text-[var(--rc-text-muted)] hover:text-[var(--rc-text)] border border-[var(--rc-border)]"
                  }`}
                >
                  <span>{tab.label}</span>
                  <span
                    className={`px-1.5 py-0.2 rounded-full text-[10px] ${
                      active ? "bg-white/20 text-white" : "bg-gray-100 text-gray-600"
                    }`}
                  >
                    {count}
                  </span>
                </button>
              );
            })}
          </div>
        </div>

        {/* Reviews Cards List */}
        {displayedReviews.length === 0 ? (
          <div className="p-8 text-center bg-white border border-[var(--rc-border)] rounded-xl text-sm text-[var(--rc-text-muted)]">
            No reviews matching the &quot;{filter.replace("_", " ")}&quot; filter.
          </div>
        ) : (
          <div className="space-y-3.5">
            {displayedReviews.map((review: ReviewAnalysisResult, idx: number) => {
              const isLong = review.review_text.length > 200;
              const isExpanded = !!expandedReviews[idx];
              const textToShow =
                isLong && !isExpanded
                  ? `${review.review_text.substring(0, 200)}...`
                  : review.review_text;

              const showSignals = !!expandedSignals[idx];
              const suspicionScore = Math.round(review.authenticity_score);

              return (
                <div
                  key={`review-${idx}`}
                  className="p-4 sm:p-5 bg-[var(--rc-card)] border border-[var(--rc-border)] rounded-lg shadow-2xs hover:shadow-xs transition-shadow space-y-3"
                >
                  {/* Top line: rating, verified badge, analyzed_by badge & classification */}
                  <div className="flex items-start justify-between gap-3">
                    <div className="flex flex-wrap items-center gap-2">
                      {/* Stars */}
                      {review.rating !== null && (
                        <div className="flex items-center gap-0.5 text-amber-400" aria-label={`${review.rating} out of 5 stars`}>
                          {[1, 2, 3, 4, 5].map((star) => (
                            <svg
                              key={star}
                              className="w-4 h-4"
                              viewBox="0 0 24 24"
                              fill={(review.rating ?? 0) >= star ? "currentColor" : "none"}
                              stroke="currentColor"
                              strokeWidth="1.8"
                            >
                              <polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2" />
                            </svg>
                          ))}
                        </div>
                      )}

                      {/* Verified Badge */}
                      {review.verified_purchase && (
                        <span className="px-2 py-0.5 text-[11px] font-semibold rounded-md bg-emerald-50 text-emerald-700 border border-emerald-200 inline-flex items-center gap-1">
                          <svg className="w-3 h-3" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
                            <polyline points="20 6 9 17 4 12" />
                          </svg>
                          Verified Purchase
                        </span>
                      )}

                      {review.reviewer_name && (
                        <span className="text-xs text-[var(--rc-text-muted)] font-medium">
                          by {review.reviewer_name}
                        </span>
                      )}
                    </div>

                    {/* Right side: Analyzed By & Classification Pill */}
                    <div className="shrink-0 flex items-center gap-2">
                      {review.analyzed_by === "heuristics" ? (
                        <span className="px-2 py-0.5 text-[10px] font-medium rounded-full bg-gray-100 text-gray-600 border border-gray-200">
                          Rule-based
                        </span>
                      ) : (
                        <span className="px-2 py-0.5 text-[10px] font-medium rounded-full bg-indigo-50 text-indigo-700 border border-indigo-200">
                          AI Analysis
                        </span>
                      )}
                      {getClassificationPill(review.classification)}
                    </div>
                  </div>

                  {/* Review text */}
                  <div className="text-sm text-[var(--rc-text)] leading-relaxed font-normal">
                    <p className="whitespace-pre-line">{textToShow}</p>
                    {isLong && (
                      <button
                        type="button"
                        onClick={() => toggleExpandReview(idx)}
                        className="text-xs font-semibold text-[var(--rc-primary)] hover:underline mt-1 cursor-pointer"
                      >
                        {isExpanded ? "Show less" : "Show more"}
                      </button>
                    )}
                  </div>

                  {/* Suspicion score & Signals footer */}
                  <div className="flex flex-wrap items-center justify-between gap-2 pt-2 border-t border-[var(--rc-border)] text-xs text-[var(--rc-text-muted)]">
                    <span className="font-medium">
                      Suspicion score:{" "}
                      <span className="font-bold text-[var(--rc-text)]">
                        {suspicionScore}/100
                      </span>
                    </span>

                    {(review.signals.length > 0 || Boolean(review.reasoning)) && (
                      <button
                        type="button"
                        onClick={() => toggleExpandSignals(idx)}
                        className="font-semibold text-[var(--rc-primary)] hover:underline flex items-center gap-1 cursor-pointer"
                        aria-expanded={showSignals}
                      >
                        <span>Why?</span>
                        <svg
                          className={`w-3.5 h-3.5 transform transition-transform ${showSignals ? "rotate-180" : ""}`}
                          viewBox="0 0 24 24"
                          fill="none"
                          stroke="currentColor"
                          strokeWidth="2"
                        >
                          <polyline points="6 9 12 15 18 9" />
                        </svg>
                      </button>
                    )}
                  </div>

                  {/* Expandable "Why?" drawer */}
                  {(review.signals.length > 0 || Boolean(review.reasoning)) && showSignals && (
                    <div className="p-3.5 bg-gray-50 rounded-lg border border-[var(--rc-border)] space-y-2.5 mt-2 text-xs">
                      {/* LLM Reasoning if available */}
                      {review.reasoning && (
                        <div className="space-y-1">
                          <p className="font-semibold text-indigo-900">AI Assessment:</p>
                          <p className="text-gray-700 leading-relaxed">{review.reasoning}</p>
                        </div>
                      )}

                      {/* Triggered heuristic/LLM signals */}
                      {review.signals.length > 0 && (
                        <div className={`space-y-1.5 ${review.reasoning ? "pt-2 border-t border-gray-200" : ""}`}>
                          <p className="font-semibold text-[var(--rc-text)]">
                            Triggered signals:
                          </p>
                          <ul className="space-y-1 text-[var(--rc-text)]">
                            {review.signals.map((sig, sIdx) => {
                              const badge = getSeverityBadge(sig.severity);
                              return (
                                <li key={sIdx} className="flex items-start gap-2">
                                  <span
                                    className={`w-2 h-2 rounded-full mt-1 shrink-0 ${badge.dot}`}
                                    aria-label={`Severity: ${badge.label}`}
                                    title={`Severity: ${badge.label}`}
                                  />
                                  <span>{sig.message}</span>
                                </li>
                              );
                            })}
                          </ul>
                        </div>
                      )}
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        )}

        {/* Load More Button */}
        {filteredReviews.length > visibleCount && (
          <div className="text-center pt-2">
            <button
              type="button"
              onClick={() => setVisibleCount((prev) => prev + 10)}
              className="px-5 py-2.5 bg-white hover:bg-gray-50 text-[var(--rc-text)] border border-[var(--rc-border)] rounded-xl text-sm font-medium shadow-2xs hover:shadow-xs transition-all cursor-pointer"
            >
              Show more reviews ({filteredReviews.length - visibleCount} remaining)
            </button>
          </div>
        )}
      </section>

      {/* FOOTER NOTE */}
      <footer className="pt-6 border-t border-[var(--rc-border)] text-center">
        <p className="text-xs text-[var(--rc-text-muted)] max-w-xl mx-auto leading-relaxed">
          This tool highlights patterns that are common in fake reviews. It does not
          guarantee a review is fake or genuine — always use your own judgment.
        </p>
      </footer>
    </div>
  );
}
