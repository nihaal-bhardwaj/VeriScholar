"use client";

import React from "react";

interface AnalysisErrorProps {
  message: string;
  onRetry: () => void;
}

export default function AnalysisError({ message, onRetry }: AnalysisErrorProps) {
  const isNetwork =
    message.toLowerCase().includes("network") ||
    message.toLowerCase().includes("failed to fetch") ||
    message.toLowerCase().includes("connect");

  let subline = "The server returned an error during processing. Check backend logs for details.";
  if (isNetwork) {
    subline = "Verify that the backend service is running at http://localhost:8000 and try again.";
  }

  return (
    <div className="saas-card p-8 sm:p-10 max-w-xl mx-auto text-center space-y-6 shadow-2xl font-sans">
      <div className="w-14 h-14 mx-auto rounded-full bg-rose-500/10 border border-rose-500/20 flex items-center justify-center text-rose-400">
        <svg className="w-7 h-7" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
          <circle cx="12" cy="12" r="10" />
          <line x1="12" y1="8" x2="12" y2="12" />
          <line x1="12" y1="16" x2="12.01" y2="16" />
        </svg>
      </div>

      <div className="space-y-2">
        <div className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-[11px] font-mono text-rose-400 bg-rose-500/10 border border-rose-500/20">
          Analysis Pipeline Fault
        </div>

        <h2 className="text-xl font-bold text-[var(--text)] tracking-tight">
          {message || "Manuscript Analysis Failed"}
        </h2>

        <p className="text-xs sm:text-sm text-[var(--text-muted)] leading-relaxed max-w-md mx-auto">
          {subline}
        </p>
      </div>

      <div>
        <button
          type="button"
          onClick={onRetry}
          className="btn-primary py-2.5 px-6 text-xs sm:text-sm cursor-pointer"
        >
          Try Again
        </button>
      </div>
    </div>
  );
}
