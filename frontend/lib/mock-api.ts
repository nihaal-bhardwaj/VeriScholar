import { CombinedAnalysisResponse } from "./api-types";
import mockData from "./sample-paper-analysis.json";

// We simulate the backend's future combined analysis contract
// by merging the existing mock extraction with the pending module blocks.
export const getMockCombinedAnalysis = (): CombinedAnalysisResponse => {
  return {
    ...(mockData as unknown as Partial<CombinedAnalysisResponse>),
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
  } as CombinedAnalysisResponse;
};

export const simulateUploadAndProcess = async (
  file: File,
  onProgress: (stage: string) => void
): Promise<CombinedAnalysisResponse> => {
  // Simulate network delay and processing stages
  const delay = (ms: number) => new Promise((resolve) => setTimeout(resolve, ms));

  onProgress("Uploading PDF...");
  await delay(1000);

  onProgress("Extracting text and references...");
  await delay(1500);

  onProgress("Verifying metadata with Crossref...");
  await delay(1000);

  onProgress("Running ML models...");
  await delay(1000);

  onProgress("Generating report...");
  await delay(500);

  return getMockCombinedAnalysis();
};
