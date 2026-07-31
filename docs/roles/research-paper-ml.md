# Role Playbook — Research Paper ML & Dataset Engineer

## Role purpose

Build the research-paper integrity ML module: collect and clean a retracted-vs-comparison dataset, define labels, train baseline classifiers, evaluate them honestly, and expose a clean backend callable interface. Outputs are risk signals, never proof of fraud.

## Owned directories

```text
ml/
ml/datasets/
ml/notebooks/
ml/training/
ml/saved_models/
backend/app/services/paper_ml/
```

## Files requiring coordination

- `docs/api-contract.md` — the `ml_analysis` block of the shared combined contract is your output shape.
- The extraction schema (Technical Lead) — decide which fields feed the model.
- Do not change the PDF parser unless coordinated with the Technical Lead.
- Do not modify `backend/app/services/pdf_parser.py` without explicit coordination.

## Current state

- Directory skeleton only (`ml/datasets`, `ml/notebooks`, `ml/saved_models`).
- No dataset, labels or models yet.
- No model code in `backend/app/services/paper_ml/` yet (directory does not exist yet).
- `ml/training/` does not exist yet; create it as part of the training-pipeline work.

## Immediate next task

Create the reproducible baseline pipeline.

## Ordered task backlog

1. Define the positive label carefully.
2. Document included and excluded retraction reasons.
3. Collect positive examples.
4. Collect matched comparison papers.
5. Remove duplicate DOI/title records.
6. Remove explicit retraction notices from text.
7. Create leakage-aware splits.
8. Train TF-IDF + Logistic Regression.
9. Train TF-IDF + Linear SVM.
10. Evaluate precision, recall, F1, PR-AUC and confusion matrix.
11. Record false positives and false negatives.
12. Export the selected complete preprocessing/model pipeline.
13. Create a clean backend callable interface.

## Input contract

Text fields produced by the extraction pipeline (title, abstract, and later full text). Accept extracted data through the documented schemas in `docs/api-contract.md`.

## Output contract

Target callable interface:

```python
def analyse_research_text(title: str, abstract: str) -> dict:
    ...
```

Target output:

```json
{
  "status": "completed",
  "risk_probability": 0.61,
  "risk_level": "elevated",
  "signals": [],
  "model_version": "paper-model-v1"
}
```

Labels represent retraction-like or integrity-risk patterns, not proof of fraud. `signals` must be explainable (e.g. text patterns), not opaque.

## Acceptance criteria

- Baseline notebook is reproducible from a documented data path.
- Dataset summary (class counts, splits, deduplication stats) is recorded.
- Evaluation reports precision, recall, F1, PR-AUC and confusion matrix.
- No leakage: splits are created before any fitting; retraction notices removed from text.
- Model and preprocessing pipeline are exported together so inference matches training.
- Risk output uses explainable wording and never claims a paper is fake.

## Required tests

Backend callable interface tests (once the service exists). Until then, notebook-level checks: dataset sanity assertions, deterministic splits, `sklearn` pipeline evaluation running end to end.

```bash
cd backend
python -m pytest
```

## Common mistakes to avoid

- Treating label = "retracted paper" as proof the paper is fraudulent.
- Fitting splits before deduplication/leakage handling.
- Reporting only accuracy; ignoring PR-AUC and false-negative review.
- Saving data or models that are too large for Git (use Git LFS later if genuinely needed).
- Changing the PDF parser or API schemas without coordination.

## Handoff requirements

Update `docs/project-status.md` and append to `docs/session-handoff.md` (bottom of file), including dataset location, label definition, evaluation numbers and any API shape proposal.

## Definition of done

- Dataset pipeline documented and reproducible.
- Baseline models trained and evaluated with recorded metrics.
- Selected pipeline exported for backend use.
- Callable interface agreed with the Technical Lead (may be pending).
- Status and handoff documents updated.
