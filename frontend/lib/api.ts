import { CombinedAnalysisResponse, PaperData } from "./api-types";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";

// We simulate the backend's future combined analysis contract
// by merging the real extraction with the pending module blocks.
const buildCombinedAnalysis = (realExtraction: { analysis_id: string; status: string; paper: PaperData; warnings?: string[] }): CombinedAnalysisResponse => {
  return {
    ...realExtraction,
    status: realExtraction.status as "completed" | "processing" | "error",
    metadata_analysis: {
      status: "pending",
      warnings: [],
    },
    citation_analysis: {
      status: "pending",
      verified: 0,
      unresolved: 0,
      warnings: [],
    },
    ml_analysis: {
      status: "pending",
      risk_probability: null,
      signals: [],
      warnings: [],
    },
    consistency_analysis: {
      status: "pending",
      warnings: [],
    },
    final_assessment: {
      risk_score: null,
      risk_level: null,
      confidence: null,
      main_reasons: [],
    },
  };
};

export const uploadAndProcessPaper = async (
  file: File,
  onProgress: (stage: string) => void
): Promise<CombinedAnalysisResponse> => {
  onProgress("Uploading PDF to server...");
  
  const formData = new FormData();
  formData.append("file", file);

  try {
    const response = await fetch(`${API_URL}/papers/extract`, {
      method: "POST",
      body: formData,
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => null);
      throw new Error(errorData?.detail || `Server error: ${response.status}`);
    }

    onProgress("Parsing response...");
    
    const data = await response.json();
    return buildCombinedAnalysis(data);

  } catch (error) {
    console.error("API Upload Error:", error);
    throw error;
  }
};
