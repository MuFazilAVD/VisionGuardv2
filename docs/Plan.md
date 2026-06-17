# Claims Risk Assessment POC Implementation Plan

## Objective

Rebuild the existing Fabric/Synapse/Spark notebook implementation as a local FastAPI and React proof of concept. The notebooks remain the source of truth for the risk logic, but the new implementation must run without Spark, Delta tables, Lakehouse storage, `notebookutils`, or `mssparkutils`.

## Source Files Reviewed

- `batch.py`: Spark notebook export for historical ingestion, rule execution, supervised pattern training, anomaly scoring, explainability, gold table creation, and artifact persistence.
- `realtime.py`: Spark notebook export for incoming claim scoring using persisted artifacts and realtime-supported rules.
- `realtime_claims.csv`: Three-row incoming claim sample and the canonical realtime claim schema.

## Key Reverse Engineering Findings

1. The system is a three-layer claim risk assessment engine:
   - Layer 1: deterministic rules.
   - Layer 2: multiclass supervised pattern classification.
   - Layer 3: numeric anomaly scoring using z-scores and L2 distance.
2. Historical batch processing applies nine rules: R006, R007, R008, R009, R013, R014, R015, R016, and R017.
3. Realtime processing applies only five rules: R006, R007, R008, R009, and R017.
4. The supervised target is the `Flag` column. It is multiclass, not binary.
5. The notebook used `RandomForestClassifier` with numeric and one-hot encoded categorical inputs.
6. The anomaly layer is not a separate model. It is deterministic statistics: mean, standard deviation, z-score, L2 distance, and normalization.
7. The final risk score weights are fixed:
   - 40% rule count.
   - 30% supervised pattern confidence.
   - 30% anomaly score.
8. Old narrative generation was deterministic hardcoded text. The new implementation must use LLM generation with deterministic fallback.

## Implementation Phases

### Phase 1: Documentation

- Create implementation plan.
- Create tracker.
- Document the full architecture.
- Document batch notebook reverse engineering.
- Document realtime notebook reverse engineering.
- Document schemas and artifact contracts.
- Document backend APIs.
- Document frontend structure and workflows.
- Document style and accessibility expectations.
- Document local and deployment setup.

### Phase 2: Backend Foundation

- Create FastAPI application.
- Add settings and path management.
- Add Pydantic schemas.
- Add repository helpers for data and artifacts.
- Add deterministic rule engine with historical and realtime modes.
- Add synthetic data generator for historical claims and editable rules workbook.
- Add feature preparation pipeline.
- Add model training service.
- Add anomaly statistics service.
- Add realtime scoring service.
- Add LLM narrative service with fallback.

### Phase 3: API

- `POST /visionguardv2/api/training/retrain`
- `GET /visionguardv2/api/training/status`
- `POST /visionguardv2/api/claims/analyze`
- `GET /visionguardv2/api/sample-data`

### Phase 4: Frontend

- Create Vite React TypeScript app.
- Configure Tailwind.
- Add shadcn-style local UI primitives.
- Build a single claim assessment workspace with engine sync, data upload, full-schema editing, and inline results.
- Use business-friendly language only in UI.
- Add API service with environment-configurable backend URL.

### Phase 5: Testing and Verification

- Unit tests for deterministic rules.
- Pipeline tests for end-to-end training and realtime scoring.
- API tests for status, retraining, sample data, and claim analysis.
- Frontend production build check.
- Start backend and frontend development servers for local trial.

## Implementation Choices

### Backend

- Python 3.14 local environment.
- FastAPI for HTTP API.
- Pandas and NumPy for tabular logic.
- Scikit-Learn for the multiclass RandomForest pipeline.
- OpenPyXL for editable Excel rules.
- Joblib and JSON for artifact persistence.
- Pydantic for request and response validation.

### Frontend

- React, TypeScript, and Vite.
- Tailwind CSS.
- Local shadcn-style primitives, not a generated shadcn CLI dependency.
- Phosphor icons for common actions.
- No technical model terminology in visible UI.

## Risks and Mitigations

- The `batch.py` export is malformed: quotes and newlines are partially stripped. Mitigation: document both the recovered logic and the malformed export caveat.
- The original historical `claims.csv` and `Sample_Rules_For_ML.xlsx` are missing. Mitigation: generate realistic replacements that preserve schema and rule coverage.
- Realtime notebook normalized anomaly scores within the incoming mini-batch, while the business requirement asks for persisted anomaly stats. Mitigation: persist training `max_anomaly_score` and clip normalized realtime anomaly scores to 1.0 for stable single-claim behavior.
- LLM credentials may be absent locally. Mitigation: deterministic fallback returns complete narrative sections and metadata.
