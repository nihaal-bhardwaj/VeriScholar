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
      return "We currently only support Amazon, Flipkart, Meesho, Ajio, and Shopsy product links.";
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
    <form onSubmit={handleSubmit} className="w-full space-y-3 font-sans" noValidate>
      <div>
        <label
          htmlFor="product-url-input"
          className="block text-sm font-medium text-[var(--rc-text)] mb-1.5"
        >
          Product Page Link
        </label>
        <div className="flex flex-col sm:flex-row gap-3">
          <input
            id="product-url-input"
            type="url"
            value={url}
            onChange={handleChange}
            placeholder="https://www.amazon.in/product-name/dp/..."
            disabled={disabled}
            aria-invalid={!!error}
            aria-describedby={error ? "url-error-msg" : "url-helper-msg"}
            className="flex-1 px-4 py-3.5 bg-[var(--rc-card)] text-[var(--rc-text)] placeholder-[var(--rc-text-muted)] border border-[var(--rc-border)] rounded-xl shadow-xs focus:outline-none focus:ring-2 focus:ring-[var(--rc-primary)] focus:border-[var(--rc-primary)] transition-all text-sm sm:text-base disabled:opacity-60"
          />
          <button
            type="submit"
            disabled={disabled}
            className="px-6 py-3.5 bg-[var(--rc-primary)] hover:bg-[var(--rc-primary-dark)] text-white font-medium rounded-xl shadow-md hover:shadow-lg transition-all flex items-center justify-center gap-2 text-sm sm:text-base cursor-pointer disabled:opacity-60 disabled:cursor-not-allowed shrink-0 focus-visible:ring-2 focus-visible:ring-[var(--rc-primary)] focus-visible:ring-offset-2"
          >
            <span>Analyze Reviews</span>
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

      {error ? (
        <p
          id="url-error-msg"
          role="alert"
          className="text-xs sm:text-sm font-medium text-[var(--rc-danger)] flex items-center gap-1.5 pt-0.5"
        >
          <svg
            className="w-4 h-4 shrink-0"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
          >
            <circle cx="12" cy="12" r="10" />
            <line x1="12" y1="8" x2="12" y2="12" />
            <line x1="12" y1="16" x2="12.01" y2="16" />
          </svg>
          <span>{error}</span>
        </p>
      ) : (
        <p
          id="url-helper-msg"
          className="text-xs sm:text-sm text-[var(--rc-text-muted)]"
        >
          Works with Amazon, Flipkart, Meesho, Ajio, and Shopsy product pages.
        </p>
      )}
    </form>
  );
}
