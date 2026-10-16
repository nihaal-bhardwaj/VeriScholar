"use client";

import React, { useEffect, useRef, useState } from "react";
import { RiskReport, MOCK_REPORT } from "../../lib/mockData";

export interface AnalysisProgressProps {
  file: File | null;
  isMock: boolean;
  onComplete: (data: RiskReport) => void;
  onError: (message: string) => void;
}

const STAGES = [
  {
    label: "PDF Ingestion & Structural Parsing",
    detail: "Parsing text, hierarchy, sections, abstract boundaries, and reference blocks",
  },
  {
    label: "Metadata Cross-Verification",
    detail: "Cross-checking title, authors, and DOI across Crossref and OpenAlex indices",
  },
  {
    label: "Citation Graph Screening",
    detail: "Resolving reference entries, checking DOI validity, and checking for phantom citations",
  },
  {
    label: "Internal Structural Consistency",
    detail: "Auditing abstract-body cohesion, equation links, and figure/table citations",
  },
  {
    label: "Stylometric NLP Anomaly Engine",
    detail: "Scanning passive hedging index, vocabulary richness, and distribution variance",
  },
  {
    label: "Synthesizing Forensic Dossier",
    detail: "Compiling calibrated risk score and inspectable evidence dossier",
  },
];

export default function AnalysisProgress({
  file,
  isMock,
  onComplete,
  onError,
}: AnalysisProgressProps) {
  const [currentStageIdx, setCurrentStageIdx] = useState<number>(0);
  const [stageProgress, setStageProgress] = useState<number[]>(new Array(STAGES.length).fill(0));

  const onCompleteRef = useRef(onComplete);
  onCompleteRef.current = onComplete;

  const onErrorRef = useRef(onError);
  onErrorRef.current = onError;

  const paperTitle = file ? file.name.replace(/\.pdf$/i, "") : MOCK_REPORT.paper_title;

  useEffect(() => {
    let cancelled = false;

    async function run() {
      const prefersReducedMotion =
        typeof window !== "undefined" &&
        window.matchMedia("(prefers-reduced-motion: reduce)").matches;
      const stageDuration = prefersReducedMotion ? 60 : 640;

      let apiPromise: Promise<RiskReport>;
      if (file && !isMock) {
        const formData = new FormData();
        formData.append("file", file);

        const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";
        apiPromise = fetch(`${apiUrl}/analyze/full`, {
          method: "POST",
          body: formData,
        }).then(async (res) => {
          if (!res.ok) {
            const errorJson = await res.json().catch(() => null);
            throw new Error(errorJson?.detail || `Server error: ${res.status}`);
          }
          return res.json();
        });
      } else {
        apiPromise = Promise.resolve(MOCK_REPORT);
      }

      let apiResult: RiskReport | null = null;
      let apiError: any = null;

      apiPromise
        .then((res) => {
          apiResult = res;
        })
        .catch((err) => {
          apiError = err;
        });

      for (let i = 0; i < STAGES.length; i++) {
        if (cancelled) return;

        if (apiError) {
          onErrorRef.current(apiError?.message || "Failed to analyze paper.");
          return;
        }

        setCurrentStageIdx(i);
        setStageProgress((prev) => {
          const next = [...prev];
          next[i] = 100;
          return next;
        });

        await new Promise((r) => setTimeout(r, stageDuration));
        if (cancelled) return;
      }

      if (!apiResult && !apiError) {
        try {
          apiResult = await apiPromise;
        } catch (err: any) {
          apiError = err;
        }
      }

      if (cancelled) return;

      if (apiError) {
        onErrorRef.current(apiError?.message || "Failed to analyze paper.");
      } else if (apiResult) {
        await new Promise((r) => setTimeout(r, prefersReducedMotion ? 40 : 350));
        if (!cancelled) {
          onCompleteRef.current(apiResult);
        }
      }
    }

    run();

    return () => {
      cancelled = true;
    };
  }, [file, isMock]);

  return (
    <div className="w-full max-w-2xl mx-auto space-y-6 animate-tab-panel font-sans">
      {/* Header Card */}
      <div className="saas-card p-6 sm:p-8 space-y-3 relative overflow-hidden shadow-2xl">
        <div className="absolute top-0 left-1/2 -translate-x-1/2 w-48 h-20 bg-white/[0.03] blur-2xl pointer-events-none" />

        <div className="flex items-center gap-2 text-xs font-mono text-zinc-300 uppercase tracking-wider">
          <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
          Active Multi-Vector Screening
        </div>

        <h2 className="text-xl sm:text-2xl font-bold text-[var(--text)] tracking-tight line-clamp-2">
          {paperTitle}
        </h2>

        <div className="w-full bg-zinc-800 rounded-full h-1.5 overflow-hidden mt-4">
          <div
            className="h-full bg-gradient-to-r from-zinc-300 via-zinc-100 to-white transition-all duration-500 rounded-full"
            style={{ width: `${((currentStageIdx + 1) / STAGES.length) * 100}%` }}
          />
        </div>
      </div>

      {/* Stepper Cards */}
      <div className="saas-card p-6 space-y-4">
        <div className="space-y-3">
          {STAGES.map((s, idx) => {
            const isActive = idx === currentStageIdx;
            const isDone = idx < currentStageIdx;

            return (
              <div
                key={s.label}
                className={`p-3.5 rounded-xl border transition-all ${
                  isActive
                    ? "bg-zinc-800/90 border-zinc-500 shadow-md"
                    : isDone
                    ? "bg-zinc-900/40 border-white/[0.04] opacity-80"
                    : "bg-transparent border-transparent opacity-40"
                }`}
              >
                <div className="flex items-center justify-between mb-1">
                  <div className="flex items-center gap-2.5">
                    {isDone ? (
                      <span className="w-5 h-5 rounded-full bg-emerald-500/20 text-emerald-400 border border-emerald-500/30 flex items-center justify-center shrink-0">
                        <svg className="w-3 h-3 text-emerald-400" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                          <polyline points="20 6 9 17 4 12" />
                        </svg>
                      </span>
                    ) : isActive ? (
                      <span className="w-5 h-5 rounded-full bg-zinc-800 text-zinc-100 border border-zinc-600 flex items-center justify-center shrink-0">
                        <svg className="w-3 h-3 text-zinc-200 animate-spin" viewBox="0 0 24 24" fill="none">
                          <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="3" />
                          <path className="opacity-80" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                        </svg>
                      </span>
                    ) : (
                      <span className="w-5 h-5 rounded-full bg-zinc-800/80 text-zinc-500 border border-white/[0.04] flex items-center justify-center text-[10px] font-mono shrink-0">
                        {idx + 1}
                      </span>
                    )}

                    <span className={`text-xs sm:text-sm font-semibold ${
                      isActive ? "text-[var(--text)]" : isDone ? "text-[var(--text-muted)]" : "text-[var(--text-faint)]"
                    }`}>
                      {s.label}
                    </span>
                  </div>

                  <span className="text-[10px] font-mono uppercase tracking-wider text-[var(--text-faint)]">
                    {isDone ? "Done" : isActive ? "Running..." : "Pending"}
                  </span>
                </div>

                <div className="text-[11px] text-[var(--text-faint)] pl-7">
                  {s.detail}
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}
