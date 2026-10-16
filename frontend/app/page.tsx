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
  const [theme, setTheme] = useState<"dark" | "light">("dark");

  const fileInputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    const currentTheme = document.documentElement.getAttribute("data-theme") as "dark" | "light" | null;
    if (currentTheme) {
      setTheme(currentTheme);
    } else {
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

    if (!file.name.toLowerCase().endsWith(".pdf") && file.type !== "application/pdf") {
      setInlineValidationError("Please upload a PDF file.");
      return;
    }

    if (file.size > 20 * 1024 * 1024) {
      setInlineValidationError("This file is too large. VeriScholar accepts PDFs up to 20MB.");
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

  const handleSampleClick = (sampleIndex: number) => {
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
    <div className="min-h-screen flex flex-col justify-between font-sans bg-[var(--bg)] text-[var(--text)] transition-colors relative z-10">
      {/* ═════════════════════════════════════════════════════════════════════
          MODERN SAAS NAVBAR (Consistent Across Both Workspaces)
         ═════════════════════════════════════════════════════════════════════ */}
      <header className="sticky top-0 z-50 w-full bg-[var(--bg)]/80 backdrop-blur-md border-b border-[var(--border)]">
        <div className="max-w-7xl mx-auto h-[68px] px-4 sm:px-6 lg:px-8 flex items-center justify-between">
          {/* Wordmark (no icon, no gradient) */}
          <Link href="/" onClick={handleReset} className="flex items-baseline cursor-pointer">
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
              onClick={handleReset}
              className="px-3.5 py-1.5 rounded-lg bg-zinc-100 text-zinc-950 shadow-sm transition-all cursor-pointer font-semibold flex items-center gap-1.5"
            >
              <svg className="w-3.5 h-3.5 text-zinc-950" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
                <polyline points="14 2 14 8 20 8" />
              </svg>
              <span>Manuscript Screener</span>
            </Link>

            <Link
              href="/reviews"
              className="px-3.5 py-1.5 rounded-lg text-zinc-400 hover:text-zinc-100 transition-all cursor-pointer flex items-center gap-1.5"
            >
              <svg className="w-3.5 h-3.5 text-zinc-400" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
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
          MAIN VIEWPORT
         ═════════════════════════════════════════════════════════════════════ */}
      <main className="flex-1 w-full max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 sm:py-12">
        {/* LANDING VIEW */}
        {viewState === "landing" && (
          <div className="space-y-16 animate-tab-panel">
            {/* HERO SECTION */}
            <div className="text-center space-y-4 max-w-3xl mx-auto pt-4">
              <h1 className="text-3xl sm:text-5xl lg:text-6xl font-extrabold text-[var(--text)] tracking-tight leading-[1.12]">
                Screen scientific manuscripts with{" "}
                <span className="bg-gradient-to-r from-zinc-100 via-zinc-300 to-zinc-400 bg-clip-text text-transparent">
                  forensic precision
                </span>
              </h1>

              <p className="text-sm sm:text-base text-[var(--text-muted)] max-w-xl mx-auto leading-relaxed">
                VeriScholar audits citations against OpenAlex &amp; Crossref graphs, detects phantom references, and scans internal document consistency before peer review.
              </p>
            </div>

            {/* MODERN DRAG & DROP UPLOAD ZONE */}
            <div className="max-w-2xl mx-auto">
              <input
                ref={fileInputRef}
                type="file"
                accept=".pdf,application/pdf"
                className="hidden"
                onChange={handleFileInputChange}
              />

              <div
                onDragEnter={handleDragOver}
                onDragOver={handleDragOver}
                onDragLeave={handleDragLeave}
                onDrop={handleDrop}
                onClick={() => fileInputRef.current?.click()}
                className={`saas-card p-8 sm:p-12 text-center cursor-pointer transition-all border-dashed relative overflow-hidden group ${
                  isDragOver
                    ? "border-zinc-400 bg-zinc-900/90 shadow-2xl scale-[1.01]"
                    : "border-white/[0.12] hover:border-zinc-500 hover:bg-zinc-900/50"
                }`}
              >
                {/* Subtle Ambient Glow */}
                <div className="absolute top-0 left-1/2 -translate-x-1/2 w-64 h-24 bg-white/[0.03] blur-3xl pointer-events-none group-hover:bg-white/[0.06] transition-all" />

                <div className="space-y-4 relative z-10">
                  <div className="w-16 h-16 mx-auto rounded-2xl bg-zinc-800/90 border border-white/[0.1] flex items-center justify-center text-zinc-200 group-hover:scale-105 group-hover:border-zinc-500 transition-all shadow-lg">
                    <svg className="w-8 h-8" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8">
                      <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
                      <polyline points="14 2 14 8 20 8" />
                      <line x1="12" y1="18" x2="12" y2="12" />
                      <line x1="9" y1="15" x2="12" y2="12" />
                      <line x1="15" y1="15" x2="12" y2="12" />
                    </svg>
                  </div>

                  <div className="space-y-1">
                    <div className="text-base sm:text-lg font-semibold text-[var(--text)]">
                      Drop your research paper PDF here, or <span className="text-zinc-200 underline underline-offset-4 font-medium">browse files</span>
                    </div>
                    <div className="text-xs text-[var(--text-faint)] font-mono">
                      Accepts scientific PDF manuscripts up to 20MB
                    </div>
                  </div>

                  <div className="pt-2">
                    <button
                      type="button"
                      onClick={(e) => {
                        e.stopPropagation();
                        fileInputRef.current?.click();
                      }}
                      className="btn-primary py-2 px-6 text-xs sm:text-sm font-semibold rounded-lg"
                    >
                      Select PDF File
                    </button>
                  </div>
                </div>
              </div>

              {inlineValidationError && (
                <div className="text-xs text-rose-400 font-medium text-center pt-2">
                  {inlineValidationError}
                </div>
              )}
            </div>

            {/* SAMPLE DEMO PAPERS (Interactive Cards) */}
            <div className="max-w-4xl mx-auto space-y-4">
              <div className="flex items-center justify-between pb-2 border-b border-[var(--border)]">
                <div>
                  <h3 className="text-sm font-bold uppercase tracking-wider text-[var(--text-muted)] font-mono">
                    Sample Pre-Screened Manuscripts
                  </h3>
                  <p className="text-xs text-[var(--text-faint)]">
                    Explore calibrated screening reports on pre-configured test cases.
                  </p>
                </div>
                <span className="text-xs font-mono text-zinc-400">1-Click Demos</span>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                {/* Sample 1 */}
                <button
                  type="button"
                  onClick={() => handleSampleClick(0)}
                  className="saas-card p-5 text-left space-y-3 cursor-pointer group hover:border-amber-500/40 transition-all flex flex-col justify-between"
                >
                  <div className="space-y-1.5">
                    <div className="flex items-center justify-between">
                      <span className="text-[10px] font-mono px-2 py-0.5 rounded-full bg-amber-500/10 text-amber-400 border border-amber-500/20 font-semibold">
                        MODERATE SCRUTINY
                      </span>
                      <span className="text-[10px] font-mono text-[var(--text-faint)]">EMNLP 2025</span>
                    </div>
                    <h4 className="text-sm font-semibold text-[var(--text)] group-hover:text-zinc-100 transition-colors line-clamp-2 leading-snug">
                      Latent Drift: Measuring Representation Instability in Fine-Tuned Language Models
                    </h4>
                  </div>
                  <div className="text-xs text-[var(--text-faint)] font-mono">
                    Kowalski, Menon, Subramaniam
                  </div>
                </button>

                {/* Sample 2 */}
                <button
                  type="button"
                  onClick={() => handleSampleClick(1)}
                  className="saas-card p-5 text-left space-y-3 cursor-pointer group hover:border-emerald-500/40 transition-all flex flex-col justify-between"
                >
                  <div className="space-y-1.5">
                    <div className="flex items-center justify-between">
                      <span className="text-[10px] font-mono px-2 py-0.5 rounded-full bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 font-semibold">
                        CLEAN VALIDATION
                      </span>
                      <span className="text-[10px] font-mono text-[var(--text-faint)]">J. Mat. Chem</span>
                    </div>
                    <h4 className="text-sm font-semibold text-[var(--text)] group-hover:text-zinc-100 transition-colors line-clamp-2 leading-snug">
                      Photocatalytic Efficiency of Doped TiO₂ Nanostructures Under Visible Light
                    </h4>
                  </div>
                  <div className="text-xs text-[var(--text-faint)] font-mono">
                    Journal of Materials &bull; 3 authors
                  </div>
                </button>

                {/* Sample 3 */}
                <button
                  type="button"
                  onClick={() => handleSampleClick(2)}
                  className="saas-card p-5 text-left space-y-3 cursor-pointer group hover:border-rose-500/40 transition-all flex flex-col justify-between"
                >
                  <div className="space-y-1.5">
                    <div className="flex items-center justify-between">
                      <span className="text-[10px] font-mono px-2 py-0.5 rounded-full bg-rose-500/10 text-rose-400 border border-rose-500/20 font-semibold">
                        HIGH ATTENTION
                      </span>
                      <span className="text-[10px] font-mono text-[var(--text-faint)]">Preprint 2025</span>
                    </div>
                    <h4 className="text-sm font-semibold text-[var(--text)] group-hover:text-zinc-100 transition-colors line-clamp-2 leading-snug">
                      Early Markers of Cognitive Decline in Longitudinal Cohort Studies
                    </h4>
                  </div>
                  <div className="text-xs text-[var(--text-faint)] font-mono">
                    Preprint Server &bull; 6 authors
                  </div>
                </button>
              </div>
            </div>

            {/* THREE CORE FORENSIC PILLARS */}
            <div className="max-w-5xl mx-auto pt-8">
              <div className="text-center space-y-1 pb-6">
                <div className="text-xs font-mono uppercase tracking-wider text-zinc-400">Multi-Vector Architecture</div>
                <h3 className="text-xl font-bold text-[var(--text)]">Three Pillars of Manuscript Screening</h3>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                <div className="saas-card p-6 space-y-3">
                  <div className="w-10 h-10 rounded-xl bg-zinc-800 border border-zinc-700/80 flex items-center justify-center text-zinc-200 font-mono font-bold">
                    01
                  </div>
                  <h4 className="text-base font-semibold text-[var(--text)]">Citation Graph Integrity</h4>
                  <p className="text-xs text-[var(--text-muted)] leading-relaxed">
                    Live verification against OpenAlex and Crossref bibliographies. Identifies phantom citations, fabricated DOIs, and distorted publication dates.
                  </p>
                </div>

                <div className="saas-card p-6 space-y-3">
                  <div className="w-10 h-10 rounded-xl bg-zinc-800 border border-zinc-700/80 flex items-center justify-center text-zinc-200 font-mono font-bold">
                    02
                  </div>
                  <h4 className="text-base font-semibold text-[var(--text)]">Structural Consistency</h4>
                  <p className="text-xs text-[var(--text-muted)] leading-relaxed">
                    Audits cross-references to figures, tables, and equations. Verifies that claimed experimental assets actually exist within the manuscript text.
                  </p>
                </div>

                <div className="saas-card p-6 space-y-3">
                  <div className="w-10 h-10 rounded-xl bg-zinc-800 border border-zinc-700/80 flex items-center justify-center text-zinc-200 font-mono font-bold">
                    03
                  </div>
                  <h4 className="text-base font-semibold text-[var(--text)]">Stylometric NLP Telemetry</h4>
                  <p className="text-xs text-[var(--text-muted)] leading-relaxed">
                    Scans passive voice hedging, vocabulary richness, and section-by-section stylistic drift to detect anomalous synthetic composition patterns.
                  </p>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* PROGRESS VIEW */}
        {viewState === "progress" && (
          <div className="max-w-2xl mx-auto py-12">
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
          <ReportDashboard
            data={reportData}
            isMock={isMockMode}
            onBack={handleReset}
            onReset={handleReset}
          />
        )}

        {/* ERROR VIEW */}
        {viewState === "error" && (
          <div className="max-w-xl mx-auto py-12">
            <AnalysisError message={errorMessage} onRetry={handleReset} />
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