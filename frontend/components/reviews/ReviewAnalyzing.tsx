"use client";

import React, { useEffect, useState } from "react";

const STEPS = [
  { label: "Connecting to e-commerce endpoint...", phase: "Network Ingestion" },
  { label: "Extracting reviewer verified status & ratings...", phase: "Metadata Parsing" },
  { label: "Running common-sense & category incoherence checks...", phase: "Gemini 3.1+ LLM Analysis" },
  { label: "Evaluating phrase repetition & astroturfing bursts...", phase: "Forensic Heuristics" },
  { label: "Synthesizing composite trust index & suspicion score...", phase: "Final Report Aggregation" },
];

export default function ReviewAnalyzing({ mode = "url" }: { mode?: string }) {
  const [currentStep, setCurrentStep] = useState(0);

  useEffect(() => {
    const timer = setInterval(() => {
      setCurrentStep((prev) => (prev < STEPS.length - 1 ? prev + 1 : prev));
    }, 1200);
    return () => clearInterval(timer);
  }, []);

  return (
    <div
      role="status"
      aria-live="polite"
      className="saas-card p-8 sm:p-10 text-center font-sans space-y-6 relative overflow-hidden shadow-2xl"
    >
      {/* Background ambient illumination */}
      <div className="absolute top-0 left-1/2 -translate-x-1/2 w-48 h-20 bg-white/[0.03] blur-2xl pointer-events-none" />

      {/* Modern Radar / Radar Ping Icon */}
      <div className="relative w-20 h-20 mx-auto flex items-center justify-center">
        <div className="absolute inset-0 rounded-full bg-white/[0.03] animate-ping" />
        <div className="w-16 h-16 rounded-full border-2 border-zinc-700 border-t-zinc-200 border-r-zinc-400 animate-spin" />
        <div className="absolute inset-0 flex items-center justify-center text-zinc-200">
          <svg className="w-7 h-7" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <path d="M12 2v4M12 18v4M4.93 4.93l2.83 2.83M16.24 16.24l2.83 2.83M2 12h4M18 12h4M4.93 19.07l2.83-2.83M16.24 7.76l2.83-2.83" />
          </svg>
        </div>
      </div>

      <div className="space-y-3">
        <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-zinc-800 border border-zinc-700 text-xs font-mono text-zinc-300">
          <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
          {STEPS[currentStep].phase}
        </div>

        <h3 className="text-xl font-bold tracking-tight text-[var(--text)]">
          Auditing Review Authenticity
        </h3>

        <p className="text-sm text-[var(--text-muted)] min-h-[22px] font-medium transition-all">
          {STEPS[currentStep].label}
        </p>
      </div>

      {/* Telemetry Stepper Track */}
      <div className="space-y-2 pt-2 border-t border-[var(--border-soft)]">
        <div className="w-full bg-zinc-800 rounded-full h-1.5 overflow-hidden">
          <div
            className="h-full bg-gradient-to-r from-zinc-300 via-zinc-200 to-white transition-all duration-500 rounded-full"
            style={{ width: `${((currentStep + 1) / STEPS.length) * 100}%` }}
          />
        </div>
        <div className="flex justify-between text-[11px] font-mono text-[var(--text-faint)]">
          <span>Step {currentStep + 1} of {STEPS.length}</span>
          <span>{Math.round(((currentStep + 1) / STEPS.length) * 100)}% Complete</span>
        </div>
      </div>
    </div>
  );
}
