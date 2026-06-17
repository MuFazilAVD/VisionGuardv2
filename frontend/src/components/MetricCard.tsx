import type { ReactNode } from "react";

import { Card, CardContent } from "./ui/card";

type MetricTone = "neutral" | "action" | "info" | "success" | "warning" | "danger" | "accent";

const toneStyles: Record<MetricTone, string> = {
  neutral: "border-slate-200 bg-slate-50 text-muted",
  action: "border-blue-200 bg-blue-50 text-action",
  info: "border-sky-200 bg-sky-50 text-info",
  success: "border-green-200 bg-green-50 text-success",
  warning: "border-amber-200 bg-amber-50 text-warning",
  danger: "border-red-200 bg-red-50 text-danger",
  accent: "border-teal-200 bg-teal-50 text-accent"
};

const toneBars: Record<MetricTone, string> = {
  neutral: "bg-slate-400",
  action: "bg-action",
  info: "bg-info",
  success: "bg-success",
  warning: "bg-warning",
  danger: "bg-danger",
  accent: "bg-accent"
};

export function MetricCard({
  label,
  value,
  detail,
  icon,
  tone = "neutral"
}: {
  label: string;
  value: ReactNode;
  detail?: string;
  icon?: ReactNode;
  tone?: MetricTone;
}) {
  return (
    <Card className="group relative min-h-28 transition hover:-translate-y-0.5 hover:shadow-lift">
      <div className={`h-1.5 w-full ${toneBars[tone]}`} />
      <CardContent className="flex h-full items-start justify-between gap-3">
        <div className="min-w-0">
          <p className="text-xs font-semibold uppercase text-muted">{label}</p>
          <div className="mt-1.5 break-words text-2xl font-semibold text-ink">{value}</div>
          {detail ? <p className="mt-1.5 text-sm text-muted">{detail}</p> : null}
        </div>
        {icon ? (
          <div className={`rounded-lg border p-2.5 shadow-sm ${toneStyles[tone]} [&>svg]:shrink-0`} aria-hidden="true">
            {icon}
          </div>
        ) : null}
      </CardContent>
    </Card>
  );
}
