# System Architecture

## Overview

The Claims Risk Assessment POC is a local full-stack application that recreates the behavior of the original Fabric/Synapse notebooks without Spark. It has three major parts:

1. A FastAPI backend that owns data generation, training, artifact persistence, realtime scoring, and LLM-backed narratives.
2. A React frontend for claims analysts and investigators.
3. Local CSV, Excel, joblib, and JSON artifacts that replace Lakehouse files, Delta tables, Spark ML artifacts, and notebook metadata.

## High-Level Architecture

```text
React UI
  |
  | HTTP JSON / multipart CSV
  v
FastAPI
  |
  +--> Sample Data Service
  |      +--> backend/app/data/historical_claims.csv
  |      +--> backend/app/data/rules.xlsx
  |
  +--> Training Service
  |      +--> Rule Engine, historical mode
  |      +--> Scikit-Learn feature pipeline
  |      +--> RandomForest multiclass classifier
  |      +--> Anomaly statistics
  |      +--> backend/artifacts/*.joblib and *.json
  |
  +--> Realtime Service
  |      +--> Rule Engine, realtime mode
  |      +--> Loaded feature pipeline and classifier
  |      +--> Loaded anomaly statistics
  |      +--> Final risk scoring
  |      +--> LLM narrative service with fallback
  |
  v
Business-friendly claim assessment response
```

## Backend Package Layout

```text
backend/
  main.py
  app/
    api/
      claims.py
      sample_data.py
      training.py
    services/
      llm_service.py
      realtime_service.py
      sample_data_service.py
      training_service.py
    pipelines/
      anomaly.py
      features.py
      risk_scoring.py
      rules_engine.py
    schemas/
      claim.py
      sample_data.py
      scoring.py
      training.py
    repositories/
      artifact_repository.py
      data_repository.py
    utils/
      paths.py
    data/
      historical_claims.csv
      rules.xlsx
  artifacts/
    rf_model.joblib
    encoders.joblib
    feature_pipeline.joblib
    metadata.json
    anomaly_stats.json
    training_metrics.json
```

## Data Flow

### Training Flow

```text
historical_claims.csv
  |
  v
Load and type-normalize claims
  |
  v
Load rules.xlsx for business metadata
  |
  v
Apply historical deterministic rules
  |
  v
Compute Rule_Flag_Count
  |
  v
Compute BilledAllowedRatio
  |
  v
Prepare numeric and categorical model inputs
  |
  v
Train multiclass pattern classifier
  |
  v
Compute anomaly means, standard deviations, and max score
  |
  v
Persist artifacts and metrics
```

### Realtime Flow

```text
Incoming JSON or CSV claims
  |
  v
Validate schema and type-normalize fields
  |
  v
Apply realtime deterministic rules only
  |
  v
Compute Rule_Flag_Count
  |
  v
Load trained feature pipeline and classifier
  |
  v
Score claim pattern and confidence
  |
  v
Load anomaly stats and compute normalized L2 anomaly score
  |
  v
Compute final risk score
  |
  v
Assign risk level
  |
  v
Generate LLM narrative or deterministic fallback
  |
  v
Return business assessment
```

## Three-Layer Risk Scoring Flow

### Layer 1: Deterministic Rules

Historical mode applies:

- R006: Modifier 59 on vision codes.
- R007: High billed-to-allowed ratio.
- R008: Excessive units on exam codes.
- R009: CPT rule violation.
- R013: Provider high exam volume.
- R014: Provider high material volume.
- R015: Provider high average billed amount.
- R016: Provider high add-on usage.
- R017: Missing diagnosis.

Realtime mode applies:

- R006
- R007
- R008
- R009
- R017

Realtime intentionally excludes provider aggregation rules because a single incoming claim batch does not have reliable historical provider volume context.

### Layer 2: Supervised Pattern Classification

The target is `Flag`, a multiclass business pattern label. Known labels are:

- CCI Edits Claims
- Exam after Comprehensive
- Bilateral Claims
- Two Exams in One Day

The model is a Scikit-Learn `RandomForestClassifier`, preserving the notebook's model family.

Numeric inputs:

- Age
- Rule_Flag_Count
- AmtCharged
- AmtEligible
- ClaimLineTotalPaid
- AllowedUnits
- BilledAllowedRatio

Categorical inputs:

- ProcedureCode
- Gender
- State
- LOB
- CoverageCode

Categorical processing uses one-hot encoding with unknown categories ignored at scoring time.

### Layer 3: Anomaly Scoring

The anomaly layer is deterministic:

1. Compute the mean for each numeric feature.
2. Compute the standard deviation for each numeric feature.
3. Compute z-score for each numeric feature.
4. Compute L2 distance:

```text
AnomalyScore = sqrt(sum(zscore^2))
```

5. Normalize:

```text
AnomalyScore_Normalized = AnomalyScore / MaxAnomalyScore
```

The POC persists `MaxAnomalyScore` from training for stable realtime scoring. Realtime values are clipped to 1.0 after normalization so risk scores remain bounded.

## Final Risk Score

```text
Final_RiskScore =
  0.4 * Rule_Flag_Count_Normalized
  + 0.3 * ML_RiskScore
  + 0.3 * AnomalyScore_Normalized
```

The UI and API response avoid technical phrasing. Internally `ML_RiskScore` is kept as an artifact-compatible field, while the frontend labels it as pattern confidence.

## Risk Levels

- High: `Final_RiskScore >= 0.75`
- Medium: `Final_RiskScore >= 0.50`
- Low: `Final_RiskScore < 0.50`

## Storage Architecture

The original storage system used Lakehouse files, Delta tables, and Spark ML model folders. The POC replaces that with local files:

```text
backend/app/data/
  historical_claims.csv
  rules.xlsx

backend/artifacts/
  rf_model.joblib
  encoders.joblib
  feature_pipeline.joblib
  metadata.json
  anomaly_stats.json
  training_metrics.json
```

The model and preprocessing pipeline are persisted separately so future engineers can inspect or replace either part.

## Deployment Architecture

Development:

- Backend: local FastAPI at `http://localhost:8000`.
- Frontend: local Vite dev server at `http://localhost:5173`.

Production:

- Frontend reads `VITE_API_BASE_URL`.
- Default production API base URL is `https://d2brdeqy144bwg.cloudfront.net`.
- Backend LLM base URL defaults to `https://d2brdeqy144bwg.cloudfront.net/myllm/v1`.

## Security and Operational Notes

- No PHI-grade security controls are implemented; this is a POC.
- LLM calls send claim assessment context to the configured LLM endpoint.
- `OPENAI_API_KEY` and `OPENAI_MODEL` must be environment variables.
- Missing LLM configuration does not block claim analysis because fallback narratives are always generated.
