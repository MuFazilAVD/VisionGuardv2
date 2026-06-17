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
const API_PREFIX = "/visionguardv2/api";

async function requestJson<T>(path: string, init?: RequestInit): Promise<T> {
  const method = init?.method || "GET";
  console.info(`[VisionGuard] API request started: ${method} ${path}`);
  const response = await fetch(`${API_BASE}${path}`, {
    ...init,
    headers: {
      ...(init?.body instanceof FormData ? {} : { "Content-Type": "application/json" }),
      ...(init?.headers || {})
    }
  });

  if (!response.ok) {
    const text = await response.text();
    console.info(`[VisionGuard] API request failed: ${method} ${path} status=${response.status}`);
    throw new Error(text || `Request failed with status ${response.status}`);
  }
  console.info(`[VisionGuard] API request completed: ${method} ${path} status=${response.status}`);
  return response.json() as Promise<T>;
}

export function getTrainingStatus() {
  console.info("[VisionGuard] Loading training status");
  return requestJson<TrainingStatus>(`${API_PREFIX}/training/status`);
}

export function retrainAssessmentEngine() {
  console.info("[VisionGuard] Starting assessment engine retrain");
  return requestJson<TrainingResponse>(`${API_PREFIX}/training/retrain`, { method: "POST" });
}

export function getSampleData() {
  console.info("[VisionGuard] Loading sample data");
  return requestJson<SampleDataResponse>(`${API_PREFIX}/sample-data`);
}

export function analyzeClaims(claims: ClaimRecord[]) {
  console.info(`[VisionGuard] Analyzing ${claims.length} claim(s)`);
  return requestJson<AnalyzeResponse>(`${API_PREFIX}/claims/analyze`, {
    method: "POST",
    body: JSON.stringify({ claims })
  });
}
