"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import ReviewUrlForm from "../../components/reviews/ReviewUrlForm";
import ReviewManualForm from "../../components/reviews/ReviewManualForm";
import ReviewAnalyzing from "../../components/reviews/ReviewAnalyzing";
import ReviewReportDashboard from "../../components/reviews/ReviewReportDashboard";
import ReviewErrorState from "../../components/reviews/ReviewErrorState";
import { analyzeManualReviews, analyzeProductUrl } from "../../lib/review-api";
import { ManualReview, ProductReviewReport, ReviewApiError } from "../../lib/review-types";

type PageState = "input" | "analyzing" | "report" | "error";
type InputTab = "url" | "manual";

export default function ReviewsPage() {
  const [pageState, setPageState] = useState<PageState>("input");
  const [activeTab, setActiveTab] = useState<InputTab>("url");
  const [reportData, setReportData] = useState<ProductReviewReport | null>(null);
  const [errorStatus, setErrorStatus] = useState<number | undefined>(undefined);
  const [errorMessage, setErrorMessage] = useState<string | undefined>(undefined);

  const [theme, setTheme] = useState<"dark" | "light">("dark");

  useEffect(() => {
    const saved = document.documentElement.getAttribute("data-theme") as
      | "dark"
      | "light"
      | null;
    if (saved && saved !== theme) {
      requestAnimationFrame(() => {
        setTheme(saved);
      });
    }
  }, [theme]);

  const toggleTheme = () => {
    const next = theme === "dark" ? "light" : "dark";
    setTheme(next);
    document.documentElement.setAttribute("data-theme", next);
  };

  const handleUrlSubmit = async (url: string) => {
    setPageState("analyzing");
    setErrorStatus(undefined);
    setErrorMessage(undefined);

    try {
      const report = await analyzeProductUrl(url);
      setReportData(report);
      setPageState("report");
    } catch (err: unknown) {
      const apiErr = err as ReviewApiError;
      setErrorStatus(apiErr.status);
      setErrorMessage(apiErr.message || "Failed to analyze product reviews.");
      setPageState("error");
    }
  };

  const handleManualSubmit = async (reviews: ManualReview[]) => {
    setPageState("analyzing");
    setErrorStatus(undefined);
    setErrorMessage(undefined);

    try {
      const report = await analyzeManualReviews(reviews);
      setReportData(report);
      setPageState("report");
    } catch (err: unknown) {
      const apiErr = err as ReviewApiError;
      setErrorStatus(apiErr.status);
      setErrorMessage(apiErr.message || "Failed to analyze submitted reviews.");
      setPageState("error");
    }
  };

  const handleResetToInput = () => {
    setPageState("input");
    setErrorStatus(undefined);
    setErrorMessage(undefined);
  };

  const handleSwitchToManualFallback = () => {
    setActiveTab("manual");
    setPageState("input");
    setErrorStatus(undefined);
    setErrorMessage(undefined);
  };

  return (
    <div className="min-h-screen flex flex-col justify-between font-sans bg-[var(--bg)] text-[var(--text)] transition-colors relative z-10">
      {/* ═════════════════════════════════════════════════════════════════════
          MODERN SAAS NAVBAR (Linear/Perplexity style)
         ═════════════════════════════════════════════════════════════════════ */}
      <header className="sticky top-0 z-50 w-full bg-[var(--bg)]/80 backdrop-blur-md border-b border-[var(--border)]">
        <div className="max-w-7xl mx-auto h-[68px] px-4 sm:px-6 lg:px-8 flex items-center justify-between">
          {/* Wordmark (no icon, no gradient) */}
          <Link href="/" className="flex items-baseline cursor-pointer">
            <span className="font-sans font-semibold text-lg tracking-tight text-[var(--text)]">
              Veri
            </span>
            <span className="font-serif italic font-medium text-xl text-[var(--text)]">
              Scholar
            </span>
          </Link>

          {/* Segmented Workspace Switcher */}
          <nav className="flex items-center p-1 bg-zinc-900/90 rounded-xl border border-white/[0.08] text-xs font-medium">
            <Link
              href="/"
              className="px-3.5 py-1.5 rounded-lg text-zinc-400 hover:text-zinc-100 transition-all cursor-pointer flex items-center gap-1.5"
            >
              <svg className="w-3.5 h-3.5 text-zinc-400" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
                <polyline points="14 2 14 8 20 8" />
              </svg>
              <span>Manuscript Screener</span>
            </Link>

            <Link
              href="/reviews"
              className="px-3.5 py-1.5 rounded-lg bg-zinc-100 text-zinc-950 shadow-sm transition-all cursor-pointer font-semibold flex items-center gap-1.5"
            >
              <svg className="w-3.5 h-3.5 text-zinc-950" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2" />
              </svg>
              <span>Review Integrity</span>
            </Link>

            <Link
              href="/methodology"
              className="hidden sm:flex px-3.5 py-1.5 rounded-lg text-zinc-400 hover:text-zinc-100 transition-all cursor-pointer"
            >
              Methodology
            </Link>
          </nav>

          {/* Right Theme Toggle */}
          <div className="flex items-center gap-3">
            <button
              type="button"
              onClick={toggleTheme}
              className="w-8 h-8 rounded-lg bg-zinc-900 border border-white/[0.08] text-zinc-400 hover:text-zinc-100 flex items-center justify-center cursor-pointer transition-colors"
              aria-label="Toggle theme"
            >
              {theme === "dark" ? (
                <svg className="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <path d="M12 3a6 6 0 0 0 9 9 9 9 0 1 1-9-9Z" />
                </svg>
              ) : (
                <svg className="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <circle cx="12" cy="12" r="4" />
                  <path d="M12 2v2M12 20v2M4.93 4.93l1.41 1.41M17.66 17.66l1.41 1.41M2 12h2M20 12h2M6.34 17.66l-1.41 1.41M19.07 4.93l-1.41 1.41" />
                </svg>
              )}
            </button>
          </div>
        </div>
      </header>

      {/* ═════════════════════════════════════════════════════════════════════
          MAIN CONTENT AREA (Distinct Modern SaaS Canvas)
         ═════════════════════════════════════════════════════════════════════ */}
      <main className="flex-1 w-full max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 sm:py-12">
        {/* STATE: INPUT */}
        {pageState === "input" && (
          <div className="w-full max-w-3xl mx-auto space-y-8 animate-tab-panel">
            {/* SaaS Centered Hero */}
            <div className="text-center space-y-3 pt-4">
              <h1 className="text-3xl sm:text-5xl font-extrabold text-[var(--text)] tracking-tight">
                Are these product reviews <span className="bg-gradient-to-r from-zinc-100 via-zinc-300 to-zinc-400 bg-clip-text text-transparent">trustworthy?</span>
              </h1>

              <p className="text-sm sm:text-base text-[var(--text-muted)] max-w-xl mx-auto leading-relaxed">
                Scan Amazon and Flipkart product pages for bot-generated praise, unnatural keyword stuffing, and physical incoherence using Gemini 3.1+ LLM intelligence.
              </p>
            </div>

            {/* Pill Tab Switcher */}
            <div className="flex items-center justify-center">
              <div
                role="tablist"
                aria-label="Review Input Modes"
                className="inline-flex p-1 bg-zinc-900/90 rounded-xl border border-white/[0.08] shadow-inner"
              >
                <button
                  type="button"
                  role="tab"
                  id="tab-url"
                  aria-selected={activeTab === "url"}
                  aria-controls="panel-url"
                  onClick={() => setActiveTab("url")}
                  className={`px-5 py-2 rounded-lg text-xs sm:text-sm font-semibold transition-all cursor-pointer flex items-center gap-2 ${
                    activeTab === "url"
                      ? "bg-zinc-100 text-zinc-950 shadow-md font-semibold"
                      : "text-zinc-400 hover:text-zinc-100"
                  }`}
                >
                  <svg className="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <circle cx="11" cy="11" r="8" />
                    <line x1="21" y1="21" x2="16.65" y2="16.65" />
                  </svg>
                  <span>Scan by Product URL</span>
                </button>
                <button
                  type="button"
                  role="tab"
                  id="tab-manual"
                  aria-selected={activeTab === "manual"}
                  aria-controls="panel-manual"
                  onClick={() => setActiveTab("manual")}
                  className={`px-5 py-2 rounded-lg text-xs sm:text-sm font-semibold transition-all cursor-pointer flex items-center gap-2 ${
                    activeTab === "manual"
                      ? "bg-zinc-100 text-zinc-950 shadow-md font-semibold"
                      : "text-zinc-400 hover:text-zinc-100"
                  }`}
                >
                  <svg className="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7" />
                    <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z" />
                  </svg>
                  <span>Paste Reviews Manually</span>
                </button>
              </div>
            </div>

            {/* Tab 1: URL Form */}
            {activeTab === "url" && (
              <div
                id="panel-url"
                role="tabpanel"
                aria-labelledby="tab-url"
                className="saas-card p-6 sm:p-8 space-y-4"
              >
                <ReviewUrlForm onSubmit={handleUrlSubmit} />
              </div>
            )}

            {/* Tab 2: Manual Paste Form */}
            {activeTab === "manual" && (
              <div
                id="panel-manual"
                role="tabpanel"
                aria-labelledby="tab-manual"
                className="saas-card p-6 sm:p-8 space-y-4"
              >
                <ReviewManualForm onSubmit={handleManualSubmit} />
              </div>
            )}
          </div>
        )}

        {/* STATE: ANALYZING */}
        {pageState === "analyzing" && (
          <div className="w-full max-w-xl mx-auto py-12">
            <ReviewAnalyzing mode={activeTab} />
          </div>
        )}

        {/* STATE: REPORT */}
        {pageState === "report" && reportData && (
          <ReviewReportDashboard data={reportData} onReset={handleResetToInput} />
        )}

        {/* STATE: ERROR */}
        {pageState === "error" && (
          <div className="w-full max-w-xl mx-auto py-8">
            <ReviewErrorState
              status={errorStatus}
              message={errorMessage}
              onRetry={handleResetToInput}
              onManualFallback={handleSwitchToManualFallback}
            />
          </div>
        )}
      </main>

      {/* FOOTER */}
      <footer className="w-full border-t border-[var(--border)] py-6 bg-[var(--bg)] text-xs text-[var(--text-faint)]">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 flex flex-col sm:flex-row items-center justify-between gap-3">
          <div className="flex items-center gap-2">
            <span className="font-semibold text-[var(--text)]">VeriScholar</span>
            <span>&bull; Academic Integrity &amp; Consumer Trust Analytics</span>
          </div>
          <div className="font-mono text-[11px]">
            Screening Instrument &bull; Not a Determination of Misconduct
          </div>
        </div>
      </footer>
    </div>
  );
}
