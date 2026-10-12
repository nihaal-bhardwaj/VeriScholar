export interface RiskSignal {
  source: "consistency" | "ml" | "citations" | "metadata";
  severity: "high" | "medium" | "low";
  message: string;
  evidence: string;
  weight: number;
}

export interface RiskReport {
  analysis_id: string;
  paper_title: string;
  paper_authors: string[];
  risk_score: number; // 0.0 to 100.0
  risk_level: "low" | "medium" | "high" | "critical";
  confidence: number; // 0.0 to 1.0
  summary: string;
  signals: RiskSignal[];
  passed_checks: string[];
  modules_used: string[];
  generated_at: string;
}

export const MOCK_REPORT: RiskReport = {
  analysis_id: "mock-001",
  paper_title: "Latent Drift: Measuring Representation Instability in Fine-Tuned Language Models",
  paper_authors: ["Kowalski", "Menon", "Subramaniam", "Álvarez"],
  risk_score: 42.0,
  risk_level: "medium",
  confidence: 0.81,
  summary: "Several inconsistencies were found. A human reviewer should examine this paper.",
  signals: [
    {
      source: "citations",
      severity: "medium",
      message: "Reference numbering gaps detected",
      evidence: "The bibliography skips three expected numbers, which can mean entries were deleted or renumbered.",
      weight: 0.5,
    },
    {
      source: "citations",
      severity: "medium",
      message: "Unresolved citations found",
      evidence: "Three of forty-two references don't match any public record after normalization.",
      weight: 0.5,
    },
    {
      source: "consistency",
      severity: "low",
      message: "Abstract–body alignment is strong",
      evidence: "Semantic similarity: 0.91 — within expected range for authentic abstracts (0.80–0.97).",
      weight: 0.2,
    },
  ],
  passed_checks: [
    "Metadata match — title, authors, and DOI resolve consistently",
    "Author consistency — author list matches across locations",
    "Figure and table numbering — all references resolve correctly",
    "Duplicate passage detection — no substantial duplicates found",
  ],
  modules_used: ["consistency", "ml", "citations", "metadata"],
  generated_at: "2026-09-17T10:30:00Z",
};

export interface MockCitation {
  num: number;
  text: string;
  status: "verified" | "partial" | "needsreview" | "notfound";
  statusWord: string;
  statusClass: string;
  note: string;
}

export const MOCK_CITATIONS: MockCitation[] = [
  {
    num: 1,
    text: "Vaswani, A., Shazeer, N., Parmar, N., et al. (2017). Attention is all you need. Advances in Neural Information Processing Systems.",
    status: "verified",
    statusWord: "verified",
    statusClass: "text-[var(--good)]",
    note: "doi 10.48550/arXiv.1706.03762 — Crossref",
  },
  {
    num: 2,
    text: "Devlin, J., Chang, M-W., Lee, K., & Toutanova, K. (2019). BERT: Pre-training of deep bidirectional transformers for language understanding. NAACL-HLT.",
    status: "verified",
    statusWord: "verified",
    statusClass: "text-[var(--good)]",
    note: "doi 10.18653/v1/N19-1423 — Crossref",
  },
  {
    num: 3,
    text: "Hendrycks, D., & Gimpel, K. (2016). Gaussian error linear units (GELUs). arXiv preprint.",
    status: "verified",
    statusWord: "verified",
    statusClass: "text-[var(--good)]",
    note: "doi 10.48550/arXiv.1606.08415 — OpenAlex",
  },
  {
    num: 4,
    text: "Kaplan, J., McCandlish, S., Henighan, T., et al. (2020). Scaling laws for neural language models. arXiv preprint.",
    status: "partial",
    statusWord: "partial",
    statusClass: "text-[var(--accent)]",
    note: "doi 10.48550/arXiv.2001.08361 — OpenAlex",
  },
  {
    num: 5,
    text: "Raffel, C., Shazeer, N., Roberts, A., et al. (2020). Exploring the limits of transfer learning with a unified text-to-text transformer. JMLR.",
    status: "verified",
    statusWord: "verified",
    statusClass: "text-[var(--good)]",
    note: "doi unresolved — Crossref",
  },
  {
    num: 6,
    text: "Chen, T., & Guestrin, C. (2016). XGBoost: A scalable tree boosting system. KDD.",
    status: "notfound",
    statusWord: "not found",
    statusClass: "text-[var(--danger)]",
    note: "doi unresolved — no match",
  },
  {
    num: 7,
    text: "Liu, Y., Ott, M., Goyal, N., et al. (2019). RoBERTa: A robustly optimized BERT pretraining approach. arXiv preprint.",
    status: "verified",
    statusWord: "verified",
    statusClass: "text-[var(--good)]",
    note: "doi 10.48550/arXiv.1907.11692 — OpenAlex",
  },
  {
    num: 8,
    text: "Radford, A., Wu, J., Child, R., et al. (2019). Language models are unsupervised multitask learners. OpenAI technical report.",
    status: "needsreview",
    statusWord: "needs review",
    statusClass: "text-[var(--warn)]",
    note: "doi unresolved — no match",
  },
  {
    num: 9,
    text: "Brown, T., Mann, B., Ryder, N., et al. (2020). Language models are few-shot learners. NeurIPS.",
    status: "verified",
    statusWord: "verified",
    statusClass: "text-[var(--good)]",
    note: "doi 10.48550/arXiv.2005.14165 — Crossref",
  },
  {
    num: 10,
    text: "Houlsby, N., Giurgiu, A., Jastrzebski, S., et al. (2019). Parameter-efficient transfer learning for NLP. ICML.",
    status: "partial",
    statusWord: "partial",
    statusClass: "text-[var(--accent)]",
    note: "doi 10.48550/arXiv.1902.00751 — OpenAlex",
  },
];
