"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";

const METHODOLOGY_STEPS = [
  {
    num: "i.",
    heading: "PDF extraction",
    desc: "Text, structure, and layout are pulled from the document, including columns, figures, and reference boundaries.",
  },
  {
    num: "ii.",
    heading: "Document analysis",
    desc: "Title, authors, abstract, and sections are identified and separated from front matter.",
  },
  {
    num: "iii.",
    heading: "Metadata verification",
    desc: "Title, authors, and DOI are checked against Crossref and OpenAlex for a matching record.",
  },
  {
    num: "iv.",
    heading: "Citation verification",
    desc: "Each reference is normalized and resolved against public bibliographic indexes.",
  },
  {
    num: "v.",
    heading: "NLP / ML signals",
    desc: "Text is scanned for statistical patterns, duplication, and abstract-body consistency.",
  },
  {
    num: "vi.",
    heading: "Unified screening report",
    desc: "All signals are compiled into one report with risk, confidence, and extraction quality shown as separate measures.",
  },
];

export default function MethodologyPage() {
  const [theme, setTheme] = useState<"dark" | "light">("dark");

  useEffect(() => {
    const currentTheme = document.documentElement.getAttribute("data-theme") as "dark" | "light" | null;
    if (currentTheme) {
      setTheme(currentTheme);
    }
  }, []);

  const toggleTheme = () => {
    const next = theme === "dark" ? "light" : "dark";
    setTheme(next);
    document.documentElement.setAttribute("data-theme", next);
  };

  return (
    <div className="min-h-screen flex flex-col justify-between relative z-10">
      {/* NAVBAR */}
      <header className="sticky top-0 z-50 w-full bg-[var(--bg)]/80 backdrop-blur-sm border-b border-[var(--border-soft)]">
        <div className="container-wide h-[76px] flex items-center justify-between">
          <Link href="/" className="flex items-baseline cursor-pointer">
            <span className="font-sans font-semibold text-lg tracking-tight text-[var(--text)]">
              Veri
            </span>
            <span className="font-serif italic font-medium text-xl text-[var(--text)]">
              Scholar
            </span>
          </Link>

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
                className="text-[var(--text)] border-b border-[var(--accent)] pb-0.5 cursor-pointer"
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

            <button
              type="button"
              onClick={toggleTheme}
              className="text-[var(--text-muted)] hover:text-[var(--text)] transition-colors p-1 cursor-pointer"
              aria-label="Toggle theme"
            >
              {theme === "dark" ? (
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

      {/* MAIN CONTENT */}
      <main className="flex-1">
        <div className="container-text py-16 sm:py-24 space-y-16">
          {/* Header */}
          <div className="space-y-4">
            <h1 className="font-serif font-medium text-[clamp(32px,4.5vw,46px)] text-[var(--text)] leading-tight tracking-tight">
              How VeriScholar reads a paper
            </h1>
            <p className="font-sans text-[17px] text-[var(--text-muted)] max-w-[54ch] leading-relaxed">
              Every report runs through the same six stages. Each one produces evidence — none of them, alone, is treated as proof of anything.
            </p>
          </div>

          {/* Ruled list of 6 steps */}
          <div className="divide-y divide-[var(--border-soft)] border-t border-b border-[var(--border-soft)]">
            {METHODOLOGY_STEPS.map((step) => (
              <div key={step.num} className="py-5 flex gap-6 items-start">
                <span className="font-serif italic text-lg text-[var(--text-faint)] w-6 shrink-0 pt-0.5">
                  {step.num}
                </span>
                <div className="space-y-1">
                  <h2 className="font-serif font-medium text-[19px] text-[var(--text)]">
                    {step.heading}
                  </h2>
                  <p className="font-sans text-sm text-[var(--text-muted)] leading-relaxed">
                    {step.desc}
                  </p>
                </div>
              </div>
            ))}
          </div>

          {/* Closing note block */}
          <section className="border-t border-[var(--border)] pt-8 mt-8 space-y-4">
            <h2 className="font-serif text-2xl font-medium text-[var(--text)]">
              What this is — and isn&apos;t
            </h2>
            <p className="font-sans text-sm text-[var(--text-muted)] leading-relaxed max-w-[64ch]">
              VeriScholar checks metadata, citations, and internal consistency against public records and the patterns typical of authentic papers, then reports what it finds as screening signals. A high risk score means something deserves a closer look, not that misconduct occurred — and a low score means no signals were found, not that the paper is verified as sound. Every report is meant to support a reviewer&apos;s judgment, not replace it.
            </p>
          </section>
        </div>
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
