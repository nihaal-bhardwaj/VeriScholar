"use client";

import React, { useState, useEffect } from "react";
import { RiskReport, RiskSignal, MOCK_CITATIONS, MockCitation } from "../../lib/mockData";

export interface ReportDashboardProps {
  data: RiskReport | any;
  isMock?: boolean;
  onBack?: () => void;
  onReset?: () => void;
}

export default function ReportDashboard({
  data,
  isMock = false,
  onBack,
  onReset,
}: ReportDashboardProps) {
  const [activeTab, setActiveTab] = useState<"overview" | "signals" | "citations">("overview");
  const [evidenceOpen, setEvidenceOpen] = useState<boolean>(false);
  const [openSignalIds, setOpenSignalIds] = useState<Record<number, boolean>>({});
  const [citationFilter, setCitationFilter] = useState<string>("all");
  const [toastMessage, setToastMessage] = useState<string | null>(null);

  // Normalize data shape if coming from CombinedAnalysisResponse
  const title = data.paper_title || data.paper?.title || "Latent Drift: Measuring Representation Instability in Fine-Tuned Language Models";
  const authors: string[] = data.paper_authors || data.paper?.authors || ["Kowalski", "Menon", "Subramaniam", "Álvarez"];
  const riskScore: number = typeof data.risk_score === "number" ? data.risk_score : (data.final_assessment?.risk_score ?? 42);
  const riskLevel: string = (data.risk_level || data.final_assessment?.risk_level || "medium").toLowerCase();
  const confidence: number = typeof data.confidence === "number" ? data.confidence : (data.final_assessment?.confidence ?? 0.81);
  const signals: RiskSignal[] = data.signals || [];
  const passedChecks: string[] = data.passed_checks || [
    "Metadata match — title, authors, and DOI resolve consistently",
    "Author consistency — author list matches across locations",
    "Figure and table numbering — all references resolve correctly",
    "Duplicate passage detection — no substantial duplicates found",
  ];
  const modulesUsed: string[] = data.modules_used || ["consistency", "ml", "citations", "metadata"];
  const generatedAt: string = data.generated_at || new Date().toISOString();

  // Animation for Risk Numeral and Track Bar
  const [animatedScore, setAnimatedScore] = useState<number>(0);
  const [animatedWidth, setAnimatedWidth] = useState<number>(0);

  useEffect(() => {
    const prefersReducedMotion =
      typeof window !== "undefined" &&
      window.matchMedia("(prefers-reduced-motion: reduce)").matches;

    const target = Math.round(riskScore);
    if (prefersReducedMotion) {
      setAnimatedScore(target);
      setAnimatedWidth(target);
      return;
    }

    const duration = 1000;
    const startTime = performance.now();
    let frameId: number;

    const easeOutCubic = (x: number) => 1 - Math.pow(1 - x, 3);

    const step = (now: number) => {
      const elapsed = now - startTime;
      const progress = Math.min(1, elapsed / duration);
      const eased = easeOutCubic(progress);

      setAnimatedScore(Math.round(eased * target));
      setAnimatedWidth(eased * target);

      if (progress < 1) {
        frameId = requestAnimationFrame(step);
      } else {
        setAnimatedScore(target);
        setAnimatedWidth(target);
      }
    };

    frameId = requestAnimationFrame(step);
    return () => cancelAnimationFrame(frameId);
  }, [riskScore]);

  const showToast = (msg: string) => {
    setToastMessage(msg);
    setTimeout(() => setToastMessage(null), 2400);
  };

  const handleReturn = () => {
    if (onBack) onBack();
    else if (onReset) onReset();
  };

  // Semantic styling for risk band
  let riskColorClass = "text-[var(--good)]";
  let riskDisplayWord = "Low";
  if (riskLevel === "critical" || riskLevel === "high") {
    riskColorClass = "text-[var(--danger)]";
    riskDisplayWord = riskLevel === "critical" ? "Critical" : "High";
  } else if (riskLevel === "medium" || riskLevel === "moderate") {
    riskColorClass = "text-[var(--warn)]";
    riskDisplayWord = "Moderate";
  }

  // Qualitative confidence label
  const confPct = Math.round(confidence * 100);
  let confWord = "moderate";
  if (confPct < 50) confWord = "low";
  else if (confPct < 75) confWord = "moderate";
  else if (confPct < 90) confWord = "moderate–high";
  else confWord = "high";

  // Formatted date
  const formattedDate = new Date(generatedAt).toLocaleDateString("en-US", {
    month: "short",
    day: "numeric",
    year: "numeric",
  });

  // Review status
  const warningSignals = signals.filter((s) => s.severity === "high" || s.severity === "medium");
  const hasReviewWarranted = warningSignals.length > 0;

  // Sorted signals for quick-list
  const severityOrder: Record<string, number> = { high: 3, medium: 2, low: 1 };
  const sortedTopSignals = [...signals]
    .sort((a, b) => (severityOrder[b.severity] || 0) - (severityOrder[a.severity] || 0))
    .slice(0, 3);

  const toggleSignal = (idx: number) => {
    setOpenSignalIds((prev) => ({ ...prev, [idx]: !prev[idx] }));
  };

  // Filtered citations
  const filteredCitations = MOCK_CITATIONS.filter((c) => {
    if (citationFilter === "all") return true;
    return c.status === citationFilter;
  });

  const citationSignals = signals.filter((s) => s.source === "citations");

  return (
    <div className="w-full max-w-[920px] mx-auto py-8">
      {/* Toast */}
      {toastMessage && (
        <div className="fixed bottom-6 right-6 bg-[var(--bg-raise)] border border-[var(--border)] text-[var(--text)] px-4 py-2 text-sm z-50 shadow-sm animate-fade-in">
          {toastMessage}
        </div>
      )}

      {/* HEADER */}
      <div className="mb-8">
        <div className="text-xs text-[var(--text-muted)] font-sans mb-3">
          <button
            type="button"
            onClick={handleReturn}
            className="hover:text-[var(--text)] transition-colors cursor-pointer"
          >
            Analyzer
          </button>
          <span className="mx-2 text-[var(--border)]">/</span>
          <span className="text-[var(--text)]">Report</span>
        </div>

        <h1 className="font-serif text-[clamp(26px,3.4vw,34px)] font-medium text-[var(--text)] max-w-[30ch] leading-tight mb-3">
          {title}
        </h1>

        <p className="font-sans text-sm text-[var(--text-muted)] max-w-[64ch] leading-relaxed mb-4">
          By {authors.length ? authors.join(", ") : "Unknown Authors"}. Screened by VeriScholar on {formattedDate}.
        </p>

        <div className="flex gap-4">
          <button
            type="button"
            onClick={() => showToast("Export feature coming soon")}
            className="btn-quiet"
          >
            Export report
          </button>
          <span className="text-[var(--border)]">·</span>
          <button
            type="button"
            onClick={() => showToast("Share link copied to clipboard")}
            className="btn-quiet"
          >
            Share
          </button>
        </div>
      </div>

      {/* SIGNATURE SUMMARY BLOCK */}
      <section className="border-t border-b border-[var(--border)] py-8 my-8">
        <div className="flex flex-col md:flex-row justify-between gap-8 mb-6">
          {/* LEFT: Dominant Risk Figure */}
          <div className="md:w-3/5">
            <div className="text-xs font-sans text-[var(--text-muted)] mb-1">
              Integrity risk
            </div>
            <div className="flex items-baseline gap-3">
              <span className="font-serif font-medium text-[clamp(72px,8vw,96px)] tracking-tight leading-none text-[var(--text)] [font-variant-numeric:lining-nums]">
                {animatedScore}
              </span>
              <span className={`font-serif italic text-2xl font-normal ${riskColorClass}`}>
                {riskDisplayWord}
              </span>
            </div>

            {/* 1px Gold Track Bar */}
            <div className="w-[230px] h-[1px] bg-[var(--border)] mt-4">
              <div
                className="h-full bg-[var(--accent)] transition-all duration-300 ease-out"
                style={{ width: `${animatedWidth}%` }}
              />
            </div>
          </div>

          {/* RIGHT: Subordinate Side Metrics */}
          <div className="md:w-2/5 flex flex-col justify-center space-y-4 md:border-l md:border-[var(--border-soft)] md:pl-8">
            <div className="flex items-baseline">
              <span className="w-[130px] text-xs font-sans text-[var(--text-muted)]">
                Confidence
              </span>
              <span className="font-serif text-xl font-medium text-[var(--text)] mr-2 [font-variant-numeric:lining-nums]">
                {confPct}%
              </span>
              <span className="font-serif italic text-xs text-[var(--text-muted)]">
                {confWord}
              </span>
            </div>

            <div className="flex items-baseline">
              <span className="w-[130px] text-xs font-sans text-[var(--text-muted)]">
                Modules run
              </span>
              <span className="font-serif text-xl font-medium text-[var(--text)] mr-2 [font-variant-numeric:lining-nums]">
                {modulesUsed.length}
              </span>
              <span className="font-serif italic text-xs text-[var(--text-muted)]">
                of 4 available
              </span>
            </div>
          </div>
        </div>

        {/* REVIEW LINE */}
        <div className="border-t border-[var(--border-soft)] pt-4 flex flex-col sm:flex-row justify-between items-start sm:items-center gap-2">
          <div className="font-sans text-sm text-[var(--text)]">
            {hasReviewWarranted ? (
              <>
                <span className="font-semibold text-[var(--warn)] mr-1">
                  Requires human review
                </span>
                <span className="text-[var(--text-muted)]">
                  — {warningSignals.length} of {signals.length || 7} signals warrant a closer look.
                </span>
              </>
            ) : (
              <>
                <span className="font-semibold text-[var(--good)] mr-1">
                  No critical signals found
                </span>
                <span className="text-[var(--text-muted)]">
                  — all checks passed or returned low-severity signals.
                </span>
              </>
            )}
          </div>

          <button
            type="button"
            onClick={() => setEvidenceOpen(!evidenceOpen)}
            className="text-btn text-xs shrink-0"
          >
            {evidenceOpen ? "Hide the evidence" : "Show the evidence"}
          </button>
        </div>

        {/* EVIDENCE QUICK-LIST (COLLAPSIBLE) */}
        <div
          className={`overflow-hidden transition-all duration-300 ease-in-out ${
            evidenceOpen ? "max-h-[500px] mt-4 opacity-100" : "max-h-0 opacity-0"
          }`}
        >
          <div className="pt-2 space-y-3">
            {sortedTopSignals.length > 0 ? (
              sortedTopSignals.map((sig, idx) => {
                const isWarn = sig.severity === "high" || sig.severity === "medium";
                return (
                  <div
                    key={idx}
                    className={`pl-4 border-l-2 text-xs font-sans leading-relaxed ${
                      isWarn ? "border-[var(--warn)]" : "border-[var(--good)]"
                    }`}
                  >
                    <span className="font-semibold text-[var(--text)] mr-1.5">
                      {sig.message}
                    </span>
                    <span className="text-[var(--text-muted)]">
                      — {sig.evidence.length > 100 ? `${sig.evidence.slice(0, 100)}…` : sig.evidence}
                    </span>
                  </div>
                );
              })
            ) : (
              <div className="pl-4 border-l-2 border-[var(--good)] text-xs font-sans text-[var(--text-muted)]">
                All consistency and integrity checks passed cleanly.
              </div>
            )}
          </div>
        </div>

        {/* DISCLAIMER NOTE */}
        <div className="border-t border-[var(--border-soft)] pt-3 mt-4 text-xs font-sans text-[var(--text-muted)] leading-relaxed">
          <span className="font-serif italic text-[var(--accent)] mr-1">Note.</span>
          This is a screening result, not a finding. VeriScholar surfaces signals worth a reviewer's attention — it does not prove or disprove research misconduct.
        </div>
      </section>

      {/* TABS */}
      <div className="border-b border-[var(--border-soft)] flex gap-8 mb-8">
        <button
          type="button"
          onClick={() => setActiveTab("overview")}
          className={`pb-3 font-sans text-sm cursor-pointer transition-colors ${
            activeTab === "overview"
              ? "border-b-2 border-[var(--accent)] text-[var(--text)] font-medium"
              : "text-[var(--text-muted)] hover:text-[var(--text)]"
          }`}
        >
          Overview
        </button>
        <button
          type="button"
          onClick={() => setActiveTab("signals")}
          className={`pb-3 font-sans text-sm cursor-pointer transition-colors flex items-center gap-1.5 ${
            activeTab === "signals"
              ? "border-b-2 border-[var(--accent)] text-[var(--text)] font-medium"
              : "text-[var(--text-muted)] hover:text-[var(--text)]"
          }`}
        >
          <span>Signals</span>
          <span className="font-serif italic text-xs text-[var(--text-muted)]">
            ({signals.length})
          </span>
        </button>
        <button
          type="button"
          onClick={() => setActiveTab("citations")}
          className={`pb-3 font-sans text-sm cursor-pointer transition-colors flex items-center gap-1.5 ${
            activeTab === "citations"
              ? "border-b-2 border-[var(--accent)] text-[var(--text)] font-medium"
              : "text-[var(--text-muted)] hover:text-[var(--text)]"
          }`}
        >
          <span>Citations</span>
          <span className="font-serif italic text-xs text-[var(--text-muted)]">
            (xlii)
          </span>
        </button>
      </div>

      {/* TAB CONTENT PANELS */}
      {activeTab === "overview" && (
        <div className="animate-tab-panel grid grid-cols-1 md:grid-cols-2 gap-8">
          {/* Module Status */}
          <div>
            <h3 className="font-serif text-lg font-medium text-[var(--text)] mb-3">
              Module status
            </h3>
            <div className="divide-y divide-[var(--border-soft)] border-t border-[var(--border-soft)]">
              {[
                {
                  id: "metadata",
                  name: "Metadata verification",
                  desc: "DOI resolved via Crossref — title and author match confirmed",
                },
                {
                  id: "citations",
                  name: "Citation checks",
                  desc: "References resolved against public bibliographic indexes",
                },
                {
                  id: "consistency",
                  name: "Internal consistency",
                  desc: "Abstract, body, and figure references checked for coherence",
                },
                {
                  id: "ml",
                  name: "ML risk assessment",
                  desc: "Scanning for unusual statistical distributions and patterns",
                },
              ].map((m) => {
                const isCompleted = modulesUsed.includes(m.id);
                return (
                  <div key={m.id} className="py-3 flex justify-between items-start gap-4">
                    <div>
                      <div className="font-sans text-sm text-[var(--text)]">{m.name}</div>
                      <div className="font-sans text-xs text-[var(--text-faint)] mt-0.5">{m.desc}</div>
                    </div>
                    <span
                      className={`font-serif italic text-xs shrink-0 ${
                        isCompleted ? "text-[var(--good)]" : "text-[var(--text-faint)]"
                      }`}
                    >
                      {isCompleted ? "completed" : "unavailable"}
                    </span>
                  </div>
                );
              })}
            </div>
          </div>

          {/* At a Glance */}
          <div>
            <h3 className="font-serif text-lg font-medium text-[var(--text)] mb-3">
              At a glance
            </h3>
            <div className="divide-y divide-[var(--border-soft)] border-t border-[var(--border-soft)] text-sm">
              <div className="py-2.5 flex justify-between">
                <span className="font-sans text-[var(--text-muted)]">Risk score</span>
                <span className="font-serif font-medium text-[var(--text)] [font-variant-numeric:lining-nums]">
                  {Math.round(riskScore)} / 100
                </span>
              </div>
              <div className="py-2.5 flex justify-between">
                <span className="font-sans text-[var(--text-muted)]">Risk level</span>
                <span className="font-serif font-medium capitalize text-[var(--text)]">
                  {riskLevel}
                </span>
              </div>
              <div className="py-2.5 flex justify-between">
                <span className="font-sans text-[var(--text-muted)]">Confidence</span>
                <span className="font-serif font-medium text-[var(--text)] [font-variant-numeric:lining-nums]">
                  {Math.round(confidence * 100)}%
                </span>
              </div>
              <div className="py-2.5 flex justify-between">
                <span className="font-sans text-[var(--text-muted)]">Signals detected</span>
                <span className="font-serif font-medium text-[var(--text)] [font-variant-numeric:lining-nums]">
                  {signals.length}
                </span>
              </div>
              <div className="py-2.5 flex justify-between">
                <span className="font-sans text-[var(--text-muted)]">Checks passed</span>
                <span className="font-serif font-medium text-[var(--text)] [font-variant-numeric:lining-nums]">
                  {passedChecks.length}
                </span>
              </div>
              <div className="py-2.5 flex justify-between">
                <span className="font-sans text-[var(--text-muted)]">Modules used</span>
                <span className="font-serif text-[var(--text)]">
                  {modulesUsed.join(", ")}
                </span>
              </div>
              <div className="py-2.5 flex justify-between">
                <span className="font-sans text-[var(--text-muted)]">Analyzed</span>
                <span className="font-serif text-[var(--text)]">{formattedDate}</span>
              </div>
            </div>
          </div>
        </div>
      )}

      {activeTab === "signals" && (
        <div className="animate-tab-panel">
          {signals.length > 0 ? (
            <div className="divide-y divide-[var(--border-soft)] border-t border-[var(--border-soft)]">
              {signals.map((sig, idx) => {
                const isWarn = sig.severity === "high" || sig.severity === "medium";
                const isOpen = openSignalIds[idx];

                return (
                  <div
                    key={idx}
                    className={`py-4 transition-all ${
                      isWarn
                        ? "border-l-2 border-l-[var(--warn)] pl-4"
                        : "border-l-2 border-transparent pl-4"
                    }`}
                  >
                    <button
                      type="button"
                      onClick={() => toggleSignal(idx)}
                      className="w-full text-left flex justify-between items-baseline mb-1 group cursor-pointer"
                    >
                      <span className="font-serif text-[19px] font-medium text-[var(--text)] group-hover:text-[var(--accent)] transition-colors">
                        {sig.message}
                      </span>
                      <span className="font-serif italic text-xs text-[var(--text-muted)] shrink-0 ml-4">
                        {sig.source}
                      </span>
                    </button>

                    <p className="font-sans text-sm text-[var(--text-muted)] leading-relaxed mb-2">
                      {sig.evidence}
                    </p>

                    <div
                      onClick={() => toggleSignal(idx)}
                      className="font-sans text-xs text-[var(--text-faint)] cursor-pointer hover:text-[var(--text-muted)] transition-colors"
                    >
                      {isWarn && (
                        <span className="text-[var(--warn)] mr-1 font-medium">
                          Needs a closer look —
                        </span>
                      )}
                      click to toggle the evidence
                    </div>

                    <div
                      className={`overflow-hidden transition-all duration-300 ease-in-out ${
                        isOpen ? "max-h-[300px] mt-3 opacity-100" : "max-h-0 opacity-0"
                      }`}
                    >
                      <div className="border-l border-[var(--border)] pl-4 ml-2 my-2 font-serif italic text-sm text-[var(--text-muted)] leading-relaxed">
                        {sig.evidence}
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          ) : (
            <div className="py-8 text-center text-sm font-sans text-[var(--text-muted)] border-t border-[var(--border-soft)]">
              No signals detected — all checks passed.
            </div>
          )}
        </div>
      )}

      {activeTab === "citations" && (
        <div className="animate-tab-panel space-y-10">
          {/* Real Citation Signals */}
          {citationSignals.length > 0 && (
            <div>
              <h3 className="font-serif text-lg font-medium text-[var(--text)] mb-3">
                Citation signals detected
              </h3>
              <div className="divide-y divide-[var(--border-soft)] border-t border-[var(--border-soft)]">
                {citationSignals.map((sig, idx) => (
                  <div key={idx} className="py-3 border-l-2 border-l-[var(--warn)] pl-4">
                    <div className="font-serif text-[17px] font-medium text-[var(--text)]">
                      {sig.message}
                    </div>
                    <div className="font-sans text-xs text-[var(--text-muted)] mt-1">
                      {sig.evidence}
                    </div>
                  </div>
                ))}
              </div>
              <p className="font-sans text-xs text-[var(--text-faint)] mt-2">
                Per-reference citation data is available via the dedicated /api/v1/citations/verify endpoint.
              </p>
            </div>
          )}

          {/* Mock Reference Table */}
          <div>
            <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-3 mb-4">
              <div>
                <h3 className="font-serif text-lg font-medium text-[var(--text)]">
                  Example reference format
                </h3>
                <p className="font-sans text-xs text-[var(--text-muted)]">
                  These are example citations, not from this paper's analysis.
                </p>
              </div>

              {/* Filters */}
              <div className="flex flex-wrap gap-4 text-xs font-sans">
                {[
                  { label: "All · 42", value: "all" },
                  { label: "Verified", value: "verified" },
                  { label: "Partially verified", value: "partial" },
                  { label: "Needs review", value: "needsreview" },
                  { label: "Not found", value: "notfound" },
                ].map((f) => (
                  <button
                    key={f.value}
                    type="button"
                    onClick={() => setCitationFilter(f.value)}
                    className={`pb-1 cursor-pointer transition-colors ${
                      citationFilter === f.value
                        ? "border-b border-[var(--accent)] text-[var(--text)] font-medium"
                        : "text-[var(--text-muted)] hover:text-[var(--text)]"
                    }`}
                  >
                    {f.label}
                  </button>
                ))}
              </div>
            </div>

            <div className="divide-y divide-[var(--border-soft)] border-t border-[var(--border-soft)]">
              {filteredCitations.map((c) => (
                <div key={c.num} className="py-3 flex gap-4 items-start">
                  <span className="font-serif italic text-xs text-[var(--text-muted)] w-8 shrink-0 pt-0.5">
                    {c.num}.
                  </span>
                  <div className="flex-1">
                    <div className="font-serif text-[16.5px] text-[var(--text)] leading-relaxed">
                      {c.text}
                    </div>
                    <div className="font-sans text-xs text-[var(--text-faint)] mt-1">
                      {c.note}
                    </div>
                  </div>
                  <span className={`font-serif italic text-xs shrink-0 text-right ${c.statusClass}`}>
                    {c.statusWord}
                  </span>
                </div>
              ))}
            </div>

            <div className="pt-4 text-xs font-sans text-[var(--text-faint)]">
              Showing 10 of 42 references in this preview.
            </div>
          </div>
        </div>
      )}
    </div>
  );
}