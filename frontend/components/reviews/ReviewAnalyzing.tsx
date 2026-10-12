"use client";

import React, { useEffect, useState } from "react";

const STATUS_MESSAGES = [
  "Fetching reviews...",
  "Checking writing patterns...",
  "Comparing reviews to each other...",
  "Calculating trust score...",
];

export default function ReviewAnalyzing() {
  const [index, setIndex] = useState(0);

  useEffect(() => {
    const timer = setInterval(() => {
      setIndex((prev) => (prev + 1) % STATUS_MESSAGES.length);
    }, 1500);
    return () => clearInterval(timer);
  }, []);

  return (
    <div
      role="status"
      aria-live="polite"
      className="w-full max-w-md mx-auto p-8 sm:p-10 bg-[var(--rc-card)] border border-[var(--rc-border)] rounded-2xl shadow-md text-center font-sans space-y-6"
    >
      {/* Animated Pulsing & Spinning Container */}
      <div className="relative w-20 h-20 mx-auto flex items-center justify-center">
        {/* Pulsing halo */}
        <div className="absolute inset-0 rounded-full bg-[var(--rc-primary)] opacity-20 animate-ping" />

        {/* Spinning gradient ring */}
        <div
          className="w-16 h-16 rounded-full border-4 border-[var(--rc-border)] border-t-[var(--rc-primary)] border-r-[var(--rc-primary)] animate-spin"
          aria-hidden="true"
        />

        {/* Center icon */}
        <div className="absolute inset-0 flex items-center justify-center text-[var(--rc-primary)]">
          <svg
            className="w-7 h-7"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
            strokeLinecap="round"
            strokeLinejoin="round"
          >
            <path d="M12 2v4M12 18v4M4.93 4.93l2.83 2.83M16.24 16.24l2.83 2.83M2 12h4M18 12h4M4.93 19.07l2.83-2.83M16.24 7.76l2.83-2.83" />
          </svg>
        </div>
      </div>

      <div className="space-y-2">
        <h3 className="text-lg sm:text-xl font-semibold text-[var(--rc-text)] tracking-tight">
          Analyzing Product Reviews
        </h3>
        <p className="text-sm sm:text-base font-medium text-[var(--rc-primary)] min-h-[24px] transition-all duration-300">
          {STATUS_MESSAGES[index]}
        </p>
        <p className="text-xs text-[var(--rc-text-muted)] pt-2">
          Evaluating sentiment consistency, repetition, and automated writing signatures.
        </p>
      </div>
    </div>
  );
}
