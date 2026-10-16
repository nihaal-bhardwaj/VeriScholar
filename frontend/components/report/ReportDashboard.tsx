"use client";

import React, { useState, useEffect, useMemo } from "react";
import { RiskReport, RiskSignal, MOCK_CITATIONS } from "../../lib/mockData";

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
  const [activeTab, setActiveTab] = useState<"signals" | "citations" | "passed" | "overview">("signals");
  const [evidenceOpen, setEvidenceOpen] = useState<boolean>(false);
  const [openSignalIds, setOpenSignalIds] = useState<Record<number, boolean>>({});
  const [citationFilter, setCitationFilter] = useState<string>("all");
  const [citationSearch, setCitationSearch] = useState<string>("");
  const [signalSeverityFilter, setSignalSeverityFilter] = useState<string>("all");
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
    "Author consistency — author list matches across document header and citations",
    "Figure and table numbering — all cited references resolve correctly",
    "Duplicate passage detection — no substantial verbatim duplication found",
    "Section structural boundaries — Abstract, Methods, Results, and References intact",
  ];
  const modulesUsed: string[] = data.modules_used || ["consistency", "ml", "citations", "metadata"];
  const generatedAt: string = data.generated_at || new Date().toISOString();

  // Animation for Risk Score
  const [animatedScore, setAnimatedScore] = useState<number>(0);

  useEffect(() => {
    const prefersReducedMotion =
      typeof window !== "undefined" &&
      window.matchMedia("(prefers-reduced-motion: reduce)").matches;

    const target = Math.round(riskScore);
    if (prefersReducedMotion) {
      setAnimatedScore(target);
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

      if (progress < 1) {
        frameId = requestAnimationFrame(step);
      } else {
        setAnimatedScore(target);
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

  // Semantic styling for risk tier
  const isHighRisk = riskLevel === "critical" || riskLevel === "high";
  const isMediumRisk = riskLevel === "medium" || riskLevel === "moderate";

  const riskBadgeConfig = isHighRisk
    ? {
        label: riskLevel === "critical" ? "Critical Risk Alert" : "High Attention Recommended",
        badgeBg: "bg-rose-500/10 text-rose-400 border-rose-500/20",
        dotColor: "bg-rose-400",
        gradient: "from-rose-500 to-red-600",
      }
    : isMediumRisk
    ? {
        label: "Moderate Scrutiny Recommended",
        badgeBg: "bg-amber-500/10 text-amber-400 border-amber-500/20",
        dotColor: "bg-amber-400",
        gradient: "from-amber-400 to-amber-600",
      }
    : {
        label: "Low Attention Needed",
        badgeBg: "bg-emerald-500/10 text-emerald-400 border-emerald-500/20",
        dotColor: "bg-emerald-400",
        gradient: "from-emerald-400 to-teal-500",
      };

  const confPct = Math.round(confidence * 100);
  const formattedDate = new Date(generatedAt).toLocaleDateString("en-US", {
    month: "short",
    day: "numeric",
    year: "numeric",
  });

  const toggleSignal = (originalIndex: number) => {
    setOpenSignalIds((prev) => ({ ...prev, [originalIndex]: !prev[originalIndex] }));
  };

  // Citations data normalization
  const rawDetails: any[] = data.citation_results?.details || [];
  const hasRealCitations = rawDetails.length > 0;

  const realCitations = rawDetails.map((item, idx) => ({
    num: item.number ?? (idx + 1),
    text: item.title || item.raw_text,
    status: item.verified ? "verified" : "notfound",
    statusWord: item.verified ? "Verified" : "Unresolved",
    statusClass: item.verified
      ? "bg-emerald-500/10 text-emerald-400 border-emerald-500/20"
      : "bg-rose-500/10 text-rose-400 border-rose-500/20",
    note: item.doi ? `DOI: ${item.doi}` : (item.note || item.raw_text),
  }));

  const citationItems = hasRealCitations ? realCitations : MOCK_CITATIONS;
  const verifiedCount = citationItems.filter((c) => c.status === "verified").length;
  const unresolvedCount = citationItems.length - verifiedCount;
  const citationResolutionPct = citationItems.length > 0 ? Math.round((verifiedCount / citationItems.length) * 100) : 0;

  const filteredCitations = useMemo(() => {
    let result = citationItems;
    if (citationFilter !== "all") {
      result = result.filter((c) => c.status === citationFilter);
    }
    if (citationSearch.trim()) {
      const q = citationSearch.toLowerCase();
      result = result.filter(
        (c) =>
          c.text.toLowerCase().includes(q) ||
          (c.note && c.note.toLowerCase().includes(q))
      );
    }
    return result;
  }, [citationItems, citationFilter, citationSearch]);

  const filteredSignals = useMemo(() => {
    const indexed = signals.map((signal, originalIndex) => ({ signal, originalIndex }));
    if (signalSeverityFilter === "all") return indexed;
    return indexed.filter((item) => item.signal.severity === signalSeverityFilter);
  }, [signals, signalSeverityFilter]);

  const handleExportJson = () => {
    const blob = new Blob([JSON.stringify(data, null, 2)], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `verischolar-manuscript-audit-${Date.now()}.json`;
    a.click();
    setTimeout(() => URL.revokeObjectURL(url), 0);
  };

  return (
    <div className="w-full max-w-7xl mx-auto space-y-8 animate-tab-panel pb-16 font-sans">
      {/* Toast Notification */}
      {toastMessage && (
        <div className="fixed bottom-6 right-6 bg-zinc-900 border border-zinc-700/80 text-[var(--text)] px-4 py-2.5 rounded-xl text-xs sm:text-sm z-50 shadow-2xl flex items-center gap-2 animate-tab-panel">
          <span className="w-2 h-2 rounded-full bg-zinc-200" />
          <span>{toastMessage}</span>
        </div>
      )}

      {/* ═════════════════════════════════════════════════════════════════════
          TOP HEADER CONTROLS (Paper Title, Authors, Export & Return)
         ═════════════════════════════════════════════════════════════════════ */}
      <div className="flex flex-col sm:flex-row sm:items-start justify-between gap-4 pb-6 border-b border-[var(--border)]">
        <div className="space-y-2 max-w-3xl">
          {/* Breadcrumbs */}
          <div className="flex items-center gap-2 text-xs font-mono text-[var(--text-faint)]">
            <button
              type="button"
              onClick={handleReturn}
              className="hover:text-[var(--text)] transition-colors cursor-pointer"
            >
              Manuscript Screener
            </button>
            <span>/</span>
            <span className="text-zinc-400 font-medium">Dossier Audit #{Math.round(riskScore * 97)}</span>
          </div>

          <h1 className="text-2xl sm:text-3xl font-bold tracking-tight text-[var(--text)] leading-tight">
            {title}
          </h1>

          <div className="flex flex-wrap items-center gap-2 text-xs text-[var(--text-muted)] pt-1">
            <span className="font-medium text-[var(--text)]">Authors:</span>
            <span>{authors.length ? authors.join(", ") : "Unknown Authors"}</span>
            <span>&bull;</span>
            <span className="font-mono text-[var(--text-faint)]">Screened on {formattedDate}</span>
          </div>
        </div>

        {/* Quick Action Buttons */}
        <div className="flex items-center gap-2.5 shrink-0 pt-2 sm:pt-0">
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
            Export Dossier
          </button>

          <button
            type="button"
            onClick={handleReturn}
            className="btn-primary text-xs sm:text-sm px-4 py-2 cursor-pointer"
          >
            <svg className="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <line x1="12" y1="5" x2="12" y2="19" />
              <line x1="5" y1="12" x2="19" y2="12" />
            </svg>
            Screen New Paper
          </button>
        </div>
      </div>

      {/* ═════════════════════════════════════════════════════════════════════
          TWO-COLUMN DASHBOARD GRID
         ═════════════════════════════════════════════════════════════════════ */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-start">
        {/* ─────────────────────────────────────────────────────────────
            LEFT COLUMN (35% width, ~4 cols): Executive Forensic Rating
           ───────────────────────────────────────────────────────────── */}
        <aside className="lg:col-span-4 space-y-6 lg:sticky lg:top-24">
          {/* Main Risk Rating Card */}
          <div className="saas-card p-6 relative overflow-hidden space-y-6">
            <div className="flex items-center justify-between text-xs font-semibold text-[var(--text-muted)] tracking-wider uppercase border-b border-[var(--border-soft)] pb-3">
              <span>Composite Risk Rating</span>
              <span className="font-mono text-xs text-[var(--text-faint)]">
                {modulesUsed.length} modules active
              </span>
            </div>

            {/* Gauge Hero Readout */}
            <div className="text-center space-y-3 py-2">
              <div className="inline-flex items-baseline justify-center gap-2">
                <span className="text-5xl sm:text-6xl font-extrabold tracking-tight text-[var(--text)] font-mono">
                  {animatedScore}
                </span>
                <span className="text-lg font-semibold text-[var(--text-faint)] font-mono">
                  / 100
                </span>
              </div>

              {/* Status Pill */}
              <div>
                <span className={`inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full text-xs font-semibold border backdrop-blur-sm ${riskBadgeConfig.badgeBg}`}>
                  <span className={`w-2 h-2 rounded-full ${riskBadgeConfig.dotColor} animate-pulse`} />
                  {riskBadgeConfig.label}
                </span>
              </div>

              {/* Progress Track */}
              <div className="w-full bg-zinc-800/80 rounded-full h-2 overflow-hidden mt-3 p-0.5 border border-white/[0.05]">
                <div
                  className={`h-full bg-gradient-to-r ${riskBadgeConfig.gradient} rounded-full transition-all duration-1000`}
                  style={{ width: `${animatedScore}%` }}
                />
              </div>

              <div className="flex justify-between text-[11px] font-mono text-[var(--text-faint)] pt-1">
                <span>0 (Clean)</span>
                <span>50 (Moderate)</span>
                <span>100 (Critical)</span>
              </div>
            </div>

            {/* Ethical Guidance Notice */}
            <div className="p-3.5 rounded-xl bg-zinc-900/60 border border-white/[0.06] text-xs text-[var(--text-muted)] leading-relaxed space-y-1">
              <div className="font-semibold text-[10px] uppercase tracking-wider text-zinc-300 flex items-center gap-1.5 font-mono">
                <svg className="w-3.5 h-3.5" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <circle cx="12" cy="12" r="10" />
                  <line x1="12" y1="16" x2="12" y2="12" />
                  <line x1="12" y1="8" x2="12.01" y2="8" />
                </svg>
                Human Review Notice
              </div>
              <p>
                This calibrated risk estimate highlights inspectable signals for peer review. It is an editorial screening instrument, not a determination of fraud.
              </p>
            </div>
          </div>

          {/* Telemetry Metric Tiles */}
          <div className="saas-card p-5 space-y-3.5">
            <div className="text-xs font-semibold uppercase tracking-wider text-[var(--text-muted)] pb-2 border-b border-[var(--border-soft)]">
              Forensic Telemetry
            </div>

            <div className="space-y-3">
              {/* Tile 1: Citation Graph */}
              <div className="p-3 rounded-lg bg-zinc-900/60 border border-white/[0.05] space-y-1.5">
                <div className="flex items-center justify-between text-xs font-medium">
                  <span className="text-[var(--text)] flex items-center gap-1.5">
                    <span className="w-1.5 h-1.5 rounded-full bg-emerald-400" />
                    Citation Verification
                  </span>
                  <span className="font-mono text-emerald-400 font-semibold">{citationResolutionPct}%</span>
                </div>
                <div className="w-full bg-zinc-800 rounded-full h-1 overflow-hidden">
                  <div className="bg-emerald-400 h-full rounded-full" style={{ width: `${citationResolutionPct}%` }} />
                </div>
                <div className="text-[10px] text-[var(--text-faint)] font-mono">
                  {verifiedCount} verified &bull; {unresolvedCount} unresolved DOIs
                </div>
              </div>

              {/* Tile 2: Structural Consistency */}
              <div className="p-3 rounded-lg bg-zinc-900/60 border border-white/[0.05] space-y-1">
                <div className="flex items-center justify-between text-xs font-medium">
                  <span className="text-[var(--text)] flex items-center gap-1.5">
                    <span className="w-1.5 h-1.5 rounded-full bg-emerald-400" />
                    Internal Consistency
                  </span>
                  <span className="font-mono text-emerald-400 font-semibold">{passedChecks.length} Passed</span>
                </div>
                <div className="text-[10px] text-[var(--text-faint)] font-mono">
                  Sections, equation refs &amp; figure tags intact
                </div>
              </div>

              {/* Tile 3: Stylometric NLP */}
              <div className="p-3 rounded-lg bg-zinc-900/60 border border-white/[0.05] space-y-1">
                <div className="flex items-center justify-between text-xs font-medium">
                  <span className="text-[var(--text)] flex items-center gap-1.5">
                    <span className="w-1.5 h-1.5 rounded-full bg-zinc-400" />
                    Stylometric NLP Index
                  </span>
                  <span className="font-mono text-zinc-300 font-semibold">{confPct}% Conf.</span>
                </div>
                <div className="text-[10px] text-[var(--text-faint)] font-mono">
                  Hedging, readability &amp; vocabulary scan
                </div>
              </div>
            </div>
          </div>
        </aside>

        {/* ─────────────────────────────────────────────────────────────
            RIGHT COLUMN (65% width, ~8 cols): Interactive Ledgers
           ───────────────────────────────────────────────────────────── */}
        <section className="lg:col-span-8 space-y-6">
          {/* Segmented Tab Bar */}
          <div className="flex items-center p-1 bg-zinc-900/90 rounded-xl border border-white/[0.08] shadow-inner text-xs font-medium">
            <button
              type="button"
              onClick={() => setActiveTab("signals")}
              className={`flex-1 py-2 px-3 rounded-lg transition-all cursor-pointer flex items-center justify-center gap-1.5 ${
                activeTab === "signals"
                  ? "bg-zinc-100 text-zinc-950 font-semibold shadow-sm"
                  : "text-zinc-400 hover:text-zinc-100"
              }`}
            >
              <span>Evidence Signals</span>
              <span className={`px-1.5 py-0.2 rounded-full text-[10px] font-mono ${
                activeTab === "signals" ? "bg-zinc-900/20 text-zinc-950 font-bold" : "bg-zinc-800 text-zinc-400"
              }`}>
                {signals.length}
              </span>
            </button>

            <button
              type="button"
              onClick={() => setActiveTab("citations")}
              className={`flex-1 py-2 px-3 rounded-lg transition-all cursor-pointer flex items-center justify-center gap-1.5 ${
                activeTab === "citations"
                  ? "bg-zinc-100 text-zinc-950 font-semibold shadow-sm"
                  : "text-zinc-400 hover:text-zinc-100"
              }`}
            >
              <span>Citation Screening</span>
              <span className={`px-1.5 py-0.2 rounded-full text-[10px] font-mono ${
                activeTab === "citations" ? "bg-zinc-900/20 text-zinc-950 font-bold" : "bg-zinc-800 text-zinc-400"
              }`}>
                {citationItems.length}
              </span>
            </button>

            <button
              type="button"
              onClick={() => setActiveTab("passed")}
              className={`flex-1 py-2 px-3 rounded-lg transition-all cursor-pointer flex items-center justify-center gap-1.5 ${
                activeTab === "passed"
                  ? "bg-zinc-100 text-zinc-950 font-semibold shadow-sm"
                  : "text-zinc-400 hover:text-zinc-100"
              }`}
            >
              <span>Passed Checks</span>
              <span className={`px-1.5 py-0.2 rounded-full text-[10px] font-mono ${
                activeTab === "passed" ? "bg-zinc-900/20 text-zinc-950 font-bold" : "bg-zinc-800 text-zinc-400"
              }`}>
                {passedChecks.length}
              </span>
            </button>

            <button
              type="button"
              onClick={() => setActiveTab("overview")}
              className={`flex-1 py-2 px-3 rounded-lg transition-all cursor-pointer flex items-center justify-center gap-1.5 ${
                activeTab === "overview"
                  ? "bg-zinc-100 text-zinc-950 font-semibold shadow-sm"
                  : "text-zinc-400 hover:text-zinc-100"
              }`}
            >
              Overview
            </button>
          </div>

          {/* ─────────────────────────────────────────────────────────
              TAB 1: EVIDENCE SIGNALS
             ───────────────────────────────────────────────────────── */}
          {activeTab === "signals" && (
            <div className="space-y-4 animate-tab-panel">
              {/* Severity Filter Pills */}
              <div className="saas-card p-3 flex flex-wrap items-center justify-between gap-2">
                <div className="flex items-center gap-1.5 text-xs">
                  <span className="text-[var(--text-faint)] mr-1">Filter Severity:</span>
                  {(
                    [
                      { id: "all", label: "All" },
                      { id: "high", label: "High" },
                      { id: "medium", label: "Medium" },
                      { id: "low", label: "Low" },
                    ] as const
                  ).map((f) => (
                    <button
                      key={f.id}
                      type="button"
                      onClick={() => setSignalSeverityFilter(f.id)}
                      className={`px-2.5 py-1 rounded-md text-xs font-medium cursor-pointer transition-all ${
                        signalSeverityFilter === f.id
                          ? "bg-zinc-700 text-white"
                          : "text-[var(--text-muted)] hover:text-[var(--text)]"
                      }`}
                    >
                      {f.label}
                    </button>
                  ))}
                </div>

                <div className="text-xs text-[var(--text-faint)] font-mono">
                  {filteredSignals.length} findings
                </div>
              </div>

              {/* Signals List */}
              {filteredSignals.length === 0 ? (
                <div className="saas-card p-12 text-center text-xs text-[var(--text-muted)]">
                  No signals detected in this severity tier.
                </div>
              ) : (
                <div className="space-y-3">
                  {filteredSignals.map(({ signal: sig, originalIndex }) => {
                    const isOpen = !!openSignalIds[originalIndex];
                    const isHigh = sig.severity === "high";
                    const isMedium = sig.severity === "medium";

                    return (
                      <div
                        key={`sig-card-${originalIndex}`}
                        className="saas-card p-4 sm:p-5 space-y-3 transition-all"
                      >
                        <div className="flex flex-wrap items-start justify-between gap-3">
                          <div className="space-y-1 flex-1">
                            <div className="flex items-center gap-2">
                              {/* Severity Dot & Pill */}
                              {isHigh ? (
                                <span className="px-2 py-0.5 rounded-full text-[10px] font-mono font-semibold bg-rose-500/10 text-rose-400 border border-rose-500/20 inline-flex items-center gap-1">
                                  <span className="w-1.5 h-1.5 rounded-full bg-rose-400" />
                                  HIGH SEVERITY
                                </span>
                              ) : isMedium ? (
                                <span className="px-2 py-0.5 rounded-full text-[10px] font-mono font-semibold bg-amber-500/10 text-amber-400 border border-amber-500/20 inline-flex items-center gap-1">
                                  <span className="w-1.5 h-1.5 rounded-full bg-amber-400" />
                                  MEDIUM
                                </span>
                              ) : (
                                <span className="px-2 py-0.5 rounded-full text-[10px] font-mono font-semibold bg-zinc-800 text-zinc-300 border border-white/[0.05] inline-flex items-center gap-1">
                                  <span className="w-1.5 h-1.5 rounded-full bg-zinc-400" />
                                  LOW
                                </span>
                              )}

                              {/* Source Module Tag */}
                              <span className="px-2 py-0.5 rounded-md text-[10px] font-mono text-zinc-300 bg-zinc-800/80 border border-zinc-700/80 uppercase">
                                {sig.source}
                              </span>
                            </div>

                            <h4 className="text-sm font-semibold text-[var(--text)] pt-1">
                              {sig.message}
                            </h4>
                          </div>

                          <button
                            type="button"
                            onClick={() => toggleSignal(originalIndex)}
                            className="text-xs text-[var(--text-muted)] hover:text-[var(--text)] font-medium flex items-center gap-1 cursor-pointer transition-colors shrink-0"
                          >
                            <span>{isOpen ? "Hide Evidence" : "Inspect Evidence"}</span>
                            <svg
                              className={`w-3.5 h-3.5 text-[var(--accent)] transition-transform ${isOpen ? "rotate-90" : ""}`}
                              viewBox="0 0 24 24"
                              fill="none"
                              stroke="currentColor"
                              strokeWidth="2.5"
                            >
                              <polyline points="9 18 15 12 9 6" />
                            </svg>
                          </button>
                        </div>

                        {/* Evidence Preview / Drawer */}
                        {isOpen ? (
                          <div className="p-3.5 rounded-lg bg-zinc-950/70 border border-white/[0.06] text-xs font-mono text-zinc-300 leading-relaxed whitespace-pre-wrap animate-tab-panel">
                            {sig.evidence}
                          </div>
                        ) : (
                          <p className="text-xs text-[var(--text-muted)] line-clamp-2 leading-relaxed">
                            {sig.evidence}
                          </p>
                        )}
                      </div>
                    );
                  })}
                </div>
              )}
            </div>
          )}

          {/* ─────────────────────────────────────────────────────────
              TAB 2: CITATION SCREENING
             ───────────────────────────────────────────────────────── */}
          {activeTab === "citations" && (
            <div className="space-y-4 animate-tab-panel">
              {/* Search & Filter Bar */}
              <div className="saas-card p-4 space-y-3">
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
                  <div className="flex items-center gap-1.5 text-xs">
                    {[
                      { id: "all", label: `All (${citationItems.length})` },
                      { id: "verified", label: `Verified (${verifiedCount})` },
                      { id: "notfound", label: `Unresolved (${unresolvedCount})` },
                    ].map((tab) => (
                      <button
                        key={tab.id}
                        type="button"
                        onClick={() => setCitationFilter(tab.id)}
                        className={`px-3 py-1.5 rounded-lg text-xs font-medium cursor-pointer transition-all ${
                          citationFilter === tab.id
                            ? "bg-zinc-100 text-zinc-950 font-semibold shadow-sm"
                            : "bg-zinc-800/60 text-zinc-400 hover:text-zinc-100 border border-white/[0.05]"
                        }`}
                      >
                        {tab.label}
                      </button>
                    ))}
                  </div>

                  <span className="text-[11px] font-mono text-[var(--text-faint)]">
                    Resolved against OpenAlex / Crossref
                  </span>
                </div>

                <div className="relative">
                  <input
                    type="text"
                    placeholder="Search references by title, author, or DOI..."
                    value={citationSearch}
                    onChange={(e) => setCitationSearch(e.target.value)}
                    className="w-full bg-zinc-950/60 border border-white/[0.08] rounded-lg px-3.5 py-2 pl-9 text-xs text-[var(--text)] placeholder-[var(--text-faint)] focus:border-zinc-400 transition-all font-mono"
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

              {/* Citations Ledger Table */}
              <div className="saas-card overflow-hidden">
                <div className="divide-y divide-white/[0.05]">
                  {filteredCitations.map((c, idx) => (
                    <div
                      key={`cit-row-${idx}`}
                      className="p-4 flex items-start justify-between gap-4 hover:bg-zinc-900/40 transition-colors"
                    >
                      <div className="flex items-start gap-3 flex-1 min-w-0">
                        <span className="font-mono text-xs font-semibold text-[var(--text-faint)] w-7 shrink-0 pt-0.5">
                          #{c.num}
                        </span>

                        <div className="space-y-1 min-w-0 flex-1">
                          <div className="text-xs sm:text-sm font-medium text-[var(--text)] leading-snug">
                            {c.text}
                          </div>
                          {c.note && (
                            <div className="text-[11px] font-mono text-[var(--text-faint)] truncate">
                              {c.note}
                            </div>
                          )}
                        </div>
                      </div>

                      {/* Status Pill */}
                      <span className={`px-2.5 py-0.5 rounded-full text-[11px] font-mono font-semibold border shrink-0 ${c.statusClass}`}>
                        {c.statusWord}
                      </span>
                    </div>
                  ))}
                </div>

                <div className="p-3 bg-zinc-900/50 border-t border-white/[0.05] text-[11px] font-mono text-[var(--text-faint)] text-center">
                  Displaying {filteredCitations.length} of {citationItems.length} citations
                </div>
              </div>
            </div>
          )}

          {/* ─────────────────────────────────────────────────────────
              TAB 3: PASSED STRUCTURAL CHECKS
             ───────────────────────────────────────────────────────── */}
          {activeTab === "passed" && (
            <div className="saas-card p-6 space-y-4 animate-tab-panel">
              <div className="text-xs font-semibold uppercase tracking-wider text-[var(--text-muted)] pb-2 border-b border-[var(--border-soft)] flex items-center justify-between">
                <span>Verified Clean Validations</span>
                <span className="font-mono text-emerald-400">{passedChecks.length} Passed</span>
              </div>

              <div className="space-y-2.5">
                {passedChecks.map((check, idx) => (
                  <div
                    key={`passed-${idx}`}
                    className="p-3 rounded-lg bg-emerald-500/[0.04] border border-emerald-500/10 flex items-start gap-3 text-xs text-[var(--text)]"
                  >
                    <svg className="w-4 h-4 text-emerald-400 shrink-0 mt-0.5" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
                      <polyline points="20 6 9 17 4 12" />
                    </svg>
                    <span className="leading-relaxed font-medium">{check}</span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* ─────────────────────────────────────────────────────────
              TAB 4: OVERVIEW
             ───────────────────────────────────────────────────────── */}
          {activeTab === "overview" && (
            <div className="saas-card p-6 space-y-6 animate-tab-panel">
              <div className="text-xs font-semibold uppercase tracking-wider text-[var(--text-muted)] pb-2 border-b border-[var(--border-soft)]">
                Dossier Metadata Summary
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 text-xs">
                <div className="p-3.5 rounded-lg bg-zinc-900/60 border border-white/[0.05] space-y-1">
                  <div className="text-[var(--text-faint)]">Document Title</div>
                  <div className="font-semibold text-[var(--text)] line-clamp-2">{title}</div>
                </div>

                <div className="p-3.5 rounded-lg bg-zinc-900/60 border border-white/[0.05] space-y-1">
                  <div className="text-[var(--text-faint)]">Integrity Risk Score</div>
                  <div className="font-mono text-base font-bold text-[var(--text)]">{Math.round(riskScore)} / 100 ({riskLevel})</div>
                </div>

                <div className="p-3.5 rounded-lg bg-zinc-900/60 border border-white/[0.05] space-y-1">
                  <div className="text-[var(--text-faint)]">Confidence Metric</div>
                  <div className="font-mono text-base font-bold text-zinc-200">{confPct}%</div>
                </div>

                <div className="p-3.5 rounded-lg bg-zinc-900/60 border border-white/[0.05] space-y-1">
                  <div className="text-[var(--text-faint)]">Active Forensic Modules</div>
                  <div className="font-mono text-xs font-semibold text-[var(--text)]">{modulesUsed.join(", ")}</div>
                </div>
              </div>
            </div>
          )}
        </section>
      </div>
    </div>
  );
}