import {
  ArrowLeft,
  CheckCircle,
  ClipboardText,
  Fingerprint,
  Gauge,
  ListChecks,
  SealCheck,
  ShieldWarning,
  Target,
  WarningCircle
} from "@phosphor-icons/react";
import type { ReactNode } from "react";

import { RiskBadge } from "../components/RiskBadge";
import type { ViewName } from "../components/Layout";
import { Button } from "../components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "../components/ui/card";
import { Table, TBody, TD, TH, THead, TR } from "../components/ui/table";
import type { AnalyzeResponse } from "../types/api";

export default function Results({
  analysis,
  onNavigate
}: {
  analysis: AnalyzeResponse | null;
  onNavigate: (view: ViewName) => void;
}) {
  if (!analysis) {
    return (
      <Card className="border-t-4 border-t-info">
        <CardContent className="flex flex-col items-start gap-4 sm:flex-row sm:items-center sm:justify-between">
          <div className="flex items-start gap-3">
            <span className="flex size-10 shrink-0 items-center justify-center rounded-lg border border-sky-200 bg-sky-50 text-info">
              <ClipboardText size={21} weight="duotone" aria-hidden="true" />
            </span>
            <div>
              <h2 className="text-xl font-semibold text-ink">No Results Yet</h2>
              <p className="mt-1 text-sm text-muted">Run a claim assessment to view investigation summaries.</p>
            </div>
          </div>
          <Button icon={<ArrowLeft size={17} weight="bold" />} onClick={() => onNavigate("review")}>
            Go To Claim Review
          </Button>
        </CardContent>
      </Card>
    );
  }

  return (
    <div className="space-y-4">
      <section className="rounded-lg border border-slate-950/20 bg-[#10151f] p-4 text-white shadow-panel">
        <div className="flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
        <div>
            <p className="text-sm font-semibold text-blue-200">Assessment Results</p>
            <h2 className="mt-1 text-2xl font-semibold text-white">Investigation Summary</h2>
            <p className="mt-1 text-sm text-slate-300">
            Processed {analysis.count} claim{analysis.count === 1 ? "" : "s"} at{" "}
            {new Date(analysis.processed_at).toLocaleString()}.
          </p>
        </div>
          <Button
            variant="secondary"
            className="border-white/15 bg-white/10 text-white hover:bg-white/15"
            icon={<ArrowLeft size={17} weight="bold" />}
            onClick={() => onNavigate("review")}
          >
          Review More Claims
        </Button>
        </div>
      </section>

      <div className="space-y-4">
        {analysis.assessments.map((assessment) => (
          <Card key={`${assessment.claim_id}-${assessment.line_number}`} className={`border-t-4 ${riskBorder(assessment.risk_level)}`}>
            <CardHeader className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
              <div>
                <CardTitle>
                  Claim {assessment.claim_id} - Line {assessment.line_number}
                </CardTitle>
                <p className="mt-1 text-sm text-muted">
                  {assessment.procedure_code} {assessment.procedure_name}
                </p>
              </div>
              <RiskBadge level={assessment.risk_level} />
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid gap-2 md:grid-cols-4">
                <SummaryStat
                  label="Risk Score"
                  value={`${Math.round(assessment.final_risk_score * 100)}%`}
                  icon={<Gauge size={19} weight="duotone" />}
                  tone={assessment.risk_level === "High" ? "danger" : assessment.risk_level === "Medium" ? "warning" : "success"}
                />
                <SummaryStat
                  label="Confidence Level"
                  value={`${Math.round(assessment.confidence_level * 100)}%`}
                  icon={<SealCheck size={19} weight="duotone" />}
                  tone="info"
                />
                <SummaryStat
                  label="Risk Indicators"
                  value={assessment.rule_flag_count.toString()}
                  icon={<ShieldWarning size={19} weight="duotone" />}
                  tone={assessment.rule_flag_count > 0 ? "warning" : "success"}
                />
                <SummaryStat
                  label="Review Pattern"
                  value={assessment.predicted_pattern}
                  icon={<Fingerprint size={19} weight="duotone" />}
                  tone="accent"
                />
              </div>

              <section className="rounded-lg border border-sky-200 bg-sky-50/80 p-4">
                <h3 className="flex items-center gap-2 text-sm font-semibold text-ink">
                  <ClipboardText size={17} weight="duotone" aria-hidden="true" />
                  Executive Summary
                </h3>
                <p className="mt-2 text-sm leading-6 text-ink">{assessment.narrative.executive_summary}</p>
              </section>

              <div className="grid gap-3 lg:grid-cols-3">
                <ResultList title="Investigation Findings" items={assessment.narrative.investigation_findings} />
                <ResultList title="Key Risk Indicators" items={assessment.narrative.key_risk_indicators} />
                <ResultList title="Review Recommendations" items={assessment.narrative.recommended_review_actions} />
              </div>

              <section className="overflow-x-auto">
                <Table className="min-w-[720px]">
                  <THead>
                    <TR>
                      <TH>Indicator</TH>
                      <TH>Severity</TH>
                      <TH>Category</TH>
                      <TH>Description</TH>
                    </TR>
                  </THead>
                  <TBody>
                    {assessment.triggered_indicators.length ? (
                      assessment.triggered_indicators.map((indicator) => (
                        <TR key={indicator.rule_id}>
                          <TD className="font-medium text-ink">{indicator.name}</TD>
                          <TD>
                            <RiskBadge level={indicator.severity} />
                          </TD>
                          <TD>{indicator.category}</TD>
                          <TD className="text-muted">{indicator.description}</TD>
                        </TR>
                      ))
                    ) : (
                      <TR>
                        <TD colSpan={4} className="text-muted">
                          No rule-based indicators were triggered.
                        </TD>
                      </TR>
                    )}
                  </TBody>
                </Table>
              </section>

              <section className="rounded-lg border border-line bg-slate-50/80 p-4">
                <h3 className="flex items-center gap-2 text-sm font-semibold text-ink">
                  <Target size={17} weight="duotone" aria-hidden="true" />
                  Detailed Claim Assessment
                </h3>
                <dl className="mt-3 grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
                  <Detail label="Provider" value={assessment.provider_npi} />
                  <Detail label="Category" value={assessment.category} />
                  <Detail label="Top Reason" value={assessment.top_reason} />
                  <Detail label="Recommended Action" value={assessment.recommended_action} />
                </dl>
              </section>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  );
}

function SummaryStat({
  label,
  value,
  icon,
  tone
}: {
  label: string;
  value: string;
  icon: ReactNode;
  tone: "success" | "warning" | "danger" | "info" | "accent";
}) {
  const toneStyles = {
    success: "border-green-200 bg-green-50 text-success",
    warning: "border-amber-200 bg-amber-50 text-warning",
    danger: "border-red-200 bg-red-50 text-danger",
    info: "border-sky-200 bg-sky-50 text-info",
    accent: "border-teal-200 bg-teal-50 text-accent"
  };

  return (
    <div className="min-h-24 rounded-lg border border-line bg-white p-3 shadow-sm">
      <div className="flex items-center gap-2">
        <span className={`flex size-8 items-center justify-center rounded-lg border ${toneStyles[tone]}`} aria-hidden="true">
          {icon}
        </span>
        <p className="text-sm text-muted">{label}</p>
      </div>
      <p className="mt-2 break-words text-lg font-semibold text-ink">{value}</p>
    </div>
  );
}

function ResultList({ title, items }: { title: string; items: string[] }) {
  return (
    <section className="rounded-lg border border-line bg-white p-3 shadow-sm">
      <h3 className="text-sm font-semibold text-ink">{title}</h3>
      <ul className="mt-3 space-y-2 text-sm text-muted">
        {items.map((item, index) => (
          <li key={`${title}-${index}`} className="flex gap-2 leading-6">
            {title === "Key Risk Indicators" ? (
              <WarningCircle className="mt-1 shrink-0 text-warning" size={14} weight="fill" aria-hidden="true" />
            ) : title === "Review Recommendations" ? (
              <ListChecks className="mt-1 shrink-0 text-action" size={14} weight="fill" aria-hidden="true" />
            ) : (
              <CheckCircle className="mt-1 shrink-0 text-success" size={14} weight="fill" aria-hidden="true" />
            )}
            <span>{item}</span>
          </li>
        ))}
      </ul>
    </section>
  );
}

function riskBorder(level: string) {
  if (level === "High") return "border-t-danger";
  if (level === "Medium") return "border-t-warning";
  if (level === "Low") return "border-t-success";
  return "border-t-info";
}

function Detail({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <dt className="text-xs font-semibold uppercase text-muted">{label}</dt>
      <dd className="mt-1 break-words text-sm text-ink">{value}</dd>
    </div>
  );
}
