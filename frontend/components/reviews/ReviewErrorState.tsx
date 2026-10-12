"use client";

import React from "react";

interface ReviewErrorStateProps {
  status?: number;
  errorMessage?: string;
  onTryAgain: () => void;
  onSwitchToManual: () => void;
}

export default function ReviewErrorState({
  status,
  errorMessage,
  onTryAgain,
  onSwitchToManual,
}: ReviewErrorStateProps) {
  const isScraperFailure = status === 502 || status === 504;
  const isUnsupportedSite = status === 400;

  return (
    <div
      role="alert"
      aria-live="assertive"
      className="w-full max-w-lg mx-auto p-6 sm:p-8 bg-[var(--rc-card)] border border-[var(--rc-border)] rounded-2xl shadow-md text-center font-sans space-y-6"
    >
      {/* Icon */}
      <div className="w-14 h-14 mx-auto rounded-full bg-red-50 border border-red-100 flex items-center justify-center text-[var(--rc-danger)]">
        <svg
          className="w-7 h-7"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          strokeWidth="2"
          strokeLinecap="round"
          strokeLinejoin="round"
        >
          <circle cx="12" cy="12" r="10" />
          <line x1="12" y1="8" x2="12" y2="12" />
          <line x1="12" y1="16" x2="12.01" y2="16" />
        </svg>
      </div>

      {/* Content based on error status */}
      {isScraperFailure ? (
        <div className="space-y-2">
          <h3 className="text-lg sm:text-xl font-semibold text-[var(--rc-text)] tracking-tight">
            We couldn&apos;t fetch reviews from that link.
          </h3>
          <p className="text-sm text-[var(--rc-text-muted)] leading-relaxed max-w-sm mx-auto">
            This can happen if the page structure has changed or the site is blocking automated access.
          </p>
          {errorMessage && (
            <p className="text-xs text-[var(--rc-danger)] font-mono pt-1 opacity-80">
              {errorMessage}
            </p>
          )}
        </div>
      ) : isUnsupportedSite ? (
        <div className="space-y-2">
          <h3 className="text-lg sm:text-xl font-semibold text-[var(--rc-text)] tracking-tight">
            Unsupported Product Link
          </h3>
          <p className="text-sm text-[var(--rc-text-muted)] leading-relaxed max-w-sm mx-auto">
            We currently support Amazon, Flipkart, Meesho, Ajio, and Shopsy product links.
          </p>
        </div>
      ) : (
        <div className="space-y-2">
          <h3 className="text-lg sm:text-xl font-semibold text-[var(--rc-text)] tracking-tight">
            Something went wrong.
          </h3>
          <p className="text-sm text-[var(--rc-text-muted)] leading-relaxed max-w-sm mx-auto">
            {errorMessage || "Please check your network connection and try again."}
          </p>
        </div>
      )}

      {/* Action Buttons */}
      <div className="flex flex-col sm:flex-row items-center justify-center gap-3 pt-2">
        {isScraperFailure ? (
          <>
            <button
              type="button"
              onClick={onSwitchToManual}
              className="w-full sm:w-auto px-5 py-3 bg-[var(--rc-primary)] hover:bg-[var(--rc-primary-dark)] text-white font-medium rounded-xl shadow-sm hover:shadow-md transition-all text-sm cursor-pointer focus-visible:ring-2 focus-visible:ring-[var(--rc-primary)]"
            >
              Paste reviews manually instead
            </button>
            <button
              type="button"
              onClick={onTryAgain}
              className="w-full sm:w-auto px-4 py-3 bg-white hover:bg-gray-50 text-[var(--rc-text)] border border-[var(--rc-border)] font-medium rounded-xl transition-all text-sm cursor-pointer"
            >
              Try link again
            </button>
          </>
        ) : isUnsupportedSite ? (
          <button
            type="button"
            onClick={onTryAgain}
            className="w-full sm:w-auto px-6 py-3 bg-[var(--rc-primary)] hover:bg-[var(--rc-primary-dark)] text-white font-medium rounded-xl shadow-sm hover:shadow-md transition-all text-sm cursor-pointer focus-visible:ring-2 focus-visible:ring-[var(--rc-primary)]"
          >
            Try a different link
          </button>
        ) : (
          <button
            type="button"
            onClick={onTryAgain}
            className="w-full sm:w-auto px-6 py-3 bg-[var(--rc-primary)] hover:bg-[var(--rc-primary-dark)] text-white font-medium rounded-xl shadow-sm hover:shadow-md transition-all text-sm cursor-pointer focus-visible:ring-2 focus-visible:ring-[var(--rc-primary)]"
          >
            Try again
          </button>
        )}
      </div>
    </div>
  );
}
