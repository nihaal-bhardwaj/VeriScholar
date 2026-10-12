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
  const isFile =
    message.toLowerCase().includes("pdf") ||
    message.toLowerCase().includes("40mb") ||
    message.toLowerCase().includes("size") ||
    message.toLowerCase().includes("corrupt");

  let subline = "The server returned an error. Check the backend logs for details.";
  if (isNetwork) {
    subline = "Make sure the backend is running at http://localhost:8000 and try again.";
  } else if (isFile) {
    subline = message;
  }

  return (
    <div className="py-12 max-w-[600px] mx-auto text-left border-t border-b border-[var(--border-soft)]">
      <div className="text-xs font-sans uppercase tracking-wider text-[var(--danger)] mb-2">
        Analysis failed
      </div>
      <h2 className="font-serif text-2xl font-medium text-[var(--text)] mb-2">
        {message || "An unexpected error occurred during analysis"}
      </h2>
      <p className="font-sans text-sm text-[var(--text-muted)] leading-relaxed mb-6">
        {subline}
      </p>
      <div>
        <button
          type="button"
          onClick={onRetry}
          className="btn"
        >
          Try again
        </button>
      </div>
    </div>
  );
}
