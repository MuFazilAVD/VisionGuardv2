# Deployment and Local Setup

## Prerequisites

- Python 3.14 or compatible Python 3.11+ runtime.
- Node.js 24 or compatible modern Node runtime.
- npm.

## Backend Setup

From the repository root:

```bash
cd backend
python -m pip install -r requirements.txt
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

The backend can generate missing sample data and train artifacts from scratch.

## Frontend Setup

From the repository root:

```bash
cd frontend
npm install
npm run dev
```

The local frontend defaults to:

```text
http://localhost:5173
```

## Environment Variables

Backend:

```text
OPENAI_BASE_URL=https://d2brdeqy144bwg.cloudfront.net/myllm/v1
OPENAI_API_KEY=<secret>
OPENAI_MODEL=<model>
APP_CORS_ORIGINS=https://d2brdeqy144bwg.cloudfront.net,https://d3bkb5k71wphsh.cloudfront.net,http://localhost:5173,http://127.0.0.1:5173
```

Frontend:

```text
VITE_API_BASE_URL=http://localhost:8000
```

Production frontend default:

```text
https://d2brdeqy144bwg.cloudfront.net
```

## Training From Scratch

Start the backend and call:

```bash
curl -X POST http://localhost:8000/visionguardv2/api/training/retrain
```

This will create or refresh:

- `backend/app/data/historical_claims.csv`
- `backend/app/data/rules.xlsx`
- `backend/artifacts/rf_model.joblib`
- `backend/artifacts/feature_pipeline.joblib`
- `backend/artifacts/encoders.joblib`
- `backend/artifacts/metadata.json`
- `backend/artifacts/anomaly_stats.json`
- `backend/artifacts/training_metrics.json`

## Claim Analysis

JSON:

```bash
curl -X POST http://localhost:8000/visionguardv2/api/claims/analyze \
  -H "Content-Type: application/json" \
  -d '{"claims":[...]}' 
```

CSV:

```bash
curl -X POST http://localhost:8000/visionguardv2/api/claims/analyze \
  -F "file=@../realtime_claims.csv"
```

## Build

Backend tests:

```bash
cd backend
python -m pytest
```

Frontend build:

```bash
cd frontend
npm run build
```

## Production Notes

- Serve the FastAPI app behind a production ASGI server.
- Serve the frontend static build from a CDN or static host.
- Keep the deployed frontend origin in `APP_CORS_ORIGINS`; the production CloudFront origin is always included by the backend.
- Configure the frontend `VITE_API_BASE_URL` to the production backend base URL.
- Store LLM credentials as secrets.
- This POC does not include authentication, authorization, audit logging, or PHI-grade compliance controls.
