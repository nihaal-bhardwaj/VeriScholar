export interface Reference {
  number?: number;
  raw_text: string;
  doi: string | null;
}

export interface ExtractedPage {
  page_number: number;
  text: string;
}

export interface PaperData {
  filename: string;
  file_size_bytes: number;
  page_count: number;
  doi: string | null;
  doi_candidates: string[];
  abstract: string | null;
  title: string | null;
  authors: string[];
  keywords: string[];
  references_text: string | null;
  references: Reference[];
  pages: ExtractedPage[];
}

export interface ModuleStatus {
  status: "pending" | "completed" | "failed";
  warnings: string[];
}

export type MetadataAnalysis = ModuleStatus;

export interface CitationAnalysis extends ModuleStatus {
  verified: number;
  unresolved: number;
}

export interface MLAnalysis extends ModuleStatus {
  risk_probability: number | null;
  signals: string[];
}

export type ConsistencyAnalysis = ModuleStatus;

export interface FinalAssessment {
  risk_score: number | null;
  risk_level: "low" | "moderate" | "high" | null;
  confidence: number | null;
  main_reasons: string[];
}

export interface CombinedAnalysisResponse {
  analysis_id: string;
  status: "processing" | "completed" | "error";
  paper: PaperData;
  metadata_analysis: MetadataAnalysis;
  citation_analysis: CitationAnalysis;
  ml_analysis: MLAnalysis;
  consistency_analysis: ConsistencyAnalysis;
  final_assessment: FinalAssessment;
  warnings?: string[];
}
