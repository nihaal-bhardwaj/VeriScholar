"use client";

import React, { useState, useRef, useCallback } from "react";

interface PDFUploaderProps {
  onUpload: (file: File) => void;
  isUploading: boolean;
}

const MAX_FILE_SIZE = 10 * 1024 * 1024; // 10MB

export default function PDFUploader({ onUpload, isUploading }: PDFUploaderProps) {
  const [isDragActive, setIsDragActive] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleDragEnter = useCallback((e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragActive(true);
  }, []);

  const handleDragLeave = useCallback((e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragActive(false);
  }, []);

  const handleDragOver = useCallback((e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    e.stopPropagation();
  }, []);

  const validateAndProcessFile = useCallback((file: File) => {
    setError(null);
    if (file.type !== "application/pdf") {
      setError("Please upload a valid PDF file.");
      return;
    }
    if (file.size > MAX_FILE_SIZE) {
      setError("File exceeds the maximum limit of 10MB.");
      return;
    }
    onUpload(file);
  }, [onUpload]);

  const handleDrop = useCallback(
    (e: React.DragEvent<HTMLDivElement>) => {
      e.preventDefault();
      e.stopPropagation();
      setIsDragActive(false);

      if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
        validateAndProcessFile(e.dataTransfer.files[0]);
        e.dataTransfer.clearData();
      }
    },
    [validateAndProcessFile]
  );

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      validateAndProcessFile(e.target.files[0]);
    }
  };

  const openFileDialog = () => {
    if (fileInputRef.current) {
      fileInputRef.current.click();
    }
  };

  return (
    <div className="flex flex-col items-center justify-center w-full max-w-2xl mx-auto space-y-4">
      <div
        className={`relative flex flex-col items-center justify-center w-full h-64 p-6 border-2 border-dashed rounded-3xl transition-all duration-300 ease-in-out cursor-pointer group shadow-sm overflow-hidden ${
          isDragActive
            ? "border-zinc-400 bg-zinc-100/50 dark:bg-zinc-800/40"
            : "border-zinc-300 bg-white dark:border-zinc-700 dark:bg-zinc-900/50 hover:bg-zinc-50 dark:hover:bg-zinc-800/50"
        } ${isUploading ? "opacity-50 pointer-events-none" : ""}`}
        onDragEnter={handleDragEnter}
        onDragLeave={handleDragLeave}
        onDragOver={handleDragOver}
        onDrop={handleDrop}
        onClick={openFileDialog}
        role="button"
        tabIndex={0}
        onKeyDown={(e) => {
          if (e.key === "Enter" || e.key === " ") {
            openFileDialog();
          }
        }}
        aria-label="Upload PDF file"
      >
        <div className="absolute inset-0 bg-white/[0.03] opacity-0 group-hover:opacity-100 transition-opacity duration-500" />
        
        <input
          type="file"
          accept="application/pdf"
          className="hidden"
          ref={fileInputRef}
          onChange={handleFileChange}
          disabled={isUploading}
        />
        <div className="flex flex-col items-center z-10 space-y-4 text-center">
          <div className="p-4 bg-zinc-100 dark:bg-zinc-800 rounded-full group-hover:scale-110 group-hover:shadow-md transition-all duration-300">
            <svg
              className={`w-10 h-10 ${
                isDragActive ? "text-zinc-200" : "text-zinc-500 dark:text-zinc-400"
              }`}
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
              xmlns="http://www.w3.org/2000/svg"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth="2"
                d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12"
              ></path>
            </svg>
          </div>
          <div className="space-y-1">
            <p className="text-lg font-medium text-zinc-900 dark:text-zinc-100">
              <span className="text-zinc-100 font-semibold group-hover:underline">Click to upload</span> or drag and drop
            </p>
            <p className="text-sm text-zinc-500 dark:text-zinc-400">
              PDF only (max. 20MB)
            </p>
          </div>
        </div>
      </div>
      
      {error && (
        <div className="w-full p-4 rounded-xl bg-red-50 text-red-600 border border-red-200 dark:bg-red-900/20 dark:text-red-400 dark:border-red-900/50 flex items-center shadow-sm animate-in fade-in slide-in-from-top-2 duration-300">
          <svg className="w-5 h-5 mr-3 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          <span className="text-sm font-medium">{error}</span>
        </div>
      )}
    </div>
  );
}
