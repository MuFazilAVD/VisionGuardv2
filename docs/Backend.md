# Backend Documentation

## Overview

The backend is a FastAPI application under `backend/`. It exposes endpoints for training, training status, sample data, and realtime claim assessment.

## Running Locally

```bash
cd backend
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

## Environment Variables

| Variable | Default | Purpose |
| --- | --- | --- |
| `OPENAI_BASE_URL` | `https://d2brdeqy144bwg.cloudfront.net/myllm/v1` | LLM API base URL. |
| `OPENAI_API_KEY` | empty | LLM API key. |
| `OPENAI_MODEL` | empty | LLM model name. |
| `APP_CORS_ORIGINS` | local dev origins | Comma-separated CORS origins. |

## Endpoints

### `POST /visionguardv2/api/training/retrain`

Runs the complete training pipeline:

1. Ensures generated sample data exists.
2. Loads historical claims.
3. Loads rules workbook.
4. Applies historical rules.
5. Trains the multiclass classifier.
6. Computes anomaly statistics.
7. Persists artifacts.
8. Returns metrics.

Example response:

```json
{
  "status": "trained",
  "trained_at": "2026-06-16T10:05:00Z",
  "metrics": {
    "accuracy": 0.94,
    "f1_weighted": 0.94,
    "train_records": 6400,
    "test_records": 1600
  },
  "artifact_version": "20260616T100500Z"
}
```

### `GET /visionguardv2/api/training/status`

Returns current training status.

Example response before training:

```json
{
  "trained": false,
  "last_training_date": null,
  "metrics": null,
  "artifact_version": null,
  "artifacts": []
}
```

Example response after training:

```json
{
  "trained": true,
  "last_training_date": "2026-06-16T10:05:00Z",
  "metrics": {
    "accuracy": 0.94,
    "f1_weighted": 0.94
  },
  "artifact_version": "20260616T100500Z",
  "artifacts": [
    "rf_model.joblib",
    "feature_pipeline.joblib",
    "metadata.json",
    "anomaly_stats.json",
    "training_metrics.json"
  ]
}
```

### `POST /visionguardv2/api/claims/analyze`

Accepts either:

- JSON body with `claims`.
- Multipart form upload with a CSV file field named `file`.

Supports one or more claims per request.

JSON request:

```json
{
  "claims": [
    {
      "ClaimId": "RT001",
      "Gender": "F",
      "Age": 45,
      "ServiceDateFrom": "5/12/2024",
      "PlaceOfService": "11",
      "LineNumber": 1,
      "ProcedureCode": "99213",
      "ProcedureName": "Office Visit Established Patient",
      "Modifier": "25",
      "Modifier2": "",
      "Modifier3": "",
      "Primary_Diagnosis_Pointer": "1",
      "Primary_Diagnosis": "H52.4",
      "LONG_DESCRIPTION": "Routine eye exam",
      "ClaimLineTotalPaid": 80,
      "AmtCharged": 120,
      "AllowedUnits": 1,
      "AmtDisallowed": 0,
      "AmtEligible": 100,
      "AmtCopay": 20,
      "AmtCoinsurance": 0,
      "AmtDeductible": 0,
      "ProviderNPI": "1234567890",
      "GroupId": "G1",
      "GroupNumber": "GRP100",
      "LOB": "COMM",
      "CoverageCode": "PPO",
      "State": "OH"
    }
  ]
}
```

Example response:

```json
{
  "processed_at": "2026-06-16T10:06:00Z",
  "count": 1,
  "assessments": [
    {
      "claim_id": "RT001",
      "line_number": 1,
      "risk_level": "Medium",
      "final_risk_score": 0.54,
      "confidence_level": 0.80,
      "triggered_indicators": [
        {
          "rule_id": "R009",
          "name": "Invalid CPT for vision plan",
          "severity": "High",
          "category": "Coding"
        }
      ],
      "narrative": {
        "executive_summary": "...",
        "investigation_findings": ["..."],
        "key_risk_indicators": ["..."],
        "risk_classification": "...",
        "recommended_review_actions": ["..."],
        "metadata": {
          "model_used": "fallback",
          "llm_success": false,
          "fallback_reason": "OPENAI_API_KEY or OPENAI_MODEL is not configured"
        }
      }
    }
  ]
}
```

### `GET /visionguardv2/api/sample-data`

Ensures generated datasets exist and returns summary information.

Example response:

```json
{
  "historical_claims": {
    "path": "backend/app/data/historical_claims.csv",
    "record_count": 8000,
    "preview": []
  },
  "rules": {
    "path": "backend/app/data/rules.xlsx",
    "record_count": 9,
    "preview": []
  },
  "realtime_claims": {
    "path": "realtime_claims.csv",
    "record_count": 3,
    "preview": []
  }
}
```

## Error Handling

- Missing artifacts on claim analysis trigger automatic training from generated data.
- Empty claim submissions return HTTP 400.
- Missing required claim fields returns HTTP 422.
- LLM failures do not fail claim assessment. The narrative service returns fallback text and metadata.
