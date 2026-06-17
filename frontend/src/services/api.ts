import type {
  AnalyzeResponse,
  ClaimRecord,
  SampleDataResponse,
  TrainingResponse,
  TrainingStatus
} from "../types/api";

const API_BASE =
  import.meta.env.VITE_API_BASE_URL ||
  (import.meta.env.PROD ? "https://d2brdeqy144bwg.cloudfront.net" : "http://localhost:8000");

async function requestJson<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, {
    ...init,
    headers: {
      ...(init?.body instanceof FormData ? {} : { "Content-Type": "application/json" }),
      ...(init?.headers || {})
    }
  });

  if (!response.ok) {
    const text = await response.text();
    throw new Error(text || `Request failed with status ${response.status}`);
  }
  return response.json() as Promise<T>;
}

export function getTrainingStatus() {
  return requestJson<TrainingStatus>("/api/training/status");
}

export function retrainAssessmentEngine() {
  return requestJson<TrainingResponse>("/api/training/retrain", { method: "POST" });
}

export function getSampleData() {
  return requestJson<SampleDataResponse>("/api/sample-data");
}

export function analyzeClaims(claims: ClaimRecord[]) {
  return requestJson<AnalyzeResponse>("/api/claims/analyze", {
    method: "POST",
    body: JSON.stringify({ claims })
  });
}
