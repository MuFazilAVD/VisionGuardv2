import { useEffect, useState } from "react";

import { Layout } from "./components/Layout";
import ClaimWorkspace from "./pages/ClaimWorkspace";
import { getSampleData, retrainAssessmentEngine } from "./services/api";
import type { SampleDataResponse, TrainingResponse } from "./types/api";

export default function App() {
  console.info("[VisionGuard] App rendered");
  const [sampleData, setSampleData] = useState<SampleDataResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [syncing, setSyncing] = useState(false);

  const refreshSamples = async () => {
    console.info("[VisionGuard] Refreshing sample datasets");
    const samples = await getSampleData();
    setSampleData(samples);
    console.info("[VisionGuard] Sample datasets refreshed");
  };

  const syncEngine = async (): Promise<TrainingResponse> => {
    console.info("[VisionGuard] Sync engine requested");
    setSyncing(true);
    try {
      const response = await retrainAssessmentEngine();
      await refreshSamples();
      console.info("[VisionGuard] Sync engine completed");
      return response;
    } finally {
      console.info("[VisionGuard] Sync engine state cleared");
      setSyncing(false);
    }
  };

  useEffect(() => {
    console.info("[VisionGuard] Initial sample data load started");
    refreshSamples()
      .catch((error) => {
        console.info("[VisionGuard] Initial sample data load failed", error);
      })
      .finally(() => {
        console.info("[VisionGuard] Initial sample data load finished");
        setLoading(false);
      });
  }, []);

  return (
    <Layout>
      <ClaimWorkspace
        loading={loading}
        sampleData={sampleData}
        syncing={syncing}
        onSync={syncEngine}
      />
    </Layout>
  );
}
