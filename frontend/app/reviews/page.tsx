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

  // VeriScholar navbar theme tracking
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
    <div className="min-h-screen flex flex-col justify-between font-sans bg-[var(--rc-bg)] text-[var(--rc-text)] transition-colors">
      {/* ═════════════════════════════════════════════════════════════════════
          VERISCHOLAR NAVBAR (Editorial style preserved per Section 1 & 5)
         ═════════════════════════════════════════════════════════════════════ */}
      <header className="sticky top-0 z-50 w-full bg-[var(--bg)]/90 backdrop-blur-sm border-b border-[var(--border-soft)]">
        <div className="container-wide h-[76px] flex items-center justify-between">
          {/* Wordmark */}
          <Link href="/" className="flex items-baseline cursor-pointer">
            <span className="font-sans font-semibold text-lg tracking-tight text-[var(--text)]">
              Veri
            </span>
            <span className="font-serif italic font-medium text-xl text-[var(--text)]">
              Scholar
            </span>
          </Link>

          {/* Navigation Links & Theme Toggle */}
          <div className="flex items-center gap-8">
            <nav className="flex items-center gap-6 text-sm font-sans">
              <Link
                href="/"
                className="text-[var(--text-muted)] hover:text-[var(--text)] pb-0.5 transition-colors cursor-pointer"
              >
                Analyzer
              </Link>
              <Link
                href="/methodology"
                className="text-[var(--text-muted)] hover:text-[var(--text)] pb-0.5 transition-colors cursor-pointer"
              >
                Methodology
              </Link>
              <Link
                href="/reviews"
                className="text-[var(--text)] border-b border-[var(--accent)] pb-0.5 font-medium cursor-pointer"
              >
                Review Checker
              </Link>
            </nav>

            {/* Theme Toggle Button */}
            <button
              type="button"
              onClick={toggleTheme}
              className="text-[var(--text-muted)] hover:text-[var(--text)] transition-colors p-1 cursor-pointer"
              aria-label="Toggle theme"
            >
              {theme === "dark" ? (
                // Moon Icon
                <svg
                  className="w-[17px] h-[17px]"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  strokeWidth="1.8"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                >
                  <path d="M12 3a6 6 0 0 0 9 9 9 9 0 1 1-9-9Z" />
                </svg>
              ) : (
                // Sun Icon
                <svg
                  className="w-[17px] h-[17px]"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  strokeWidth="1.8"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                >
                  <circle cx="12" cy="12" r="4" />
                  <path d="M12 2v2" />
                  <path d="M12 20v2" />
                  <path d="m4.93 4.93 1.41 1.41" />
                  <path d="m17.66 17.66 1.41 1.41" />
                  <path d="M2 12h2" />
                  <path d="M20 12h2" />
                  <path d="m6.34 17.66-1.41 1.41" />
                  <path d="m19.07 4.93-1.41 1.41" />
                </svg>
              )}
            </button>
          </div>
        </div>
      </header>

      {/* ═════════════════════════════════════════════════════════════════════
          MAIN CONTENT AREA (Distinct Consumer/Modern Design)
         ═════════════════════════════════════════════════════════════════════ */}
      <main className="flex-1 w-full max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 py-8 sm:py-12">
        {/* STATE: INPUT */}
        {pageState === "input" && (
          <div className="w-full max-w-2xl mx-auto space-y-8 animate-tab-panel">
            {/* Friendly Centered Hero */}
            <div className="text-center space-y-3">
              <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-indigo-50 border border-indigo-100 text-xs font-semibold text-[var(--rc-primary)]">
                <span className="w-2 h-2 rounded-full bg-[var(--rc-primary)]" />
                Consumer Trust &amp; Safety Tool
              </div>
              <h1 className="text-2xl sm:text-4xl font-extrabold text-[var(--rc-text)] tracking-tight">
                Is this product&apos;s reviews trustworthy?
              </h1>
              <p className="text-sm sm:text-base text-[var(--rc-text-muted)] max-w-lg mx-auto leading-relaxed">
                Paste a product link from Amazon or Flipkart and we&apos;ll check if
                the reviews look genuine.
              </p>
            </div>

            {/* Pill Tab Switcher */}
            <div className="flex items-center justify-center">
              <div
                role="tablist"
                aria-label="Review Input Modes"
                className="inline-flex p-1 bg-gray-200/80 rounded-full border border-[var(--rc-border)]"
              >
                <button
                  type="button"
                  role="tab"
                  id="tab-url"
                  aria-selected={activeTab === "url"}
                  aria-controls="panel-url"
                  onClick={() => setActiveTab("url")}
                  className={`px-5 py-2 rounded-full text-xs sm:text-sm font-semibold transition-all cursor-pointer ${
                    activeTab === "url"
                      ? "bg-white text-[var(--rc-primary)] shadow-sm"
                      : "text-[var(--rc-text-muted)] hover:text-[var(--rc-text)]"
                  }`}
                >
                  Paste a product link
                </button>
                <button
                  type="button"
                  role="tab"
                  id="tab-manual"
                  aria-selected={activeTab === "manual"}
                  aria-controls="panel-manual"
                  onClick={() => setActiveTab("manual")}
                  className={`px-5 py-2 rounded-full text-xs sm:text-sm font-semibold transition-all cursor-pointer ${
                    activeTab === "manual"
                      ? "bg-white text-[var(--rc-primary)] shadow-sm"
                      : "text-[var(--rc-text-muted)] hover:text-[var(--rc-text)]"
                  }`}
                >
                  Paste reviews manually
                </button>
              </div>
            </div>

            {/* Tab 1: URL Form */}
            {activeTab === "url" && (
              <div
                id="panel-url"
                role="tabpanel"
                aria-labelledby="tab-url"
                className="bg-[var(--rc-card)] p-6 sm:p-8 rounded-2xl border border-[var(--rc-border)] shadow-sm space-y-4"
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
                className="bg-transparent space-y-4"
              >
                <ReviewManualForm onSubmit={handleManualSubmit} />
              </div>
            )}
          </div>
        )}

        {/* STATE: ANALYZING */}
        {pageState === "analyzing" && (
          <div className="py-12 sm:py-16 animate-tab-panel">
            <ReviewAnalyzing />
          </div>
        )}

        {/* STATE: ERROR */}
        {pageState === "error" && (
          <div className="py-12 animate-tab-panel">
            <ReviewErrorState
              status={errorStatus}
              errorMessage={errorMessage}
              onTryAgain={handleResetToInput}
              onSwitchToManual={handleSwitchToManualFallback}
            />
          </div>
        )}

        {/* STATE: REPORT */}
        {pageState === "report" && reportData && (
          <div className="animate-tab-panel">
            <ReviewReportDashboard
              data={reportData}
              onReset={handleResetToInput}
            />
          </div>
        )}
      </main>
    </div>
  );
}
