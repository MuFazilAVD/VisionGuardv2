import { CheckCircle, Warning, WarningOctagon } from "@phosphor-icons/react";

import { Badge } from "./ui/badge";

const riskConfig: Record<string, { className: string; icon: typeof CheckCircle }> = {
  High: { className: "border-red-200 bg-red-50 text-danger", icon: WarningOctagon },
  Medium: { className: "border-amber-200 bg-amber-50 text-warning", icon: Warning },
  Low: { className: "border-green-200 bg-green-50 text-success", icon: CheckCircle }
};

export function RiskBadge({ level }: { level: string }) {
  const config = riskConfig[level] || { className: "border-line bg-slate-50 text-muted", icon: Warning };
  const Icon = config.icon;

  return (
    <Badge className={config.className}>
      <Icon size={14} weight="fill" aria-hidden="true" />
      {level}
    </Badge>
  );
}
