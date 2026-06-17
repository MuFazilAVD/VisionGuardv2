import {
  ArrowsClockwise,
  ChartLineUp,
  CheckCircle,
  ClockClockwise,
  Database,
  SealCheck,
  ShieldCheck,
  Tag,
  WarningCircle
} from "@phosphor-icons/react";
import { useState } from "react";

import { MetricCard } from "../components/MetricCard";
import { Button } from "../components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "../components/ui/card";
import { retrainAssessmentEngine } from "../services/api";
import type { TrainingResponse, TrainingStatus } from "../types/api";

export default function Retraining({
  trainingStatus,
  onRefresh
}: {
  trainingStatus: TrainingStatus | null;
  onRefresh: () => Promise<void>;
}) {
  const [busy, setBusy] = useState(false);
  const [result, setResult] = useState<TrainingResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  const runRetraining = async () => {
    setBusy(true);
    setError(null);
    try {
      const response = await retrainAssessmentEngine();
      setResult(response);
      await onRefresh();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Refresh failed.");
    } finally {
      setBusy(false);
    }
  };

  const metrics = result?.metrics || trainingStatus?.metrics || {};
  const validationQuality = typeof metrics.accuracy === "number" ? `${Math.round(metrics.accuracy * 100)}%` : "-";
  const recordsUsed = Number(metrics.train_records || 0) + Number(metrics.test_records || 0);

  return (
    <div className="space-y-4">
      <section className="rounded-lg border border-slate-950/20 bg-[#10151f] p-4 text-white shadow-panel">
        <p className="text-sm font-semibold text-blue-200">Retraining</p>
        <h2 className="mt-1 text-2xl font-semibold text-white">Refresh Assessment Engine</h2>
        <p className="mt-1 max-w-3xl text-sm text-slate-300">
          Refresh the assessment engine using the generated historical claim set and editable rule workbook.
        </p>
      </section>

      <Card className="border-t-4 border-t-action">
        <CardHeader>
          <CardTitle>Refresh Assessment Engine</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
            <div className="flex items-start gap-3">
              <span
                className={`flex size-10 shrink-0 items-center justify-center rounded-lg border ${
                  busy
                    ? "border-sky-200 bg-sky-50 text-info"
                    : trainingStatus?.trained
                      ? "border-green-200 bg-green-50 text-success"
                      : "border-amber-200 bg-amber-50 text-warning"
                }`}
                aria-hidden="true"
              >
                {busy ? (
                  <ArrowsClockwise className="animate-spin" size={20} weight="bold" />
                ) : trainingStatus?.trained ? (
                  <ShieldCheck size={20} weight="duotone" />
                ) : (
                  <WarningCircle size={20} weight="duotone" />
                )}
              </span>
              <div>
              <p className="text-sm font-medium text-ink">
                {busy ? "Refresh is running" : trainingStatus?.trained ? "Engine is ready" : "Engine needs refresh"}
              </p>
              <p className="mt-1 text-sm text-muted">
                Last refresh:{" "}
                {trainingStatus?.last_training_date
                  ? new Date(trainingStatus.last_training_date).toLocaleString()
                  : "Not available"}
              </p>
              </div>
            </div>
            <Button
              disabled={busy}
              icon={busy ? <ArrowsClockwise className="animate-spin" size={17} weight="bold" /> : <ArrowsClockwise size={17} weight="bold" />}
              onClick={runRetraining}
            >
              {busy ? "Refreshing" : "Refresh Now"}
            </Button>
          </div>
          {error ? (
            <p className="flex items-start gap-2 rounded-lg border border-red-200 bg-red-50 p-3 text-sm text-danger">
              <WarningCircle className="mt-0.5 shrink-0" size={17} weight="fill" aria-hidden="true" />
              {error}
            </p>
          ) : null}
          {result ? (
            <p className="flex items-center gap-2 rounded-lg border border-green-200 bg-green-50 p-3 text-sm text-success">
              <CheckCircle size={17} weight="fill" aria-hidden="true" />
              Refresh completed successfully.
            </p>
          ) : null}
        </CardContent>
      </Card>

      <section className="grid gap-3 md:grid-cols-3">
        <MetricCard
          label="Validation Quality"
          value={validationQuality}
          detail="Latest refresh check"
          icon={validationQuality === "-" ? <ClockClockwise size={22} weight="duotone" /> : <SealCheck size={22} weight="duotone" />}
          tone={validationQuality === "-" ? "neutral" : "success"}
        />
        <MetricCard
          label="Historical Records Used"
          value={recordsUsed ? recordsUsed.toLocaleString() : "-"}
          detail="Training and test records"
          icon={<Database size={22} weight="duotone" />}
          tone="accent"
        />
        <MetricCard
          label="Assessment Version"
          value={result?.artifact_version || trainingStatus?.artifact_version || "-"}
          detail="Current deployed artifact"
          icon={(result?.artifact_version || trainingStatus?.artifact_version) ? <Tag size={22} weight="duotone" /> : <ChartLineUp size={22} weight="duotone" />}
          tone="info"
        />
      </section>
    </div>
  );
}
