"use client";

import React from "react";

interface ReviewErrorStateProps {
  status?: number;
  message?: string;
  errorMessage?: string;
  onRetry?: () => void;
  onTryAgain?: () => void;
  onManualFallback?: () => void;
  onSwitchToManual?: () => void;
}

export default function ReviewErrorState({
  status,
  message,
  errorMessage,
  onRetry,
  onTryAgain,
  onManualFallback,
  onSwitchToManual,
}: ReviewErrorStateProps) {
  const displayMsg = message || errorMessage;
  const handleRetry = onRetry || onTryAgain || (() => {});
  const handleManual = onManualFallback || onSwitchToManual || (() => {});

  const isScraperFailure = status === 502 || status === 504;
  const isUnsupportedSite = status === 400;

  return (
    <div
      role="alert"
      aria-live="assertive"
      className="saas-card p-8 sm:p-10 text-center font-sans space-y-6 max-w-lg mx-auto shadow-2xl"
    >
      {/* Icon */}
      <div className="w-14 h-14 mx-auto rounded-full bg-rose-500/10 border border-rose-500/20 flex items-center justify-center text-rose-400">
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
          <h3 className="text-xl font-bold text-[var(--text)] tracking-tight">
            Unable to fetch reviews from this link
          </h3>
          <p className="text-sm text-[var(--text-muted)] leading-relaxed max-w-sm mx-auto">
            The target site may have updated its layout or has active bot protection. You can paste reviews manually to continue.
          </p>
          {displayMsg && (
            <p className="text-xs text-rose-400/80 font-mono pt-1">
              {displayMsg}
            </p>
          )}
        </div>
      ) : isUnsupportedSite ? (
        <div className="space-y-2">
          <h3 className="text-xl font-bold text-[var(--text)] tracking-tight">
            Unsupported Product Link
          </h3>
          <p className="text-sm text-[var(--text-muted)] leading-relaxed max-w-sm mx-auto">
            We currently support Amazon, Flipkart, Meesho, Ajio, and Shopsy product links.
          </p>
        </div>
      ) : (
        <div className="space-y-2">
          <h3 className="text-xl font-bold text-[var(--text)] tracking-tight">
            Inspection Could Not Complete
          </h3>
          <p className="text-sm text-[var(--text-muted)] leading-relaxed max-w-sm mx-auto">
            {displayMsg || "Please check your network connection and try again."}
          </p>
        </div>
      )}

      {/* Action Buttons */}
      <div className="flex flex-col sm:flex-row items-center justify-center gap-3 pt-2">
        {isScraperFailure ? (
          <>
            <button
              type="button"
              onClick={handleManual}
              className="btn-primary w-full sm:w-auto text-xs sm:text-sm py-2.5 px-5 cursor-pointer"
            >
              Paste reviews manually instead
            </button>
            <button
              type="button"
              onClick={handleRetry}
              className="btn-secondary w-full sm:w-auto text-xs sm:text-sm py-2.5 px-4 cursor-pointer"
            >
              Try again
            </button>
          </>
        ) : (
          <button
            type="button"
            onClick={handleRetry}
            className="btn-primary w-full sm:w-auto text-xs sm:text-sm py-2.5 px-6 cursor-pointer"
          >
            Try Again
          </button>
        )}
      </div>
    </div>
  );
}
