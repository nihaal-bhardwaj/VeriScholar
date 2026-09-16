"use client";

import React from "react";
import { CombinedAnalysisResponse } from "../../lib/api-types";

interface ReportDashboardProps {
  data: CombinedAnalysisResponse;
  onReset: () => void;
}

const MODULE_DESCRIPTIONS = [
  {
    name: "Metadata Analysis",
    key: "metadata_analysis" as const,
    description: "Verifies the paper's title, authors and DOI against Crossref.",
  },
  {
    name: "Citation Checks",
    key: "citation_analysis" as const,
    description: "Verifies each reference against scholarly databases.",
  },
  {
    name: "ML Risk Assessment",
    key: "ml_analysis" as const,
    description: "Scores the paper with a trained risk model.",
  },
];

export default function ReportDashboard({ data, onReset }: ReportDashboardProps) {
  const shortId = data.analysis_id ? data.analysis_id.slice(0, 8) : "";

  return (
    <div className="w-full max-w-4xl mx-auto space-y-8 animate-in fade-in slide-in-from-bottom-4 duration-700 pb-20">

      {/* Header section with disclaimer */}
      <div className="bg-amber-50 dark:bg-amber-950/30 border border-amber-200 dark:border-amber-900/50 rounded-2xl p-6 shadow-sm">
        <div className="flex items-start space-x-4">
          <svg className="w-6 h-6 text-amber-600 dark:text-amber-500 shrink-0 mt-1" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
          </svg>
          <div>
            <h3 className="text-lg font-semibold text-amber-900 dark:text-amber-400">Important Notice</h3>
            <p className="mt-1 text-sm text-amber-800 dark:text-amber-500 leading-relaxed">
              This analysis highlights signals that may require human review. It does not prove research misconduct.
              The system uses pattern matching and metadata verification as screening indicators only.
            </p>
          </div>
        </div>
      </div>

      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <h2 className="text-3xl font-semibold tracking-tight text-zinc-900 dark:text-zinc-50">
            Analysis Report
          </h2>
          {shortId && (
            <p className="mt-1 text-sm text-zinc-500 dark:text-zinc-500">
              Analysis ID: <code className="font-mono text-xs">{shortId}…</code>
            </p>
          )}
        </div>
        <button
          onClick={onReset}
          className="px-4 py-2 text-sm font-medium text-zinc-700 bg-white border border-zinc-300 rounded-lg shadow-sm hover:bg-zinc-50 dark:bg-zinc-800 dark:text-zinc-300 dark:border-zinc-700 dark:hover:bg-zinc-700 transition-colors"
        >
          Analyse Another Paper
        </button>
      </div>

      {/* FINAL SCORE CARD */}
      <div className="bg-white dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-800 rounded-2xl p-6 shadow-sm flex items-center justify-between">
        <div>
          <h3 className="text-lg font-semibold text-zinc-900 dark:text-zinc-100">Overall Integrity Risk Score</h3>
          <p className="mt-1 text-sm text-zinc-500 dark:text-zinc-400">
            Based on {data.final_assessment.confidence ? Math.round(data.final_assessment.confidence * 100) : 0}% confidence evaluation across available modules.
          </p>
        </div>
        <div className="text-right">
          <span className={`text-4xl font-bold ${data.final_assessment.risk_level === 'high' ? 'text-red-500' : data.final_assessment.risk_level === 'moderate' ? 'text-amber-500' : 'text-emerald-500'}`}>
            {data.final_assessment.risk_score?.toFixed(1) || "0.0"}
          </span>
          <span className="block text-sm font-medium text-zinc-500 uppercase mt-1">
            {data.final_assessment.risk_level || "Unknown"} RISK
          </span>
        </div>
      </div>

      {/* Main Signals from Modules */}
      {data.ml_analysis.signals && data.ml_analysis.signals.length > 0 && (
        <div className="bg-red-50/50 dark:bg-red-900/10 border border-red-100 dark:border-red-900/30 rounded-2xl p-6 shadow-sm">
          <h3 className="text-lg font-semibold text-red-900 dark:text-red-400 mb-4">Integrity Flags Detected</h3>
          <ul className="space-y-2 list-disc list-inside text-sm text-red-800 dark:text-red-300">
            {data.ml_analysis.signals.map((signal, idx) => (
              <li key={idx} className="leading-relaxed">{signal}</li>
            ))}
          </ul>
        </div>
      )}

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">

        {/* Paper Information */}
        <div className="bg-white dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-800 rounded-2xl p-6 shadow-sm">
          <h3 className="text-lg font-semibold text-zinc-900 dark:text-zinc-100 mb-4">Document Details</h3>
          <dl className="space-y-4 text-sm">
            <div>
              <dt className="text-zinc-500 dark:text-zinc-400">Filename</dt>
              <dd className="font-medium text-zinc-900 dark:text-zinc-200 truncate">{data.paper.filename}</dd>
            </div>
            <div>
              <dt className="text-zinc-500 dark:text-zinc-400">Title</dt>
              <dd className="font-medium text-zinc-900 dark:text-zinc-200">{data.paper.title || "Not detected"}</dd>
            </div>
            <div>
              <dt className="text-zinc-500 dark:text-zinc-400">Authors</dt>
              <dd className="font-medium text-zinc-900 dark:text-zinc-200">
                {data.paper.authors && data.paper.authors.length > 0
                  ? data.paper.authors.join(", ")
                  : "Not detected"}
              </dd>
            </div>
            <div>
              <dt className="text-zinc-500 dark:text-zinc-400">DOI</dt>
              <dd className="font-medium text-zinc-900 dark:text-zinc-200">{data.paper.doi || "Not found"}</dd>
            </div>
            <div>
              <dt className="text-zinc-500 dark:text-zinc-400">Pages Extracted</dt>
              <dd className="font-medium text-zinc-900 dark:text-zinc-200">{data.paper.page_count}</dd>
            </div>
          </dl>
        </div>

        {/* Status Overview */}
        <div className="bg-white dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-800 rounded-2xl p-6 shadow-sm">
          <h3 className="text-lg font-semibold text-zinc-900 dark:text-zinc-100 mb-4">Module Status</h3>
          <ul className="space-y-4 text-sm">
            {MODULE_DESCRIPTIONS.map((module) => (
              <li key={module.key}>
                <div className="flex items-center justify-between">
                  <span className="text-zinc-600 dark:text-zinc-400">{module.name}</span>
                  <StatusBadge status={data[module.key].status} />
                </div>
                <p className="mt-1 text-xs text-zinc-400 dark:text-zinc-500">
                  {module.description}
                </p>
              </li>
            ))}
          </ul>
        </div>
      </div>

      {/* Abstract preview */}
      <div className="bg-white dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-800 rounded-2xl p-6 shadow-sm">
        <h3 className="text-lg font-semibold text-zinc-900 dark:text-zinc-100 mb-4">Abstract</h3>
        <p className="text-sm text-zinc-600 dark:text-zinc-400 leading-relaxed">
          {data.paper.abstract || "No abstract detected."}
        </p>
      </div>

      {/* Extracted References */}
      <div className="bg-white dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-800 rounded-2xl p-6 shadow-sm">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-semibold text-zinc-900 dark:text-zinc-100">Extracted References</h3>
          <span className="px-3 py-1 bg-zinc-100 dark:bg-zinc-800 text-zinc-600 dark:text-zinc-400 text-xs font-medium rounded-full">
            {data.paper.references.length} found
          </span>
        </div>
        <div className="max-h-96 overflow-y-auto pr-2 space-y-3">
          {data.paper.references.length > 0 ? (
            data.paper.references.map((ref, i) => (
              <div key={i} className="p-3 bg-zinc-50 dark:bg-zinc-800/50 rounded-lg text-sm border border-zinc-100 dark:border-zinc-800">
                <span className="font-semibold text-zinc-700 dark:text-zinc-300 mr-2">[{ref.number || i + 1}]</span>
                <span className="text-zinc-600 dark:text-zinc-400">{ref.raw_text}</span>
                {ref.doi && (
                  <div className="mt-2 flex items-center text-xs text-blue-600 dark:text-blue-400">
                    <svg className="w-4 h-4 mr-1" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M13.828 10.172a4 4 0 00-5.656 0l-4 4a4 4 0 105.656 5.656l1.102-1.101m-.758-4.899a4 4 0 005.656 0l4-4a4 4 0 00-5.656-5.656l-1.1 1.1" />
                    </svg>
                    {ref.doi}
                  </div>
                )}
              </div>
            ))
          ) : (
            <p className="text-sm text-zinc-500">No structured references extracted.</p>
          )}
        </div>
      </div>

    </div>
  );
}

function StatusBadge({ status }: { status: string }) {
  if (status === "completed") {
    return (
      <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-medium bg-emerald-100 text-emerald-800 dark:bg-emerald-900/30 dark:text-emerald-400">
        <span className="h-1.5 w-1.5 rounded-full bg-emerald-500" />
        Completed
      </span>
    );
  }
  if (status === "pending") {
    return (
      <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-medium bg-zinc-100 text-zinc-800 dark:bg-zinc-800 dark:text-zinc-400">
        <span className="h-1.5 w-1.5 rounded-full bg-zinc-400" />
        Pending
      </span>
    );
  }
  return (
    <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-medium bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-400">
      <span className="h-1.5 w-1.5 rounded-full bg-red-500" />
      Error
    </span>
  );
}