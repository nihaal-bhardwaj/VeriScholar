import { CombinedAnalysisResponse, PaperData } from "./api-types";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";

export const uploadAndProcessPaper = async (
  file: File,
  onProgress: (stage: string) => void
): Promise<CombinedAnalysisResponse> => {
  try {
    // 1. Upload & Extract
    onProgress("Uploading PDF & extracting contents...");
    const formData = new FormData();
    formData.append("file", file);

    const extractRes = await fetch(`${API_URL}/papers/extract`, {
      method: "POST",
      body: formData,
    });
    if (!extractRes.ok) {
      const errorData = await extractRes.json().catch(() => null);
      throw new Error(errorData?.detail || `Extraction error: ${extractRes.status}`);
    }
    const extraction = await extractRes.json();
    const paper: PaperData = extraction.paper;
    const fullText = paper.pages.map((p: { text: string }) => p.text).join("\n");

    // 2. Parallel Module Execution
    onProgress("Running ML Risk models, verifying Citations & Metadata...");

    const [citationRes, mlRes, integrityRes, metadataRes] = await Promise.all([
      // Execute Citations
      fetch(`${API_URL}/citations/verify`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          analysis_id: extraction.analysis_id,
          references: paper.references,
        }),
      })
        .then((res) => (res.ok ? res.json() : { status: "failed", verified: 0, unresolved: 0, warnings: [] }))
        .catch(() => ({ status: "failed", verified: 0, unresolved: 0, warnings: ["Network error"] })),

      // Execute ML Analysis
      fetch(`${API_URL}/ml/analyze`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          full_text: fullText,
          abstract: paper.abstract || "",
          pages: paper.pages,
        }),
      })
        .then((res) => (res.ok ? res.json() : { signals: [], passed_rules: [], ml_risk_contribution: 0, confidence: 0 }))
        .catch(() => ({ signals: [], passed_rules: [], ml_risk_contribution: 0, confidence: 0 })),

      // Execute Integrity Check
      fetch(`${API_URL}/integrity/check`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          analysis_id: extraction.analysis_id,
          full_text: fullText,
          authors: paper.authors,
          references: paper.references,
          pages: paper.pages,
        }),
      })
        .then((res) => (res.ok ? res.json() : { flags: [], warnings: [], passed_checks: [], consistency_score: 0 }))
        .catch(() => ({ flags: [], warnings: [], passed_checks: [], consistency_score: 0 })),

      // Execute Metadata Verification
      fetch(`${API_URL}/citations/metadata`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          title: paper.title,
          authors: paper.authors,
          doi: paper.doi,
        }),
      })
        .then((res) => (res.ok ? res.json() : null))
        .catch(() => null),
    ]);

    // 3. Generate Final Report
    onProgress("Synthesizing final risk assessment...");
    const reportRes = await fetch(`${API_URL}/report/generate`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        analysis_id: extraction.analysis_id,
        paper_title: paper.title || "",
        paper_authors: paper.authors || [],
        abstract: paper.abstract || "",
        keywords: paper.keywords || [],
        consistency_report: integrityRes,
        ml_results: mlRes,
        citation_results: citationRes,
        metadata_results: null,
        extraction_quality: paper.extraction_quality,
        paper_metadata: metadataRes,
      }),
    });
    const finalReport = reportRes.ok ? await reportRes.json() : null;

    // 4. Transform into UI Contract (CombinedAnalysisResponse)
    onProgress("Done.");

    const isMetadataComplete =
      Boolean(finalReport?.modules_used?.includes("metadata")) ||
      Boolean(metadataRes && (metadataRes.matched || metadataRes.status === "verified"));

    return {
      analysis_id: extraction.analysis_id,
      status: "completed",
      paper: paper,
      metadata_analysis: {
        status: isMetadataComplete
          ? "completed"
          : metadataRes?.status === "unavailable"
          ? "failed"
          : "pending",
        warnings: metadataRes?.status === "unavailable" ? ["Metadata provider unreachable"] : [],
      },
      citation_analysis: {
        status: citationRes.status || "completed",
        verified: citationRes.verified || 0,
        unresolved: citationRes.unresolved || 0,
        warnings: citationRes.warnings || [],
      },
      ml_analysis: {
        status: mlRes.confidence > 0 ? "completed" : "failed",
        risk_probability: mlRes.ml_risk_contribution || 0,
        signals:
          mlRes.signals?.map(
            (s: { severity: string; message: string }) => `${s.severity.toUpperCase()}: ${s.message}`
          ) || [],
        warnings: [],
      },
      consistency_analysis: {
        status: "completed",
        warnings: integrityRes.warnings || [],
      },
      final_assessment: {
        risk_score: finalReport?.risk_score || 0,
        risk_level: finalReport?.risk_level || "low",
        confidence: finalReport?.confidence || 0,
        assessment_status: finalReport?.assessment_status || "evaluated",
        main_reasons: finalReport?.summary ? [finalReport.summary] : [],
        modules_used: finalReport?.modules_used || [],
        paper_metadata: finalReport?.paper_metadata || metadataRes,
      },
      modules_used: finalReport?.modules_used || [],
      paper_metadata: finalReport?.paper_metadata || metadataRes,
      warnings: extraction.warnings || [],
    };

  } catch (error) {
    console.error("API Upload Orchestration Error:", error);
    throw error;
  }
};
