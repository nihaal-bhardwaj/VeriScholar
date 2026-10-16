"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";

const METHODOLOGY_STEPS = [
  {
    num: "01",
    heading: "PDF Parsing & Layout Extraction",
    desc: "Text, layout, and structural elements are extracted from the manuscript, separating columns, tables, headers, and reference blocks.",
    tag: "Core Engine",
  },
  {
    num: "02",
    heading: "Bibliographic Graph Ingestion",
    desc: "Title, authors, and DOI candidates are extracted and matched against OpenAlex, Crossref, and preprint graph APIs.",
    tag: "Graph Network",
  },
  {
    num: "03",
    heading: "Citation Reference Resolution",
    desc: "Every cited entry is parsed, normalized, and queried across bibliographic indices to detect phantom references and missing DOIs.",
    tag: "Integrity Audit",
  },
  {
    num: "04",
    heading: "Internal Structural Consistency",
    desc: "Text references to figures, equations, and tables are verified against actual manuscript contents to ensure claimed assets exist.",
    tag: "Rule Engine",
  },
  {
    num: "05",
    heading: "Stylometric NLP Telemetry",
    desc: "The manuscript is scanned for passive voice hedging decay, vocabulary complexity, and distribution drift between sections.",
    tag: "Machine Learning",
  },
  {
    num: "06",
    heading: "Forensic Synthesis & Scoring",
    desc: "All multi-vector signals are aggregated into calibrated risk scores and an inspectable dossier with line-by-line evidence.",
    tag: "Risk Report",
  },
];

export default function MethodologyPage() {
  const [theme, setTheme] = useState<"dark" | "light">("dark");

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

  return (
    <div className="min-h-screen flex flex-col justify-between font-sans bg-[var(--bg)] text-[var(--text)] transition-colors relative z-10">
      {/* ═════════════════════════════════════════════════════════════════════
          MODERN SAAS NAVBAR
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
              className="px-3.5 py-1.5 rounded-lg text-zinc-400 hover:text-zinc-100 transition-all cursor-pointer flex items-center gap-1.5"
            >
              <svg className="w-3.5 h-3.5 text-zinc-400" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2" />
              </svg>
              <span>Review Integrity</span>
            </Link>

            <Link
              href="/methodology"
              className="px-3.5 py-1.5 rounded-lg bg-zinc-100 text-zinc-950 shadow-sm transition-all cursor-pointer font-semibold"
            >
              Methodology
            </Link>
          </nav>

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
      </header>

      {/* ═════════════════════════════════════════════════════════════════════
          MAIN CONTENT
         ═════════════════════════════════════════════════════════════════════ */}
      <main className="flex-1 w-full max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 py-12 sm:py-16 space-y-12 animate-tab-panel">
        <div className="space-y-4 max-w-2xl">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-zinc-800/80 border border-zinc-700/60 text-xs font-semibold text-zinc-300">
            <span className="w-1.5 h-1.5 rounded-full bg-emerald-400" />
            Verification Methodology &amp; Ethics Protocol
          </div>
          <h1 className="text-3xl sm:text-5xl font-extrabold text-[var(--text)] tracking-tight">
            How VeriScholar screens a manuscript
          </h1>
          <p className="text-sm sm:text-base text-[var(--text-muted)] leading-relaxed">
            Every analysis runs through six sequential validation stages. Each stage produces inspectable evidence — none of them in isolation is treated as proof of misconduct.
          </p>
        </div>

        {/* 6 Step Cards Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {METHODOLOGY_STEPS.map((step) => (
            <div key={step.num} className="saas-card p-6 space-y-3">
              <div className="flex items-center justify-between">
                <span className="w-8 h-8 rounded-lg bg-zinc-800 border border-white/[0.08] text-xs font-mono font-bold text-zinc-200 flex items-center justify-center">
                  {step.num}
                </span>
                <span className="text-[10px] font-mono px-2 py-0.5 rounded-full bg-zinc-800 text-zinc-400 border border-zinc-700/80">
                  {step.tag}
                </span>
              </div>
              <h3 className="text-base font-bold text-[var(--text)] tracking-tight">
                {step.heading}
              </h3>
              <p className="text-xs sm:text-sm text-[var(--text-muted)] leading-relaxed">
                {step.desc}
              </p>
            </div>
          ))}
        </div>

        {/* Closing Ethics Policy */}
        <div className="saas-card p-6 sm:p-8 space-y-3 bg-zinc-900 border border-white/[0.08]">
          <div className="text-xs font-mono uppercase tracking-wider text-zinc-400 font-bold">
            Ethical Boundaries &amp; Product Limits
          </div>
          <h2 className="text-lg sm:text-xl font-bold text-[var(--text)]">
            Screening Instrument &mdash; Not an Accusation
          </h2>
          <p className="text-xs sm:text-sm text-[var(--text-muted)] leading-relaxed">
            VeriScholar checks metadata, citations, and internal consistency against public records. A high attention rating indicates specific anomalies that merit a closer look by peer reviewers. It never claims fraud has been proven, and a low score does not replace thorough human review.
          </p>
        </div>
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
