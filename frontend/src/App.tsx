import { useEffect, useState } from "react";

import { Layout, type ViewName } from "./components/Layout";
import Dashboard from "./pages/Dashboard";
import ClaimReview from "./pages/ClaimReview";
import Results from "./pages/Results";
import Retraining from "./pages/Retraining";
import { getSampleData, getTrainingStatus } from "./services/api";
import type { AnalyzeResponse, SampleDataResponse, TrainingStatus } from "./types/api";

export default function App() {
  const [activeView, setActiveView] = useState<ViewName>("dashboard");
  const [trainingStatus, setTrainingStatus] = useState<TrainingStatus | null>(null);
  const [sampleData, setSampleData] = useState<SampleDataResponse | null>(null);
  const [analysis, setAnalysis] = useState<AnalyzeResponse | null>(null);
  const [loading, setLoading] = useState(true);

  const refreshStatus = async () => {
    const [status, samples] = await Promise.all([getTrainingStatus(), getSampleData()]);
    setTrainingStatus(status);
    setSampleData(samples);
  };

  useEffect(() => {
    refreshStatus()
      .catch(() => undefined)
      .finally(() => setLoading(false));
  }, []);

  return (
    <Layout activeView={activeView} onChangeView={setActiveView}>
      {activeView === "dashboard" ? (
        <Dashboard
          loading={loading}
          sampleData={sampleData}
          trainingStatus={trainingStatus}
          onNavigate={setActiveView}
        />
      ) : null}
      {activeView === "retraining" ? (
        <Retraining
          trainingStatus={trainingStatus}
          onRefresh={async () => {
            await refreshStatus();
          }}
        />
      ) : null}
      {activeView === "review" ? (
        <ClaimReview
          sampleData={sampleData}
          onAnalysis={(result) => {
            setAnalysis(result);
            setActiveView("results");
          }}
        />
      ) : null}
      {activeView === "results" ? <Results analysis={analysis} onNavigate={setActiveView} /> : null}
    </Layout>
  );
}

