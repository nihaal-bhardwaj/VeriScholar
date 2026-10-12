"use client";

import React, { useState, useRef, useEffect } from "react";
import Link from "next/link";
import { RiskReport } from "../lib/mockData";
import AnalysisProgress from "../components/progress/AnalysisProgress";
import ReportDashboard from "../components/report/ReportDashboard";
import AnalysisError from "../components/AnalysisError";

export default function HomePage() {
  const [viewState, setViewState] = useState<"landing" | "progress" | "report" | "error">("landing");
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [isMockMode, setIsMockMode] = useState<boolean>(false);
  const [reportData, setReportData] = useState<RiskReport | null>(null);
  const [errorMessage, setErrorMessage] = useState<string>("");
  const [inlineValidationError, setInlineValidationError] = useState<string | null>(null);
  const [isDragOver, setIsDragOver] = useState<boolean>(false);
  const [theme, setTheme] = useState<"dark" | "light">(() => {
    if (typeof document !== "undefined") {
      const currentTheme = document.documentElement.getAttribute("data-theme");
      if (currentTheme === "light" || currentTheme === "dark") return currentTheme;
    }
    return "dark";
  });

  const fileInputRef = useRef<HTMLInputElement>(null);

  // Synchronize theme attribute on mount and toggle
  useEffect(() => {
    if (!document.documentElement.getAttribute("data-theme")) {
      document.documentElement.setAttribute("data-theme", "dark");
    }
  }, []);

  const toggleTheme = () => {
    const next = theme === "dark" ? "light" : "dark";
    setTheme(next);
    document.documentElement.setAttribute("data-theme", next);
  };

  const validateAndProcessFile = (file: File) => {
    setInlineValidationError(null);

    // Client-side validations (Section 10)
    if (!file.name.toLowerCase().endsWith(".pdf") && file.type !== "application/pdf") {
      setInlineValidationError("Please upload a PDF file.");
      return;
    }

    if (file.size > 40 * 1024 * 1024) {
      setInlineValidationError("This file is too large. VeriScholar accepts PDFs up to 15MB.");
      return;
    }

    setSelectedFile(file);
    setIsMockMode(false);
    setViewState("progress");
  };

  const handleFileInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      validateAndProcessFile(e.target.files[0]);
    }
  };

  const handleSampleClick = () => {
    setInlineValidationError(null);
    setSelectedFile(null);
    setIsMockMode(true);
    setViewState("progress");
  };

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragOver(true);
  };

  const handleDragLeave = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragOver(false);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragOver(false);

    if (e.dataTransfer && e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      validateAndProcessFile(e.dataTransfer.files[0]);
    }
  };

  const handleAnalysisComplete = (data: RiskReport) => {
    setReportData(data);
    setViewState("report");
  };

  const handleAnalysisError = (msg: string) => {
    setErrorMessage(msg);
    setViewState("error");
  };

  const handleReset = () => {
    setViewState("landing");
    setSelectedFile(null);
    setIsMockMode(false);
    setReportData(null);
    setErrorMessage("");
    setInlineValidationError(null);
    if (fileInputRef.current) fileInputRef.current.value = "";
  };

  return (
    <div className="min-h-screen flex flex-col justify-between relative z-10">
      {/* NAVBAR (Section 5) */}
      <header className="sticky top-0 z-50 w-full bg-[var(--bg)]/80 backdrop-blur-sm border-b border-[var(--border-soft)]">
        <div className="container-wide h-[76px] flex items-center justify-between">
          {/* Wordmark (no icon, no gradient) */}
          <Link href="/" onClick={handleReset} className="flex items-baseline cursor-pointer">
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
                onClick={handleReset}
                className="text-[var(--text)] border-b border-[var(--accent)] pb-0.5 cursor-pointer"
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
                className="text-[var(--text-muted)] hover:text-[var(--text)] pb-0.5 transition-colors cursor-pointer"
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
                  <path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z" />
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
                  <circle cx="12" cy="12" r="5" />
                  <line x1="12" y1="1" x2="12" y2="3" />
                  <line x1="12" y1="21" x2="12" y2="23" />
                  <line x1="4.22" y1="4.22" x2="5.64" y2="5.64" />
                  <line x1="18.36" y1="18.36" x2="19.78" y2="19.78" />
                  <line x1="1" y1="12" x2="3" y2="12" />
                  <line x1="21" y1="12" x2="23" y2="12" />
                  <line x1="4.22" y1="19.78" x2="5.64" y2="18.36" />
                  <line x1="18.36" y1="5.64" x2="19.78" y2="4.22" />
                </svg>
              )}
            </button>
          </div>
        </div>
      </header>

      {/* MAIN VIEWPORT */}
      <main className="flex-1">
        {/* LANDING VIEW */}
        {viewState === "landing" && (
          <div className="container-text py-16 sm:py-24 space-y-20">
            {/* HERO SECTION */}
            <section className="space-y-6">
              <h1 className="font-serif font-medium text-[clamp(34px,5vw,52px)] text-[var(--text)] max-w-[16ch] leading-[1.16] tracking-tight">
                A quiet second reader for every paper you submit
              </h1>

              <p className="font-sans text-[17px] text-[var(--text-muted)] max-w-[54ch] leading-relaxed">
                VeriScholar checks a paper&apos;s metadata, citations, and internal consistency against the public record, then tells you plainly what it found — and what it didn&apos;t.
              </p>

              {/* Upload Action Row */}
              <div className="pt-2 space-y-2">
                <div className="flex items-center gap-4">
                  <input
                    ref={fileInputRef}
                    type="file"
                    accept=".pdf,application/pdf"
                    className="hidden"
                    onChange={handleFileInputChange}
                  />
                  <button
                    type="button"
                    onClick={() => fileInputRef.current?.click()}
                    className="btn cursor-pointer"
                  >
                    Upload a paper
                  </button>
                  <span className="font-sans text-xs text-[var(--text-muted)]">
                    PDF, up to 15MB
                  </span>
                </div>

                {/* Inline Validation Error */}
                {inlineValidationError && (
                  <div className="text-xs text-[var(--danger)] font-sans pt-1">
                    {inlineValidationError}
                  </div>
                )}
              </div>

              {/* Drop Strip (NOT a dashed box) */}
              <div
                onDragEnter={handleDragOver}
                onDragOver={handleDragOver}
                onDragLeave={handleDragLeave}
                onDrop={handleDrop}
                onClick={() => fileInputRef.current?.click()}
                className={`w-full py-6 border-t border-[var(--border-soft)] text-xs text-[var(--text-muted)] font-sans cursor-pointer transition-colors ${isDragOver ? "bg-[var(--bg-raise)] text-[var(--text)]" : ""
                  }`}
              >
                Or drop a PDF anywhere on this page.
              </div>
            </section>

            {/* RECENTLY REVIEWED SECTION */}
            <section className="space-y-6">
              <div>
                <h2 className="font-serif text-2xl font-medium text-[var(--text)]">
                  Recently reviewed
                </h2>
                <p className="font-sans text-sm text-[var(--text-muted)] mt-1">
                  Sample reports — select one to view the full screening report.
                </p>
              </div>

              <div className="divide-y divide-[var(--border-soft)] border-t border-b border-[var(--border-soft)]">
                {/* Sample 1 */}
                <button
                  type="button"
                  onClick={handleSampleClick}
                  className="w-full text-left py-4 flex justify-between items-center group relative hover:pl-3 transition-all cursor-pointer"
                >
                  <div className="space-y-1">
                    <div className="font-serif text-[19px] font-medium text-[var(--text)] group-hover:text-[var(--accent)] transition-colors">
                      Latent Drift: Measuring Representation Instability in Fine-Tuned Language Models
                    </div>
                    <div className="font-sans text-sm text-[var(--text-muted)]">
                      EMNLP 2025 — Kowalski, Menon, Subramaniam, Álvarez
                    </div>
                  </div>
                  <div className="text-right shrink-0 ml-4">
                    <div className="font-serif italic text-sm text-[var(--warn)]">
                      Moderate
                    </div>
                    <div className="font-sans text-xs text-[var(--text-faint)] mt-0.5">
                      2 minutes ago
                    </div>
                  </div>
                </button>

                {/* Sample 2 */}
                <button
                  type="button"
                  onClick={handleSampleClick}
                  className="w-full text-left py-4 flex justify-between items-center group relative hover:pl-3 transition-all cursor-pointer"
                >
                  <div className="space-y-1">
                    <div className="font-serif text-[19px] font-medium text-[var(--text)] group-hover:text-[var(--accent)] transition-colors">
                      Photocatalytic Efficiency of Doped TiO₂ Nanostructures Under Visible Light
                    </div>
                    <div className="font-sans text-sm text-[var(--text-muted)]">
                      Journal of Materials Chemistry — 3 authors
                    </div>
                  </div>
                  <div className="text-right shrink-0 ml-4">
                    <div className="font-serif italic text-sm text-[var(--good)]">
                      Low
                    </div>
                    <div className="font-sans text-xs text-[var(--text-faint)] mt-0.5">
                      1 hour ago
                    </div>
                  </div>
                </button>

                {/* Sample 3 */}
                <button
                  type="button"
                  onClick={handleSampleClick}
                  className="w-full text-left py-4 flex justify-between items-center group relative hover:pl-3 transition-all cursor-pointer"
                >
                  <div className="space-y-1">
                    <div className="font-serif text-[19px] font-medium text-[var(--text)] group-hover:text-[var(--accent)] transition-colors">
                      Early Markers of Cognitive Decline in Longitudinal Cohort Studies
                    </div>
                    <div className="font-sans text-sm text-[var(--text-muted)]">
                      Preprint — 6 authors
                    </div>
                  </div>
                  <div className="text-right shrink-0 ml-4">
                    <div className="font-serif italic text-sm text-[var(--danger)]">
                      Needs review
                    </div>
                    <div className="font-sans text-xs text-[var(--text-faint)] mt-0.5">
                      Yesterday
                    </div>
                  </div>
                </button>
              </div>
            </section>

            {/* HOW A REPORT GETS MADE */}
            <section className="space-y-6">
              <h2 className="font-serif text-2xl font-medium text-[var(--text)]">
                How a report gets made
              </h2>

              <div className="space-y-4 max-w-[60ch] font-sans text-[15.5px] leading-relaxed text-[var(--text-muted)]">
                <p>
                  <span className="font-serif italic text-[var(--text)] mr-1">First,</span>
                  the PDF is parsed for text, structure, and layout, and its metadata is checked against Crossref and OpenAlex for a matching record.
                </p>
                <p>
                  <span className="font-serif italic text-[var(--text)] mr-1">Then,</span>
                  each reference is resolved against public indexes, and the abstract, body, and figures are compared for internal consistency.
                </p>
                <p>
                  <span className="font-serif italic text-[var(--text)] mr-1">Finally,</span>
                  everything is compiled into one report — with risk, confidence, and modules shown as separate, distinct measures.
                </p>
              </div>
            </section>
          </div>
        )}

        {/* PROGRESS VIEW */}
        {viewState === "progress" && (
          <div className="container-text py-16">
            <AnalysisProgress
              file={selectedFile}
              isMock={isMockMode}
              onComplete={handleAnalysisComplete}
              onError={handleAnalysisError}
            />
          </div>
        )}

        {/* REPORT VIEW */}
        {viewState === "report" && reportData && (
          <div className="container-wide py-8">
            <ReportDashboard
              data={reportData}
              isMock={isMockMode}
              onBack={handleReset}
              onReset={handleReset}
            />
          </div>
        )}

        {/* ERROR VIEW */}
        {viewState === "error" && (
          <div className="container-text py-16">
            <AnalysisError message={errorMessage} onRetry={handleReset} />
          </div>
        )}
      </main>

      {/* FOOTER */}
      <footer className="w-full border-t border-[var(--border)] py-6 mt-16">
        <div className="container-wide flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 text-xs text-[var(--text-muted)] font-sans">
          <div>© 2026 VeriScholar. A design prototype.</div>
          <div className="max-w-[38ch] sm:text-right leading-relaxed">
            VeriScholar surfaces screening signals — it does not determine or prove research misconduct.
          </div>
        </div>
      </footer>
    </div>
  );
}