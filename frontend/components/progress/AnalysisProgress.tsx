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
    label: "PDF extraction",
    detail: "Parsing text, layout, and structural elements",
  },
  {
    label: "Metadata verification",
    detail: "Cross-checking title, authors, and DOI against Crossref and OpenAlex",
  },
  {
    label: "Citation verification",
    detail: "Resolving reference entries against public indexes",
  },
  {
    label: "Internal consistency",
    detail: "Comparing abstract, body, and figures for coherence",
  },
  {
    label: "ML / NLP analysis",
    detail: "Scanning for unusual text and statistical patterns",
  },
  {
    label: "Generating report",
    detail: "Compiling screening signals into a unified report",
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
  const onErrorRef = useRef(onError);

  useEffect(() => {
    onCompleteRef.current = onComplete;
    onErrorRef.current = onError;
  }, [onComplete, onError]);

  const paperTitle = file ? file.name.replace(/\.pdf$/i, "") : MOCK_REPORT.paper_title;

  useEffect(() => {
    let cancelled = false;

    async function run() {
      const prefersReducedMotion =
        typeof window !== "undefined" &&
        window.matchMedia("(prefers-reduced-motion: reduce)").matches;
      const stageDuration = prefersReducedMotion ? 60 : 640;

      // Start API promise concurrently
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
      let apiError: unknown = null;

      apiPromise
        .then((res) => {
          apiResult = res;
        })
        .catch((err) => {
          apiError = err;
        });

      // Animate stages 0 through 5
      for (let i = 0; i < STAGES.length; i++) {
        if (cancelled) return;
        if (apiError) {
          onErrorRef.current(
            apiError instanceof Error ? apiError.message : "Failed to analyze paper."
          );
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

      // If animation completed but API is still processing, wait for it
      if (!apiResult && !apiError) {
        try {
          apiResult = await apiPromise;
        } catch (err: unknown) {
          apiError = err;
        }
      }

      if (cancelled) return;

      if (apiError) {
        onErrorRef.current(
          apiError instanceof Error ? apiError.message : "Failed to analyze paper."
        );
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
    <div className="w-full max-w-[740px] mx-auto py-8">
      <div className="mb-8">
        <span className="text-xs uppercase tracking-widest text-[var(--text-faint)] font-sans block mb-2">
          Analyzing
        </span>
        <h2 className="font-serif italic text-[22px] text-[var(--text)] font-normal leading-snug">
          {paperTitle}
        </h2>
      </div>

      <div className="border-t border-[var(--border-soft)]">
        {STAGES.map((s, idx) => {
          const isActive = idx === currentStageIdx;
          const isDone = idx < currentStageIdx;

          let stateWord = "";
          if (isDone) stateWord = "done";
          else if (isActive) stateWord = "in progress";

          return (
            <div
              key={s.label}
              className="py-4 border-b border-[var(--border-soft)] transition-colors"
            >
              <div className="flex justify-between items-baseline mb-1">
                <span
                  className={
                    isActive
                      ? "font-serif italic text-lg text-[var(--text)]"
                      : isDone
                      ? "font-sans text-sm text-[var(--text)]"
                      : "font-sans text-sm text-[var(--text-muted)]"
                  }
                >
                  {s.label}
                </span>
                <span className="font-serif italic text-xs text-[var(--text-muted)]">
                  {stateWord}
                </span>
              </div>
              <div className="text-xs text-[var(--text-faint)] font-sans mb-2.5">
                {s.detail}
              </div>
              <div className="w-full h-[1px] bg-[var(--border)] overflow-hidden">
                <div
                  className="h-full bg-[var(--accent)] transition-all duration-[640ms] ease-linear"
                  style={{
                    width: isDone ? "100%" : isActive ? `${stageProgress[idx]}%` : "0%",
                  }}
                />
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
