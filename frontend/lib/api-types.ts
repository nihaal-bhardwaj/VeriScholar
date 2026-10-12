export interface Reference {
  number?: number;
  raw_text: string;
  doi: string | null;
}

export interface ExtractedPage {
  page_number: number;
  text: string;
}

export interface ExtractionQuality {
  quality_score: number;
  status: "good" | "degraded" | "poor";
  issues: string[];
}

export interface PaperData {
  filename: string;
  file_size_bytes: number;
  page_count: number;
  doi: string | null;
  doi_candidates: string[];
  abstract: string | null;
  abstract_status?: "found" | "absent" | "uncertain";
  abstract_confidence?: number | null;
  title: string | null;
  title_confidence?: number | null;
  title_source?: string | null;
  authors: string[];
  author_confidence?: number | null;
  author_source?: string | null;
  keywords: string[];
  references_text: string | null;
  references: Reference[];
  extraction_quality?: ExtractionQuality | null;
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
  risk_level: "low" | "moderate" | "medium" | "high" | "critical" | null;
  confidence: number | null;
  assessment_status?: "evaluated" | "limited_evidence" | "undetermined";
  main_reasons: string[];
  modules_used?: string[];
  paper_metadata?: Record<string, any> | null;
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
  modules_used?: string[];
  paper_metadata?: Record<string, any> | null;
  warnings?: string[];
}
