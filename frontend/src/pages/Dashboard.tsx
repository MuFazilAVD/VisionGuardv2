import {
  ArrowsClockwise,
  Article,
  ChartLineUp,
  ClipboardText,
  Database,
  FileCsv,
  Pulse,
  ShieldCheck,
  WarningCircle
} from "@phosphor-icons/react";
import type { ReactNode } from "react";

import { MetricCard } from "../components/MetricCard";
import type { ViewName } from "../components/Layout";
import { Button } from "../components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "../components/ui/card";
import type { SampleDataResponse, TrainingStatus } from "../types/api";

export default function Dashboard({
  loading,
  sampleData,
  trainingStatus,
  onNavigate
}: {
  loading: boolean;
  sampleData: SampleDataResponse | null;
  trainingStatus: TrainingStatus | null;
  onNavigate: (view: ViewName) => void;
}) {
  const lastRefresh = trainingStatus?.last_training_date
    ? new Date(trainingStatus.last_training_date).toLocaleString()
    : "Not refreshed yet";
  const engineTone = loading ? "info" : trainingStatus?.trained ? "success" : "warning";

  return (
    <div className="space-y-4">
      <section className="overflow-hidden rounded-lg border border-slate-950/20 bg-[#10151f] p-4 text-white shadow-panel">
        <div className="flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
        <div>
            <p className="text-sm font-semibold text-blue-200">Operational Overview</p>
            <h2 className="mt-1 text-2xl font-semibold text-white">Claims Review Command Center</h2>
            <p className="mt-1 max-w-3xl text-sm text-slate-300">
            Readiness, evidence quality, and claim review actions are grouped for fast analyst decisions.
          </p>
        </div>
        <div className="flex flex-wrap gap-2">
            <Button
              variant="secondary"
              className="border-white/15 bg-white/10 text-white hover:bg-white/15"
              icon={<ArrowsClockwise size={17} weight="bold" />}
              onClick={() => onNavigate("retraining")}
            >
            Refresh Engine
          </Button>
          <Button icon={<ClipboardText size={17} weight="bold" />} onClick={() => onNavigate("review")}>
            Review Claims
          </Button>
        </div>
        </div>
      </section>

      <section className="grid gap-3 md:grid-cols-2 xl:grid-cols-4">
        <MetricCard
          label="Assessment Engine"
          value={loading ? "Checking" : trainingStatus?.trained ? "Ready" : "Needs Refresh"}
          detail={`Last refresh: ${lastRefresh}`}
          icon={loading ? <Pulse size={22} weight="duotone" /> : trainingStatus?.trained ? <ShieldCheck size={22} weight="duotone" /> : <WarningCircle size={22} weight="duotone" />}
          tone={engineTone}
        />
        <MetricCard
          label="Historical Claims"
          value={sampleData?.historical_claims.record_count.toLocaleString() || "-"}
          detail="Available for retraining"
          icon={<Database size={22} weight="duotone" />}
          tone="accent"
        />
        <MetricCard
          label="Editable Rules"
          value={sampleData?.rules.record_count || "-"}
          detail="Business-maintained indicators"
          icon={<FileCsv size={22} weight="duotone" />}
          tone="info"
        />
        <MetricCard
          label="Recent Processing"
          value={sampleData?.realtime_claims.record_count || "-"}
          detail="Sample incoming claims"
          icon={<ChartLineUp size={22} weight="duotone" />}
          tone="action"
        />
      </section>

      <Card>
        <CardHeader>
          <CardTitle>Current Readiness Signals</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid gap-3 lg:grid-cols-3">
            <SignalPanel
              title="Data"
              detail="Historical claims and editable rule definitions are available for controlled refreshes."
              icon={<Database size={20} weight="duotone" />}
              tone="accent"
            />
            <SignalPanel
              title="Assessment"
              detail="Claim indicators, known review patterns, and billing consistency are evaluated together."
              icon={<Pulse size={20} weight="duotone" />}
              tone="info"
            />
            <SignalPanel
              title="Narrative"
              detail="Investigation summaries stay paired with recommended analyst actions."
              icon={<Article size={20} weight="duotone" />}
              tone="action"
            />
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

function SignalPanel({
  title,
  detail,
  icon,
  tone
}: {
  title: string;
  detail: string;
  icon: ReactNode;
  tone: "action" | "info" | "accent";
}) {
  const toneStyles = {
    action: "border-blue-200 bg-blue-50 text-action",
    info: "border-sky-200 bg-sky-50 text-info",
    accent: "border-teal-200 bg-teal-50 text-accent"
  };
  const toneBorders = {
    action: "border-l-4 border-l-action",
    info: "border-l-4 border-l-info",
    accent: "border-l-4 border-l-accent"
  };

  return (
    <div className={`rounded-lg border border-line bg-white p-3 shadow-sm ${toneBorders[tone]}`}>
      <div className="flex items-center gap-3">
        <span className={`flex size-9 items-center justify-center rounded-lg border ${toneStyles[tone]}`} aria-hidden="true">
          {icon}
        </span>
        <p className="text-sm font-semibold text-ink">{title}</p>
      </div>
      <p className="mt-2 text-sm leading-6 text-muted">{detail}</p>
    </div>
  );
}
