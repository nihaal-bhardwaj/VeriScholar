from pydantic import BaseModel, Field
from typing import List, Optional

class CitationVerifyRequest(BaseModel):
    analysis_id: str = Field(..., description="UUID of the analysis")
    references: List[dict] = Field(..., description="List of extracted references")

class CitationAnalysisResult(BaseModel):
    status: str = Field(default="completed")
    verified: int = Field(default=0)
    unresolved: int = Field(default=0)
    warnings: List[str] = Field(default_factory=list)
    details: List[dict] = Field(default_factory=list)

