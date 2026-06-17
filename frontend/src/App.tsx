import { useEffect, useState } from "react";

import { Layout } from "./components/Layout";
import ClaimWorkspace from "./pages/ClaimWorkspace";
import { getSampleData, retrainAssessmentEngine } from "./services/api";
import type { SampleDataResponse, TrainingResponse } from "./types/api";

export default function App() {
  const [sampleData, setSampleData] = useState<SampleDataResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [syncing, setSyncing] = useState(false);

  const refreshSamples = async () => {
    const samples = await getSampleData();
    setSampleData(samples);
  };

  const syncEngine = async (): Promise<TrainingResponse> => {
    setSyncing(true);
    try {
      const response = await retrainAssessmentEngine();
      await refreshSamples();
      return response;
    } finally {
      setSyncing(false);
    }
  };

  useEffect(() => {
    refreshSamples()
      .catch(() => undefined)
      .finally(() => setLoading(false));
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
