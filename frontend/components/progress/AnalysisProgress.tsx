"use client";

import React from "react";

interface AnalysisProgressProps {
  currentStage: string;
}

export default function AnalysisProgress({ currentStage }: AnalysisProgressProps) {
  const stages = [
    "Uploading PDF...",
    "Extracting text and references...",
    "Generating report...",
  ];

  const currentIndex = stages.indexOf(currentStage);

  return (
    <div className="w-full max-w-2xl mx-auto bg-white dark:bg-zinc-900 rounded-3xl shadow-sm border border-zinc-200 dark:border-zinc-800 p-8 space-y-8 animate-in fade-in slide-in-from-bottom-4 duration-500">
      <div className="text-center space-y-2">
        <h2 className="text-2xl font-semibold tracking-tight text-zinc-900 dark:text-zinc-50">
          Analysing Paper
        </h2>
        <p className="text-zinc-500 dark:text-zinc-400">
          Please wait while we process your document...
        </p>
      </div>

      <div className="space-y-6">
        {stages.map((stage, index) => {
          const isCompleted = currentIndex > index;
          const isCurrent = currentIndex === index;
          const isPending = currentIndex < index;

          return (
            <div key={stage} className="flex items-center space-x-4">
              <div className="flex-shrink-0 flex items-center justify-center w-8 h-8 rounded-full border-2 transition-colors duration-300">
                {isCompleted && (
                  <div className="w-8 h-8 rounded-full bg-emerald-500 border-emerald-500 flex items-center justify-center text-white">
                    <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M5 13l4 4L19 7" />
                    </svg>
                  </div>
                )}
                {isCurrent && (
                  <div className="w-8 h-8 rounded-full border-blue-500 border-t-transparent animate-spin" />
                )}
                {isPending && (
                  <div className="w-8 h-8 rounded-full border-zinc-200 dark:border-zinc-700 bg-zinc-50 dark:bg-zinc-800" />
                )}
              </div>
              <span
                className={`text-sm font-medium transition-colors duration-300 ${
                  isCompleted
                    ? "text-zinc-900 dark:text-zinc-300"
                    : isCurrent
                    ? "text-blue-600 dark:text-blue-400"
                    : "text-zinc-400 dark:text-zinc-600"
                }`}
              >
                {stage}
              </span>
            </div>
          );
        })}
      </div>
    </div>
  );
}
