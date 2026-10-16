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
type SortOption = "suspicion_desc" | "suspicion_asc" | "rating_desc" | "rating_asc";

export default function ReviewReportDashboard({
  data,
  onReset,
}: ReviewReportDashboardProps) {
  const [filter, setFilter] = useState<FilterClassification>("all");
  const [searchQuery, setSearchQuery] = useState("");
  const [sortBy, setSortBy] = useState<SortOption>("suspicion_desc");
  const [visibleCount, setVisibleCount] = useState(10);
  const [expandedReviews, setExpandedReviews] = useState<Record<number, boolean>>({});
  const [expandedSignals, setExpandedSignals] = useState<Record<number, boolean>>({});

  // Calculations for circular progress ring
  const isInsufficient = data.trust_level === "insufficient_data";
  const trustPercent = isInsufficient
    ? 0
    : Math.max(0, Math.min(100, Math.round(100 - data.overall_trust_score)));

  // SVG dimensions for score gauge
  const size = 160;
  const strokeWidth = 10;
  const radius = (size - strokeWidth) / 2;
  const circumference = 2 * Math.PI * radius;
  const strokeDashoffset = isInsufficient
    ? circumference
    : circumference - (trustPercent / 100) * circumference;

  // Ring & theme configuration
  const getThemeConfig = () => {
    switch (data.trust_level) {
      case "low_trust_concern":
        return {
          strokeColor: "#10B981",
          gradientFrom: "#34D399",
          gradientTo: "#059669",
          badgeBg: "bg-emerald-500/10 text-emerald-400 border-emerald-500/20",
          dotColor: "bg-emerald-400",
          label: "Highly Trustworthy",
        };
      case "moderate_concern":
        return {
          strokeColor: "#F59E0B",
          gradientFrom: "#FBBF24",
          gradientTo: "#D97706",
          badgeBg: "bg-amber-500/10 text-amber-400 border-amber-500/20",
          dotColor: "bg-amber-400",
          label: "Some Concerns Detected",
        };
      case "high_concern":
        return {
          strokeColor: "#EF4444",
          gradientFrom: "#F87171",
          gradientTo: "#DC2626",
          badgeBg: "bg-rose-500/10 text-rose-400 border-rose-500/20",
          dotColor: "bg-rose-400",
          label: "Elevated Manipulation Signal",
        };
      case "critical_concern":
        return {
          strokeColor: "#DC2626",
          gradientFrom: "#FB7185",
          gradientTo: "#991B1B",
          badgeBg: "bg-red-500/15 text-red-300 border-red-500/30",
          dotColor: "bg-red-400",
          label: "Critical Manipulation Alert",
        };
      case "insufficient_data":
      default:
        return {
          strokeColor: "#71717A",
          gradientFrom: "#A1A1AA",
          gradientTo: "#52525B",
          badgeBg: "bg-zinc-500/10 text-zinc-400 border-zinc-500/20",
          dotColor: "bg-zinc-400",
          label: "Insufficient Review Data",
        };
    }
  };

  const themeConfig = getThemeConfig();

  // Breakdown counts & percentages
  const totalReviews = data.reviews.length;
  const genuineCount = useMemo(
    () => data.reviews.filter((r) => r.classification === "likely_genuine").length,
    [data.reviews]
  );
  const uncertainCount = useMemo(
    () => data.reviews.filter((r) => r.classification === "uncertain").length,
    [data.reviews]
  );
  const fakeCount = useMemo(
    () => data.reviews.filter((r) => r.classification === "likely_fake").length,
    [data.reviews]
  );

  const genuinePct = totalReviews > 0 ? Math.round((genuineCount / totalReviews) * 100) : 0;
  const uncertainPct = totalReviews > 0 ? Math.round((uncertainCount / totalReviews) * 100) : 0;
  const fakePct = totalReviews > 0 ? Math.max(0, 100 - genuinePct - uncertainPct) : 0;

  // Filtered & sorted reviews mapped with their original index in data.reviews
  const filteredAndSortedReviews = useMemo(() => {
    let result = data.reviews.map((review, originalIndex) => ({ review, originalIndex }));

    if (filter !== "all") {
      result = result.filter((item) => item.review.classification === filter);
    }

    if (searchQuery.trim()) {
      const q = searchQuery.toLowerCase();
      result = result.filter(
        (item) =>
          item.review.review_text.toLowerCase().includes(q) ||
          (item.review.reviewer_name && item.review.reviewer_name.toLowerCase().includes(q))
      );
    }

    result.sort((a, b) => {
      if (sortBy === "suspicion_desc") return b.review.authenticity_score - a.review.authenticity_score;
      if (sortBy === "suspicion_asc") return a.review.authenticity_score - b.review.authenticity_score;
      if (sortBy === "rating_desc") return (b.review.rating ?? 0) - (a.review.rating ?? 0);
      if (sortBy === "rating_asc") return (a.review.rating ?? 0) - (b.review.rating ?? 0);
      return 0;
    });

    return result;
  }, [data.reviews, filter, searchQuery, sortBy]);

  const displayedReviews = filteredAndSortedReviews.slice(0, visibleCount);

  // Clear expanded state whenever filter, searchQuery, or sortBy changes
  React.useEffect(() => {
    setExpandedReviews({});
    setExpandedSignals({});
  }, [filter, searchQuery, sortBy]);

  const toggleExpandReview = (originalIndex: number) => {
    setExpandedReviews((prev) => ({ ...prev, [originalIndex]: !prev[originalIndex] }));
  };

  const toggleExpandSignals = (originalIndex: number) => {
    setExpandedSignals((prev) => ({ ...prev, [originalIndex]: !prev[originalIndex] }));
  };

  const handleExportJson = () => {
    const blob = new Blob([JSON.stringify(data, null, 2)], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `verischolar-review-report-${Date.now()}.json`;
    a.click();
    setTimeout(() => URL.revokeObjectURL(url), 0);
  };

  return (
    <div className="w-full max-w-7xl mx-auto space-y-8 animate-tab-panel pb-16">
      {/* ═════════════════════════════════════════════════════════════════════
          TOP HEADER CONTROLS (Brand Title & Quick Action Bar)
         ═════════════════════════════════════════════════════════════════════ */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-[var(--border)]">
        <div className="space-y-1">
          <div className="inline-flex items-center gap-2 text-xs font-semibold text-[var(--accent)] tracking-wider uppercase">
            <span className="w-2 h-2 rounded-full bg-[var(--accent)] animate-pulse" />
            Forensic Intelligence Audit
          </div>
          <h2 className="text-2xl sm:text-3xl font-bold tracking-tight text-[var(--text)]">
            Review Authenticity Report
          </h2>
          {data.product_title && (
            <p className="text-sm text-[var(--text-muted)] line-clamp-1 max-w-2xl font-mono">
              {data.product_title}
            </p>
          )}
        </div>

        <div className="flex items-center gap-3 shrink-0">
          <button
            type="button"
            onClick={handleExportJson}
            className="btn-secondary text-xs sm:text-sm px-3.5 py-2 cursor-pointer"
          >
            <svg className="w-4 h-4 text-[var(--text-muted)]" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
              <polyline points="7 10 12 15 17 10" />
              <line x1="12" y1="15" x2="12" y2="3" />
            </svg>
            Export Audit
          </button>

          <button
            type="button"
            onClick={onReset}
            className="btn-primary text-xs sm:text-sm px-4 py-2 cursor-pointer"
          >
            <svg className="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <polyline points="1 4 1 10 7 10" />
              <path d="M3.51 15a9 9 0 1 0 2.13-9.36L1 10" />
            </svg>
            Scan Another Product
          </button>
        </div>
      </div>

      {/* ═════════════════════════════════════════════════════════════════════
          TWO-COLUMN DASHBOARD GRID (Sleek SaaS Layout)
         ═════════════════════════════════════════════════════════════════════ */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-start">
        {/* ─────────────────────────────────────────────────────────────
            LEFT COLUMN (35% width, ~4 cols): Executive Trust Telemetry
           ───────────────────────────────────────────────────────────── */}
        <aside className="lg:col-span-4 space-y-6 lg:sticky lg:top-24">
          {/* Main Trust Index Card */}
          <div className="saas-card p-6 sm:p-7 relative overflow-hidden space-y-6">
            <div className="flex items-center justify-between text-xs font-semibold text-[var(--text-muted)] tracking-wider uppercase border-b border-[var(--border-soft)] pb-3">
              <span>Overall Trust Index</span>
              <span className="font-mono text-[var(--text-faint)]">
                {data.total_reviews_analyzed} items
              </span>
            </div>

            {/* Glowing SVG Radial Gauge */}
            <div className="relative w-[160px] h-[160px] mx-auto flex items-center justify-center my-2">
              <svg className="w-full h-full -rotate-90 transform" viewBox={`0 0 ${size} ${size}`}>
                <defs>
                  <linearGradient id="scoreGradient" x1="0%" y1="0%" x2="100%" y2="100%">
                    <stop offset="0%" stopColor={themeConfig.gradientFrom} />
                    <stop offset="100%" stopColor={themeConfig.gradientTo} />
                  </linearGradient>
                </defs>
                {/* Background track */}
                <circle
                  cx={size / 2}
                  cy={size / 2}
                  r={radius}
                  stroke="rgba(255, 255, 255, 0.08)"
                  strokeWidth={strokeWidth}
                  fill="transparent"
                />
                {/* Progress Stroke */}
                <circle
                  cx={size / 2}
                  cy={size / 2}
                  r={radius}
                  stroke="url(#scoreGradient)"
                  strokeWidth={strokeWidth}
                  strokeDasharray={circumference}
                  strokeDashoffset={strokeDashoffset}
                  strokeLinecap="round"
                  fill="transparent"
                  className="transition-[stroke-dashoffset] duration-1000 ease-out"
                />
              </svg>

              {/* Gauge Inner Score Readout */}
              <div className="absolute inset-0 flex flex-col items-center justify-center text-center">
                {isInsufficient ? (
                  <span className="text-4xl font-extrabold text-[var(--text-muted)]">--</span>
                ) : (
                  <>
                    <span className="text-4xl sm:text-5xl font-extrabold tracking-tight text-[var(--text)] font-sans">
                      {trustPercent}
                    </span>
                    <span className="text-[11px] uppercase font-semibold text-[var(--text-muted)] tracking-wider mt-0.5">
                      out of 100
                    </span>
                  </>
                )}
              </div>
            </div>

            {/* Status Pill & Summary */}
            <div className="text-center space-y-3">
              <div className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full text-xs font-semibold border backdrop-blur-sm mx-auto" style={{
                backgroundColor: themeConfig.badgeBg.includes("emerald") ? "rgba(16, 185, 129, 0.1)" : themeConfig.badgeBg.includes("amber") ? "rgba(245, 158, 11, 0.1)" : "rgba(239, 68, 68, 0.1)",
                borderColor: themeConfig.badgeBg.includes("emerald") ? "rgba(16, 185, 129, 0.25)" : themeConfig.badgeBg.includes("amber") ? "rgba(245, 158, 11, 0.25)" : "rgba(239, 68, 68, 0.25)",
                color: themeConfig.badgeBg.includes("emerald") ? "#34D399" : themeConfig.badgeBg.includes("amber") ? "#FBBF24" : "#F87171"
              }}>
                <span className={`w-2 h-2 rounded-full ${themeConfig.dotColor} animate-pulse`} />
                {themeConfig.label}
              </div>

              <p className="text-xs sm:text-sm text-[var(--text-muted)] leading-relaxed">
                {data.summary}
              </p>
            </div>

            {/* Distribution Stacked Bar */}
            <div className="space-y-2.5 pt-4 border-t border-[var(--border-soft)]">
              <div className="flex items-center justify-between text-xs font-medium">
                <span className="text-[var(--text-muted)]">Sentiment &amp; Authenticity</span>
                <span className="font-mono text-xs text-[var(--text-faint)]">Distribution</span>
              </div>

              <div className="h-2.5 w-full bg-zinc-800/80 rounded-full overflow-hidden flex gap-0.5 p-0.5 border border-white/[0.05]">
                <div
                  style={{ width: `${genuinePct}%` }}
                  className="bg-emerald-500 rounded-full transition-all duration-700"
                  title={`Likely Genuine: ${genuinePct}%`}
                />
                <div
                  style={{ width: `${uncertainPct}%` }}
                  className="bg-amber-500 rounded-full transition-all duration-700"
                  title={`Uncertain: ${uncertainPct}%`}
                />
                <div
                  style={{ width: `${fakePct}%` }}
                  className="bg-rose-500 rounded-full transition-all duration-700"
                  title={`Likely Manipulated: ${fakePct}%`}
                />
              </div>

              {/* Legend */}
              <div className="grid grid-cols-3 gap-1 pt-1 text-[11px] font-medium text-center">
                <div className="bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 py-1 rounded-md">
                  <div className="font-bold">{genuineCount}</div>
                  <div className="text-[10px] text-emerald-400/80">Genuine</div>
                </div>
                <div className="bg-amber-500/10 border border-amber-500/20 text-amber-400 py-1 rounded-md">
                  <div className="font-bold">{uncertainCount}</div>
                  <div className="text-[10px] text-amber-400/80">Uncertain</div>
                </div>
                <div className="bg-rose-500/10 border border-rose-500/20 text-rose-400 py-1 rounded-md">
                  <div className="font-bold">{fakeCount}</div>
                  <div className="text-[10px] text-rose-400/80">Fake</div>
                </div>
              </div>
            </div>
          </div>

          {/* Pattern-Level Batch Findings */}
          {data.batch_signals && data.batch_signals.length > 0 && (
            <div className="saas-card p-5 space-y-3">
              <div className="flex items-center justify-between">
                <h3 className="text-xs font-semibold uppercase tracking-wider text-[var(--text-muted)] flex items-center gap-2">
                  <svg className="w-3.5 h-3.5 text-amber-400" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z" />
                    <line x1="12" y1="9" x2="12" y2="13" />
                    <line x1="12" y1="17" x2="12.01" y2="17" />
                  </svg>
                  <span>Anomalies Flagged</span>
                </h3>
                <span className="text-[10px] font-mono px-2 py-0.5 rounded-full bg-amber-500/15 text-amber-300 font-semibold border border-amber-500/30">
                  {data.batch_signals.length} caught
                </span>
              </div>

              <div className="space-y-2">
                {data.batch_signals.map((sig: ReviewSignal, idx: number) => {
                  const isHigh = sig.severity === "high";
                  return (
                    <div
                      key={`batch-sig-${idx}`}
                      className="p-3 rounded-lg bg-zinc-900/60 border border-white/[0.06] flex items-start gap-2.5 text-xs text-[var(--text)]"
                    >
                      <span className={`w-1.5 h-1.5 rounded-full mt-1.5 shrink-0 ${isHigh ? "bg-rose-400" : "bg-amber-400"}`} />
                      <span className="leading-relaxed">{sig.message}</span>
                    </div>
                  );
                })}
              </div>
            </div>
          )}
        </aside>

        {/* ─────────────────────────────────────────────────────────────
            RIGHT COLUMN (65% width, ~8 cols): Interactive Review Stream
           ───────────────────────────────────────────────────────────── */}
        <section className="lg:col-span-8 space-y-5">
          {/* Controls Bar: Filters, Search & Sort */}
          <div className="saas-card p-4 space-y-3">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
              {/* Filter Pills */}
              <div className="flex flex-wrap items-center gap-1.5">
                {(
                  [
                    { id: "all", label: "All Reviews", count: totalReviews },
                    { id: "likely_genuine", label: "Genuine", count: genuineCount },
                    { id: "uncertain", label: "Uncertain", count: uncertainCount },
                    { id: "likely_fake", label: "Manipulated", count: fakeCount },
                  ] as const
                ).map((tab) => {
                  const active = filter === tab.id;
                  return (
                    <button
                      key={tab.id}
                      type="button"
                      onClick={() => {
                        setFilter(tab.id);
                        setVisibleCount(10);
                      }}
                      className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-all flex items-center gap-1.5 cursor-pointer ${
                        active
                          ? "bg-zinc-100 text-zinc-950 font-semibold shadow-sm"
                          : "bg-zinc-800/60 text-[var(--text-muted)] hover:text-[var(--text)] border border-white/[0.05]"
                      }`}
                    >
                      <span>{tab.label}</span>
                      <span className={`px-1.5 py-0.2 rounded-full text-[10px] font-mono ${
                        active ? "bg-zinc-900/20 text-zinc-950 font-bold" : "bg-zinc-700/60 text-[var(--text-faint)]"
                      }`}>
                        {tab.count}
                      </span>
                    </button>
                  );
                })}
              </div>

              {/* Sort Dropdown */}
              <div className="flex items-center gap-2 shrink-0 text-xs">
                <span className="text-[var(--text-faint)]">Sort:</span>
                <select
                  value={sortBy}
                  onChange={(e) => setSortBy(e.target.value as SortOption)}
                  className="bg-zinc-900 border border-white/[0.08] text-[var(--text)] rounded-lg px-2.5 py-1 text-xs focus:border-zinc-400 cursor-pointer"
                >
                  <option value="suspicion_desc">Highest Suspicion</option>
                  <option value="suspicion_asc">Lowest Suspicion</option>
                  <option value="rating_desc">Highest Stars</option>
                  <option value="rating_asc">Lowest Stars</option>
                </select>
              </div>
            </div>

            {/* Keyword Search Input */}
            <div className="relative">
              <input
                type="text"
                placeholder="Search review text or reviewer name..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full bg-zinc-950/60 border border-white/[0.08] rounded-lg px-3.5 py-2 pl-9 text-xs text-[var(--text)] placeholder-[var(--text-faint)] focus:border-zinc-400 transition-all"
              />
              <svg
                className="w-4 h-4 text-[var(--text-faint)] absolute left-3 top-2.5"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                strokeWidth="2"
              >
                <circle cx="11" cy="11" r="8" />
                <line x1="21" y1="21" x2="16.65" y2="16.65" />
              </svg>
            </div>
          </div>

          {/* Review Stream Cards */}
          {displayedReviews.length === 0 ? (
            <div className="saas-card p-12 text-center space-y-2 text-[var(--text-muted)]">
              <svg className="w-8 h-8 text-[var(--text-faint)] mx-auto" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
                <circle cx="11" cy="11" r="8" />
                <line x1="21" y1="21" x2="16.65" y2="16.65" />
              </svg>
              <div className="text-sm font-medium">No reviews matching the active filters</div>
              <p className="text-xs text-[var(--text-faint)]">Try clearing the search query or changing your filter classification.</p>
            </div>
          ) : (
            <div className="space-y-3.5">
              {displayedReviews.map(({ review, originalIndex }) => {
                const isExpanded = !!expandedReviews[originalIndex];
                const showWhy = !!expandedSignals[originalIndex];
                const suspicionScore = Math.round(review.authenticity_score);
                const isLong = review.review_text.length > 220;
                const textToShow = isLong && !isExpanded
                  ? `${review.review_text.substring(0, 220)}...`
                  : review.review_text;

                const isFake = review.classification === "likely_fake";
                const isGenuine = review.classification === "likely_genuine";

                return (
                  <div
                    key={`review-card-${originalIndex}`}
                    className="saas-card p-5 space-y-3.5 transition-all"
                  >
                    {/* Top Row: Reviewer Monogram, Rating, Badges & Classification */}
                    <div className="flex flex-wrap items-start justify-between gap-3">
                      <div className="flex flex-wrap items-center gap-2.5">
                        {/* Avatar Initial Circle */}
                        <div className="w-7 h-7 rounded-full bg-zinc-800 border border-white/[0.08] text-xs font-bold text-[var(--text-muted)] flex items-center justify-center shrink-0 font-mono">
                          {(review.reviewer_name || "A").charAt(0).toUpperCase()}
                        </div>

                        {/* Name */}
                        <span className="text-xs font-semibold text-[var(--text)]">
                          {review.reviewer_name || "Anonymous Reviewer"}
                        </span>

                        {/* Stars */}
                        {review.rating !== null && (
                          <div className="flex items-center gap-0.5 text-amber-400" title={`${review.rating} out of 5 stars`}>
                            {[1, 2, 3, 4, 5].map((star) => (
                              <svg
                                key={star}
                                className="w-3.5 h-3.5"
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

                        {/* Verified Purchase Badge */}
                        {review.verified_purchase && (
                          <span className="px-2 py-0.5 text-[10px] font-semibold rounded-md bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 inline-flex items-center gap-1">
                            <svg className="w-3 h-3" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
                              <polyline points="20 6 9 17 4 12" />
                            </svg>
                            Verified
                          </span>
                        )}

                        {/* AI / Heuristics Tag */}
                        {review.analyzed_by?.includes("llm") ? (
                          <span className="px-2 py-0.5 text-[10px] font-medium rounded-full bg-violet-500/10 text-violet-300 border border-violet-500/20 inline-flex items-center gap-1 font-mono">
                            <span className="w-1.5 h-1.5 rounded-full bg-violet-400" />
                            AI Analysis
                          </span>
                        ) : (
                          <span className="px-2 py-0.5 text-[10px] font-medium rounded-full bg-zinc-800 text-zinc-400 border border-white/[0.05] font-mono">
                            Rule-based
                          </span>
                        )}
                      </div>

                      {/* Right Status Pill */}
                      <div className="shrink-0">
                        {isFake ? (
                          <span className="px-2.5 py-1 text-xs font-semibold rounded-full bg-rose-500/15 text-rose-300 border border-rose-500/30 font-mono inline-flex items-center gap-1.5">
                            <span className="w-1.5 h-1.5 rounded-full bg-rose-400" />
                            Likely Fake ({suspicionScore}/100)
                          </span>
                        ) : isGenuine ? (
                          <span className="px-2.5 py-1 text-xs font-semibold rounded-full bg-emerald-500/15 text-emerald-300 border border-emerald-500/30 font-mono inline-flex items-center gap-1.5">
                            <span className="w-1.5 h-1.5 rounded-full bg-emerald-400" />
                            Likely Genuine ({suspicionScore}/100)
                          </span>
                        ) : (
                          <span className="px-2.5 py-1 text-xs font-semibold rounded-full bg-amber-500/15 text-amber-300 border border-amber-500/30 font-mono inline-flex items-center gap-1.5">
                            <span className="w-1.5 h-1.5 rounded-full bg-amber-400" />
                            Uncertain ({suspicionScore}/100)
                          </span>
                        )}
                      </div>
                    </div>

                    {/* Review Body */}
                    <div className="text-xs sm:text-sm text-[var(--text)] leading-relaxed font-normal">
                      &ldquo;{textToShow}&rdquo;
                      {isLong && (
                        <button
                          type="button"
                          onClick={() => toggleExpandReview(originalIndex)}
                          className="ml-2 text-xs text-zinc-300 hover:text-white underline cursor-pointer font-medium"
                        >
                          {isExpanded ? "Show less" : "Read more"}
                        </button>
                      )}
                    </div>

                    {/* Expandable "Why? Forensic Assessment" Drawer Toggle */}
                    <div className="pt-1 flex items-center justify-between border-t border-[var(--border-soft)]">
                      <button
                        type="button"
                        onClick={() => toggleExpandSignals(originalIndex)}
                        className="text-xs font-semibold text-[var(--text-muted)] hover:text-[var(--text)] inline-flex items-center gap-1.5 cursor-pointer transition-colors"
                      >
                        <svg
                          className={`w-3.5 h-3.5 text-zinc-400 transition-transform ${showWhy ? "rotate-90" : ""}`}
                          viewBox="0 0 24 24"
                          fill="none"
                          stroke="currentColor"
                          strokeWidth="2.5"
                        >
                          <polyline points="9 18 15 12 9 6" />
                        </svg>
                        <span>{showWhy ? "Hide forensic evidence" : "Why? Inspect forensic evidence"}</span>
                      </button>

                      <span className="text-[11px] font-mono text-[var(--text-faint)]">
                        {review.signals.length} {review.signals.length === 1 ? "signal" : "signals"}
                      </span>
                    </div>

                    {/* Drawer Content */}
                    {showWhy && (
                      <div className="p-4 rounded-xl bg-zinc-950/70 border border-white/[0.08] space-y-3 animate-tab-panel">
                        {/* AI Reasoning (if available) */}
                        {review.reasoning && (
                          <div className="p-3 rounded-lg bg-violet-950/30 border border-violet-500/20 text-xs text-violet-200 space-y-1">
                            <div className="font-semibold text-[10px] uppercase tracking-wider text-violet-400 flex items-center gap-1.5">
                              <svg className="w-3 h-3 text-violet-400" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                                <path d="m12 3-1.912 5.813a2 2 0 0 1-1.275 1.275L3 12l5.813 1.912a2 2 0 0 1 1.275 1.275L12 21l1.912-5.813a2 2 0 0 1 1.275-1.275L21 12l-5.813-1.912a2 2 0 0 1-1.275-1.275L12 3Z" />
                              </svg>
                              AI Common-Sense Assessment
                            </div>
                            <p className="leading-relaxed text-zinc-300">{review.reasoning}</p>
                          </div>
                        )}

                        {/* Heuristic / Pattern Signals */}
                        {review.signals.length === 0 ? (
                          <div className="text-xs text-[var(--text-faint)] italic">
                            No suspicious rule-based heuristics triggered for this review.
                          </div>
                        ) : (
                          <div className="space-y-2">
                            <div className="text-[10px] font-semibold uppercase tracking-wider text-[var(--text-faint)]">
                              Triggered Signals
                            </div>
                            {review.signals.map((sig, sIdx) => {
                              const isHigh = sig.severity === "high";
                              return (
                                <div
                                  key={`sig-${sIdx}`}
                                  className="p-2.5 rounded-lg bg-zinc-900/60 border border-white/[0.04] flex items-start gap-2.5 text-xs text-[var(--text)]"
                                >
                                  <span className={`w-1.5 h-1.5 rounded-full mt-1.5 shrink-0 ${isHigh ? "bg-rose-400" : "bg-amber-400"}`} />
                                  <div className="space-y-0.5">
                                    <div className="font-medium">{sig.message}</div>
                                    <div className="text-[10px] font-mono text-[var(--text-faint)]">
                                      Rule: {sig.rule} ({sig.severity})
                                    </div>
                                  </div>
                                </div>
                              );
                            })}
                          </div>
                        )}
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          )}

          {/* Load More Pagination */}
          {visibleCount < filteredAndSortedReviews.length && (
            <div className="pt-4 text-center">
              <button
                type="button"
                onClick={() => setVisibleCount((prev) => prev + 10)}
                className="btn-secondary text-xs sm:text-sm px-6 py-2 cursor-pointer font-medium"
              >
                Load {Math.min(10, filteredAndSortedReviews.length - visibleCount)} More Reviews
              </button>
            </div>
          )}
        </section>
      </div>
    </div>
  );
}
