"use client";

import React, { useState } from "react";

interface ReviewUrlFormProps {
  onSubmit: (url: string) => void;
  disabled?: boolean;
}

export default function ReviewUrlForm({ onSubmit, disabled }: ReviewUrlFormProps) {
  const [url, setUrl] = useState("");
  const [error, setError] = useState<string | null>(null);

  const validateUrl = (value: string): string | null => {
    const trimmed = value.trim();
    if (!trimmed) {
      return "Please enter a product URL.";
    }

    let parsed: URL;
    try {
      parsed = new URL(trimmed);
    } catch {
      return "Please enter a valid web address (including https://).";
    }

    const host = parsed.hostname.toLowerCase();
    const supported = [
      "amazon.",
      "flipkart.com",
      "meesho.com",
      "ajio.com",
      "shopsy.in",
    ];
    if (!supported.some((dom) => host.includes(dom))) {
      return "We currently support Amazon, Flipkart, Meesho, Ajio, and Shopsy product links.";
    }

    return null;
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    const validationError = validateUrl(url);
    if (validationError) {
      setError(validationError);
      return;
    }
    setError(null);
    onSubmit(url.trim());
  };

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setUrl(e.target.value);
    if (error) {
      setError(null);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="w-full space-y-4 font-sans" noValidate>
      <div className="space-y-2">
        <label
          htmlFor="product-url-input"
          className="text-xs font-semibold uppercase tracking-wider text-[var(--text-muted)] flex items-center justify-between"
        >
          <span>E-Commerce Product URL</span>
          <span className="text-[11px] font-mono text-[var(--text-faint)] lowercase">
            https:// supported
          </span>
        </label>

        {/* Modern SaaS Input Bar with Sheen & Focus Ring */}
        <div className="relative flex flex-col sm:flex-row items-stretch sm:items-center gap-2 p-1.5 bg-zinc-900/90 border border-white/[0.1] rounded-xl shadow-lg focus-within:border-zinc-400 focus-within:ring-2 focus-within:ring-zinc-400/20 transition-all">
          <div className="flex items-center flex-1 px-3 gap-2.5">
            <svg
              className="w-5 h-5 text-[var(--text-faint)] shrink-0"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="2"
            >
              <circle cx="11" cy="11" r="8" />
              <line x1="21" y1="21" x2="16.65" y2="16.65" />
            </svg>
            <input
              id="product-url-input"
              type="url"
              value={url}
              onChange={handleChange}
              placeholder="Paste Amazon or Flipkart product link..."
              disabled={disabled}
              aria-invalid={!!error}
              aria-describedby={error ? "url-error-msg" : "url-helper-msg"}
              className="w-full bg-transparent text-[var(--text)] placeholder-[var(--text-faint)] text-sm focus:outline-none disabled:opacity-60 py-2"
            />
          </div>

          <button
            type="submit"
            disabled={disabled}
            className="btn-primary py-2.5 px-5 text-xs sm:text-sm shrink-0 cursor-pointer disabled:opacity-50 disabled:cursor-not-allowed font-medium rounded-lg"
          >
            <span>Scan Product</span>
            <svg
              className="w-4 h-4"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="2.2"
              strokeLinecap="round"
              strokeLinejoin="round"
            >
              <line x1="5" y1="12" x2="19" y2="12" />
              <polyline points="12 5 19 12 12 19" />
            </svg>
          </button>
        </div>
      </div>

      {/* Validation Message */}
      {error ? (
        <p
          id="url-error-msg"
          role="alert"
          className="text-xs font-medium text-rose-400 flex items-center gap-1.5 pt-0.5"
        >
          <svg className="w-4 h-4 shrink-0" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <circle cx="12" cy="12" r="10" />
            <line x1="12" y1="8" x2="12" y2="12" />
            <line x1="12" y1="16" x2="12.01" y2="16" />
          </svg>
          <span>{error}</span>
        </p>
      ) : (
        <div className="text-xs text-[var(--text-faint)]">
          <span>Supported: Amazon, Flipkart, Meesho, Ajio, Shopsy</span>
        </div>
      )}
    </form>
  );
}
