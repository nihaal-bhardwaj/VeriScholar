"use client";

import React, { useState } from "react";
import Link from "next/link";
import PDFUploader from "../../components/upload/PDFUploader";
import AnalysisProgress from "../../components/progress/AnalysisProgress";
import ReportDashboard from "../../components/report/ReportDashboard";
import { uploadAndProcessPaper } from "../../lib/api";
import { CombinedAnalysisResponse } from "../../lib/api-types";

type UIState = "IDLE" | "PROCESSING" | "REPORT" | "ERROR";

export default function AnalyserPage() {
  const [uiState, setUiState] = useState<UIState>("IDLE");
  const [currentStage, setCurrentStage] = useState<string>("");
  const [reportData, setReportData] = useState<CombinedAnalysisResponse | null>(null);
  const [errorMsg, setErrorMsg] = useState<string>("");

  const handleUpload = async (file: File) => {
    setUiState("PROCESSING");
    setErrorMsg("");
    try {
      const result = await uploadAndProcessPaper(file, (stage) => {
        setCurrentStage(stage);
      });

      setReportData(result);
      setUiState("REPORT");
    } catch {
      setUiState("ERROR");
      setErrorMsg("An unexpected error occurred during analysis.");
    }
  };

  const handleReset = () => {
    setUiState("IDLE");
    setReportData(null);
    setCurrentStage("");
    setErrorMsg("");
  };

  return (
    <div className="flex min-h-screen flex-col bg-zinc-50 font-sans dark:bg-black">
      <header className="sticky top-0 z-10 w-full border-b border-zinc-200/70 bg-zinc-50/80 backdrop-blur dark:border-zinc-800/70 dark:bg-black/70">
        <div className="mx-auto flex w-full max-w-4xl items-center justify-between px-6 py-4">
          <Link href="/" className="flex items-center gap-2.5">
            <span className="flex h-8 w-8 items-center justify-center rounded-lg bg-gradient-to-br from-indigo-500 to-purple-600 text-sm font-bold text-white shadow-sm">
              V
            </span>
            <span className="text-lg font-semibold tracking-tight text-zinc-900 dark:text-zinc-50">
              VeriScholar
            </span>
          </Link>
          <nav className="flex gap-6 text-sm text-zinc-600 dark:text-zinc-400">
            <Link href="/analyser" className="text-zinc-900 dark:text-zinc-100 font-medium">Paper Analyser</Link>
            <Link href="#" className="hover:text-zinc-900 dark:hover:text-zinc-100">Review Detector</Link>
            <Link href="#" className="hover:text-zinc-900 dark:hover:text-zinc-100">Methodology</Link>
          </nav>
        </div>
      </header>

      <main className="flex flex-1 flex-col items-center p-6 sm:p-12">
        <div className="w-full max-w-4xl space-y-8">

          {uiState === "IDLE" && (
            <div className="space-y-12 py-12 animate-in fade-in zoom-in-95 duration-500">
              <div className="text-center space-y-4">
                <h1 className="text-4xl font-bold tracking-tight text-zinc-900 dark:text-zinc-50">
                  Analyse a Research Paper
                </h1>
                <p className="text-lg text-zinc-600 dark:text-zinc-400 max-w-2xl mx-auto">
                  Upload a PDF manuscript to extract its metadata, references and structure, then screen it for integrity risk signals.
                </p>
              </div>
              <PDFUploader onUpload={handleUpload} isUploading={false} />
            </div>
          )}

          {uiState === "PROCESSING" && (
            <div className="py-12">
              <AnalysisProgress currentStage={currentStage} />
            </div>
          )}

          {uiState === "REPORT" && reportData && (
            <ReportDashboard data={reportData} onReset={handleReset} />
          )}

          {uiState === "ERROR" && (
            <div className="w-full max-w-2xl mx-auto p-6 bg-red-50 dark:bg-red-900/20 rounded-2xl border border-red-200 dark:border-red-900/50 text-center space-y-4">
              <div className="inline-flex p-3 rounded-full bg-red-100 dark:bg-red-900/40 text-red-600 dark:text-red-400">
                <svg className="w-8 h-8" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
              </div>
              <h3 className="text-xl font-semibold text-red-800 dark:text-red-400">Processing Failed</h3>
              <p className="text-red-600 dark:text-red-500">{errorMsg}</p>
              <button
                onClick={handleReset}
                className="mt-4 px-4 py-2 bg-white dark:bg-zinc-800 border border-zinc-300 dark:border-zinc-700 rounded-lg text-sm font-medium shadow-sm"
              >
                Try Again
              </button>
            </div>
          )}

        </div>
      </main>

      <footer className="self-center px-6 py-6 text-xs text-zinc-400">
        Screening signals only, not proof of misconduct.
      </footer>
    </div>
  );
}
