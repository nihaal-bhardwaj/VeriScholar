# Role Manual — Research Paper ML & Dataset Engineer

## 1. Role name

- **Official role name:** Research Paper ML & Dataset Engineer
- **Short role name:** Paper ML Engineer
- **Purpose:** Build the research-paper integrity ML module: collect and clean a retracted-vs-comparison dataset, define labels carefully, train baseline classifiers, evaluate them honestly, and expose a clean backend callable interface. Outputs are risk signals, never proof of fraud.

## 2. Position in the system

```text
PDF upload
→ PDF extraction           (Technical Lead, Backend & PDF Processing Engineer)
→ Metadata and citation checks   (Citation Integrity Engineer)
→ ML analysis                    ← this role owns this stage
→ Combined result                (Technical Lead orchestrates)
→ Frontend report                (Frontend Engineer)
```

This role consumes the structured extraction output (title, abstract, later full text) and produces the `ml_analysis` block of the shared combined contract in `docs/api-contract.md`.

## 3. Main responsibilities

### Core responsibilities

- Define the positive label carefully and document included and excluded retraction reasons.
- Collect positive examples (retracted papers) and matched comparison papers from official sources.
- Clean the dataset: remove duplicate DOI/title records and explicit retraction notices from text.
- Create leakage-aware splits before any model fitting.
- Train TF-IDF + Logistic Regression and TF-IDF + Linear SVM baselines.
- Evaluate precision, recall, F1, PR-AUC and confusion matrix; record false positives and false negatives.
- Export the selected complete preprocessing/model pipeline so inference matches training.
- Create a clean backend callable interface (`analyse_research_text(title, abstract) -> dict`).
- Never emit random or placeholder risk numbers as if they were real model output.

### Documentation responsibilities

- Keep the `ml_analysis` shape in `docs/api-contract.md` in sync (coordinated changes only).
- Update `docs/project-status.md` and append to `docs/session-handoff.md` after meaningful work.

### Testing responsibilities

- Backend callable-interface tests once the service exists; notebook-level sanity and reproducibility checks until then.

## 4. Owned files and directories

### Primary ownership

```text
ml/
ml/datasets/
ml/notebooks/
ml/training/          (future — create as part of the training-pipeline work)
ml/saved_models/
backend/app/services/paper_ml/
```

### Shared files requiring coordination

- `docs/api-contract.md` — the `ml_analysis` block of the shared combined contract is the output shape.
- The extraction schema (Technical Lead) — coordinate which extracted fields feed the model.
- `backend/app/services/pdf_parser.py` — do not modify without explicit coordination with the Technical Lead.
- `backend/requirements*.txt` — document any dependency additions.

### Other members' areas (do not casually edit)

```text
backend/app/ (api/, core/, schemas/, pdf_parser.py) → Technical Lead
backend/app/services/metadata/, citations/, integrity_rules/, review_detector/ → Citation Integrity Engineer
frontend/ → Frontend Engineer
```

## 5. Programming languages

| Language | Why it is needed | Expected level |
| --- | --- | --- |
| Python | Entire ML pipeline, notebooks and backend service | Advanced |
| Jupyter Notebook | Reproducible exploratory analysis and baselines | Intermediate |
| Markdown | Dataset notes and documentation | Basic |
| SQL | Optional dataset queries over exported metadata (OpenAlex/Crossref) | Basic (optional) |

## 6. Technologies and libraries

| Technology | Purpose in VeriScholar | Required or optional |
| --- | --- | --- |
| pandas | Dataset loading, cleaning, deduplication, summaries | Required |
| NumPy | Numeric arrays and evaluation math | Required |
| scikit-learn | TF-IDF vectorisation, Logistic Regression, LinearSVC, pipelines, metrics, model selection | Required |
| TF-IDF | Text features from title and abstract | Required |
| Logistic Regression | Baseline classifier 1 | Required |
| Linear SVM (LinearSVC) | Baseline classifier 2 | Required |
| joblib | Saving/loading the preprocessing + model pipeline together | Required |
| Matplotlib | Evaluation plots (PR curve, confusion matrix) | Required |
| Pydantic | Typed output schema for the backend callable | Required |
| Sentence Transformers | Optional text-embedding features (later stage) | Optional |
| XGBoost / LightGBM | Optional stronger classifiers (later stage) | Optional |
| imbalanced-learn | Optional resampling techniques (e.g. SMOTE) | Optional |

## 7. Knowledge requirements

### Must understand

- pandas DataFrames: loading, cleaning, deduplication, group-level summaries and stratified splits.
- scikit-learn: `TfidfVectorizer`, `Pipeline`, `LogisticRegression`, `LinearSVC`, `train_test_split`, `cross_val_score`, `classification_report`, `precision_recall_curve`, `average_precision_score`, `confusion_matrix`.
- Why accuracy is misleading on imbalanced data and why PR-AUC matters more than ROC for sparse positives.
- Joblib serialization so inference always uses the same preprocessing as training.
- Python type hints and dict-based output contracts.
- The dataset-risk framing: retracted ≠ fake, and honest-error retractions must be handled in label semantics.

### Should learn during development

- Leakage sources: fitting before splitting, duplicate DOI/title records, retraction-notice text in training data, journal/year-driven shortcuts.
- Retraction taxonomy (e.g. Retraction Watch reasons) and which reasons to include or exclude from the positive label.
- Class-imbalance handling (`class_weight`, resampling) and domain shift between the retracted and comparison pools.
- Missing-data behaviour: empty abstracts and short texts must not crash the pipeline.

### Optional advanced knowledge

- Sentence Transformers embeddings, XGBoost/LightGBM, and explainability tools (SHAP/LIME) for signal extraction.

## 8. Official documentation and sources

| Source | What to learn or obtain from it | Priority |
| --- | --- | --- |
| [pandas documentation](https://pandas.pydata.org/docs/) — verified | DataFrames, cleaning, deduplication | Required |
| [NumPy documentation](https://numpy.org/doc/stable/) — verified | Arrays and numeric operations | Required |
| [scikit-learn documentation](https://scikit-learn.org/stable/) — verified | TF-IDF, Logistic Regression, LinearSVC, metrics, pipelines | Required |
| [joblib documentation](https://joblib.readthedocs.io/en/stable/) — verified | Pipeline serialization | Required |
| [Matplotlib documentation](https://matplotlib.org/stable/) — verified | Evaluation plots | Required |
| [OpenAlex documentation](https://docs.openalex.org/) — verified (docs moved to developers.openalex.org; the API now requires a free key) | Publication metadata source for dataset collection | Recommended |
| [Crossref REST API documentation](https://www.crossref.org/documentation/retrieve-metadata/rest-api/) — verified | DOI metadata and retraction-related metadata | Recommended |
| Retraction Watch database — retractiondatabase.org — **URL could not be verified; confirm before adding** | Retraction records and reasons | Recommended |
| [Sentence Transformers documentation](https://sbert.net/) — verified | Optional text embeddings | Optional |

## 9. Inputs received

### Currently

- **Source:** Technical Lead's extraction pipeline.
- **Fields:** title and abstract via the documented schemas in `docs/api-contract.md`; full text later.
- **Missing-data behaviour:** the pipeline must accept empty/missing abstracts gracefully and continue with whatever text is available, matching how the extractor warns instead of failing.

### Later (integration)

- Called from the backend orchestrator through the agreed service interface `analyse_research_text(title, abstract) -> dict`.

## 10. Outputs produced

### Target callable interface

```python
def analyse_research_text(title: str, abstract: str) -> dict:
    ...
```

### Target output

```json
{
  "status": "completed",
  "risk_probability": 0.61,
  "risk_level": "elevated",
  "signals": [],
  "model_version": "paper-model-v1",
  "limitations": []
}
```

- **Consumer:** Technical Lead (orchestrator) and Frontend Engineer (report display).
- **Contract:** maps into the `ml_analysis` block of `docs/api-contract.md`.
- **Status values:** `pending` until the module actually runs; `completed` when it does; `unavailable`/`failed` on error — never fabricated numbers.
- **Signals:** explainable text patterns, not opaque scores.
- **Risk wording:** human-review wording such as "High attention recommended" — never "This paper is fake".
- **Labels:** represent retraction-like or integrity-risk patterns, not proof of fraud.

## 11. Things to implement

### Dataset pipeline

1. Define the positive label carefully; document included and excluded retraction reasons.
2. Collect positive examples from official sources (Retraction Watch, OpenAlex, Crossref).
3. Collect matched comparison papers from the same sources and time period.
4. Remove duplicate DOI/title records.
5. Remove explicit retraction notices from the text (they leak the label).
6. Create leakage-aware splits (by DOI, with journal/year balance) before any fitting.
7. Record dataset summary: class counts, split sizes, deduplication statistics.

### Baseline models

8. Train TF-IDF + Logistic Regression.
9. Train TF-IDF + Linear SVM.
10. Evaluate precision, recall, F1, PR-AUC and confusion matrix.
11. Record false positives and false negatives for human review.
12. Export the selected complete preprocessing/model pipeline (joblib) with a version tag.

### Integration

13. Create the clean backend callable `analyse_research_text(title, abstract) -> dict` in `backend/app/services/paper_ml/` with a Pydantic-typed output following the `ml_analysis` contract.
14. Handle empty abstracts and short inputs gracefully.
15. Do not output model values (not even placeholders) before the trained pipeline exists.

## 12. Acceptance criteria

- Baseline notebook is reproducible from a documented data path.
- Dataset summary (class counts, splits, deduplication stats) is recorded.
- Evaluation reports precision, recall, F1, PR-AUC and confusion matrix.
- No leakage: splits are created before any fitting; retraction notices removed from text; no duplicate DOI/title across train/test.
- Model and preprocessing pipeline are exported together so inference matches training.
- Risk output uses explainable wording and never claims a paper is fake.
- Backend callable matches the `ml_analysis` contract agreed with the Technical Lead.

## 13. Testing responsibilities

### Backend tests (once the service exists)

```bash
cd backend
python -m pytest
```

- Callable-interface tests: happy path, empty abstract, very short text, missing fields.

### Notebook-level checks (until then)

- Dataset sanity assertions (label counts, no duplicate DOIs, no retraction-notice text remaining).
- Deterministic, leakage-free splits.
- The full sklearn pipeline runs end to end and produces the recorded metrics.

### Edge cases

- Papers with no abstract, very short abstracts, non-English text, unexpected characters.

### Evidence to record

- Notebook evaluation output (metrics, confusion matrix, PR curve).
- Sample false-positive and false-negative cases for the handoff.

## 14. Dependencies on other roles

### Needs from other roles

- **Technical Lead, Backend & PDF Processing Engineer:** stable extraction schema and agreed feature fields (title/abstract), agreement on the `ml_analysis` output shape, and wiring of the backend callable.
- **Citation Integrity Engineer:** optional later — metadata/citation-derived features with coordinated interface changes.

### What other roles need from this role

- The `ml_analysis` output shape and callable interface for orchestrator integration.
- Dataset location, label definition and evaluation numbers for reports.

### What may be mocked temporarily

- The backend callable may be stubbed by the Technical Lead while building the orchestrator — clearly labelled as a mock, never presented as real analysis.

### Contract changes requiring coordination

Any `ml_analysis` shape change requires: schema update, backend test update, `docs/api-contract.md` update, `sample-responses/` update, frontend coordination and a `docs/project-status.md` entry.

## 15. Common mistakes to avoid

- Treating "retracted" as proof the paper is fraudulent — many retractions are honest errors.
- Leakage: fitting splits before deduplication, leaving retraction notices in the text, or allowing journal/year/duplicate-DOI shortcuts.
- Reporting only accuracy on imbalanced data; ignoring PR-AUC and false-negative review.
- Ignoring class imbalance and domain shift between the retracted and comparison pools.
- Saving data or models that are too large for Git (use Git LFS later if genuinely needed).
- Changing the PDF parser or API schemas without coordination.
- Outputting random or placeholder risk numbers as if they were real model output.
- Releasing a model export without its matching preprocessing step.

## 16. Definition of done

- [ ] Dataset pipeline documented and reproducible from a documented data path.
- [ ] Baseline models trained and evaluated with recorded metrics (precision, recall, F1, PR-AUC, confusion matrix).
- [ ] Selected pipeline exported together with preprocessing for backend use.
- [ ] Callable interface agreed with the Technical Lead (may be pending).
- [ ] Tests run (backend `pytest` suite and notebook checks).
- [ ] `docs/project-status.md` updated; handoff entry appended to `docs/session-handoff.md`.
- [ ] No unrelated files modified.
- [ ] Commit/push status reported to the team.

## 17. Handoff requirements

After meaningful changes, report:

- Dataset location and collection/cleaning steps.
- Label definition and included/excluded retraction reasons.
- Deduplication and split statistics.
- Evaluation numbers, sample false positives and false negatives.
- Model export location and version; how preprocessing is bundled.
- API shape proposal for the backend callable.
- Blockers and dependencies.
- Whether changes were committed and pushed.

## 18. Viva knowledge

Be able to explain:

- The VeriScholar pipeline and why ML outputs are risk signals, not proof of misconduct.
- Why retracted ≠ fake and how honest-error retractions shape the label definition.
- Every leakage type handled (splitting, duplicate DOIs, retraction-notice text, journal/year shortcuts) and how the splits avoid them.
- Why PR-AUC and confusion-matrix review beat raw accuracy on imbalanced data.
- TF-IDF + Logistic Regression vs TF-IDF + Linear SVM trade-offs.
- Why preprocessing and model must be exported and loaded together.
- The `ml_analysis` contract in `docs/api-contract.md` and how status must be reported honestly (`pending`/`unavailable`, never fabricated numbers).
- How the callable handles empty abstracts and short inputs.
- Where the dataset comes from (Retraction Watch, OpenAlex, Crossref) and the limits of those sources.
