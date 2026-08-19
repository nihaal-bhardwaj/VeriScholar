"""ML analysis endpoint.

Runs the ML text analysis (feature extraction + anomaly scoring) on
submitted text without requiring a PDF upload. Outputs are explainable
screening signals, never a fake-paper verdict.
"""

from fastapi import APIRouter, status

from app.schemas.ml import MLAnalysisRequest, MLAnalysisResult
from app.services.ml.ml_pipeline import run_ml_analysis

router = APIRouter()


@router.post(
    "/ml/analyze",
    response_model=MLAnalysisResult,
    status_code=status.HTTP_200_OK,
    tags=["ml"],
)
def analyze(request: MLAnalysisRequest) -> MLAnalysisResult:
    """Run the ML text analysis over the submitted text."""
    return run_ml_analysis(request.full_text, request.abstract, request.pages)