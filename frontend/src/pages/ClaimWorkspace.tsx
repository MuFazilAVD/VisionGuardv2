import {
  ArrowsClockwise,
  CaretDown,
  CaretUp,
  ChartLineUp,
  CheckCircle,
  ClipboardText,
  Fingerprint,
  Gauge,
  ListChecks,
  Plus,
  SealCheck,
  ShieldWarning,
  Target,
  Trash,
  UploadSimple,
  WarningCircle
} from "@phosphor-icons/react";
import { useEffect, useRef, useState } from "react";
import type { ReactNode } from "react";

import { RiskBadge } from "../components/RiskBadge";
import { Button } from "../components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "../components/ui/card";
import { Input } from "../components/ui/input";
import { Table, TBody, TD, TH, THead, TR } from "../components/ui/table";
import { analyzeClaims } from "../services/api";
import type {
  AnalyzeResponse,
  BatchSummary,
  ClaimRecord,
  SampleDataResponse,
  TrainingResponse
} from "../types/api";

const editableColumns = [
  "ClaimId",
  "MemberId",
  "Gender",
  "Age",
  "ServiceDateFrom",
  "PlaceOfService",
  "LineNumber",
  "ProcedureCode",
  "ProcedureName",
  "Modifier",
  "Modifier2",
  "Modifier3",
  "Primary_Diagnosis_Pointer",
  "Primary_Diagnosis",
  "LONG_DESCRIPTION",
  "ClaimLineTotalPaid",
  "AmtCharged",
  "AllowedUnits",
  "AmtDisallowed",
  "AmtEligible",
  "AmtCopay",
  "AmtCoinsurance",
  "AmtDeductible",
  "ProviderNPI",
  "GroupId",
  "GroupNumber",
  "LOB",
  "CoverageCode",
  "State"
];

type ClaimWorkspaceProps = {
  loading: boolean;
  sampleData: SampleDataResponse | null;
  syncing: boolean;
  onSync: () => Promise<TrainingResponse>;
};

type ProcedureProfile = {
  code: string;
  name: string;
  category: "exam" | "material" | "medical";
  eligibleRange: [number, number];
};

type DiagnosisProfile = {
  code: string;
  description: string;
  category: "vision" | "medical";
  ageRange: [number, number];
};

const procedureProfiles: ProcedureProfile[] = [
  { code: "92002", name: "Intermediate Eye Exam New Patient", category: "exam", eligibleRange: [85, 145] },
  { code: "92004", name: "Comprehensive Eye Exam New Patient", category: "exam", eligibleRange: [140, 260] },
  { code: "92012", name: "Intermediate Eye Exam Established Patient", category: "exam", eligibleRange: [75, 135] },
  { code: "92014", name: "Comprehensive Eye Exam", category: "exam", eligibleRange: [115, 220] },
  { code: "S0620", name: "Routine Ophthalmological Examination New Patient", category: "exam", eligibleRange: [90, 180] },
  { code: "S0621", name: "Routine Ophthalmological Examination Established Patient", category: "exam", eligibleRange: [80, 160] },
  { code: "V2020", name: "Frames", category: "material", eligibleRange: [45, 280] },
  { code: "V2100", name: "Single Vision Lenses", category: "material", eligibleRange: [55, 180] },
  { code: "V2200", name: "Bifocal Lenses", category: "material", eligibleRange: [80, 240] },
  { code: "V2300", name: "Trifocal Lenses", category: "material", eligibleRange: [110, 320] },
  { code: "V2750", name: "Anti-Reflective Coating", category: "material", eligibleRange: [35, 110] },
  { code: "V2755", name: "UV Coating", category: "material", eligibleRange: [20, 70] },
  { code: "V2760", name: "Scratch Resistant Coating", category: "material", eligibleRange: [15, 65] },
  { code: "99213", name: "Office Visit Established Patient", category: "medical", eligibleRange: [90, 210] },
  { code: "80050", name: "General Health Panel", category: "medical", eligibleRange: [65, 190] },
  { code: "93000", name: "Electrocardiogram", category: "medical", eligibleRange: [45, 160] }
];

const diagnosisProfiles: DiagnosisProfile[] = [
  { code: "H52.4", description: "Presbyopia", category: "vision", ageRange: [40, 90] },
  { code: "H52.13", description: "Myopia, bilateral", category: "vision", ageRange: [12, 80] },
  { code: "H52.03", description: "Hypermetropia, bilateral", category: "vision", ageRange: [8, 85] },
  { code: "H25.13", description: "Age-related nuclear cataract, bilateral", category: "vision", ageRange: [55, 92] },
  { code: "H40.003", description: "Glaucoma suspect, bilateral", category: "vision", ageRange: [30, 90] },
  { code: "E11.9", description: "Type 2 diabetes mellitus without complications", category: "medical", ageRange: [35, 90] },
  { code: "I10", description: "Essential hypertension", category: "medical", ageRange: [30, 92] },
  { code: "J02.9", description: "Acute pharyngitis, unspecified", category: "medical", ageRange: [8, 75] },
  { code: "Z00.00", description: "General adult medical examination", category: "medical", ageRange: [18, 85] }
];

const coverageProfiles = [
  { lob: "COMM", coverageCodes: ["PPO", "HMO", "EPO", "VSP"] },
  { lob: "MEDICARE", coverageCodes: ["PPO", "HMO"] },
  { lob: "MEDICAID", coverageCodes: ["HMO", "EPO"] }
];

const claimStates = ["AZ", "CA", "FL", "GA", "IL", "NC", "NY", "OH", "PA", "TX"];
const placesOfService = ["11", "22", "24", "49", "50", "81"];

function blankClaim(existingClaims: ClaimRecord[]): ClaimRecord {
  const procedure = chooseUnusedProfile(
    procedureProfiles,
    new Set(existingClaims.map((claim) => String(claim.ProcedureCode ?? "").trim())),
    (profile) => profile.code
  );
  const diagnosisCategory = procedure.category === "medical" ? "medical" : "vision";
  const matchingDiagnoses = diagnosisProfiles.filter((diagnosis) => diagnosis.category === diagnosisCategory);
  const diagnosis = chooseUnusedProfile(
    matchingDiagnoses,
    new Set(existingClaims.map((claim) => String(claim.Primary_Diagnosis ?? "").trim())),
    (profile) => profile.code
  );
  const coverageProfile = randomChoice(coverageProfiles);
  const eligible = randomMoney(...procedure.eligibleRange);
  const charged = roundMoney(eligible * randomBetween(0.9, 2.7));
  const copay = randomChoice([0, 5, 10, 15, 20, 25, 30, 40]);
  const coinsurance = randomChoice([0, 0, 5, 10, 15, 20]);
  const deductible = randomChoice([0, 0, 10, 25, 50, 75]);
  const units =
    procedure.category === "exam"
      ? Math.random() < 0.25
        ? randomInteger(2, 4)
        : 1
      : randomInteger(1, procedure.category === "material" ? 4 : 3);

  return {
    ClaimId: nextIdentifier(existingClaims, "ClaimId", "RT"),
    MemberId: nextIdentifier(existingClaims, "MemberId", "MEM"),
    Gender: Math.random() < 0.5 ? "M" : "F",
    Age: randomInteger(...diagnosis.ageRange),
    ServiceDateFrom: nextServiceDate(existingClaims),
    PlaceOfService: randomChoice(placesOfService),
    LineNumber: 1,
    ProcedureCode: procedure.code,
    ProcedureName: procedure.name,
    Modifier: randomModifier(procedure.category),
    Modifier2: "",
    Modifier3: "",
    Primary_Diagnosis_Pointer: "1",
    Primary_Diagnosis: diagnosis.code,
    LONG_DESCRIPTION: diagnosis.description,
    ClaimLineTotalPaid: roundMoney(Math.max(eligible - copay - coinsurance - deductible, 0)),
    AmtCharged: charged,
    AllowedUnits: units,
    AmtDisallowed: roundMoney(Math.max(charged - eligible, 0)),
    AmtEligible: eligible,
    AmtCopay: copay,
    AmtCoinsurance: coinsurance,
    AmtDeductible: deductible,
    ProviderNPI: uniqueGeneratedValue(existingClaims, "ProviderNPI", () => randomDigits(10)),
    GroupId: uniqueGeneratedValue(existingClaims, "GroupId", () => `G${randomInteger(10, 999)}`),
    GroupNumber: uniqueGeneratedValue(existingClaims, "GroupNumber", () => `GRP${randomInteger(100, 9999)}`),
    LOB: coverageProfile.lob,
    CoverageCode: randomChoice(coverageProfile.coverageCodes),
    State: randomChoice(claimStates)
  };
}

function chooseUnusedProfile<T>(
  profiles: readonly T[],
  usedValues: Set<string>,
  valueForProfile: (profile: T) => string
) {
  const unusedProfiles = profiles.filter((profile) => !usedValues.has(valueForProfile(profile)));
  return randomChoice(unusedProfiles.length ? unusedProfiles : profiles);
}

function randomModifier(category: ProcedureProfile["category"]) {
  if (category === "exam") return randomChoice(["", "", "", "25", "59"]);
  if (category === "material") return randomChoice(["", "", "", "50", "59"]);
  return randomChoice(["", "", "", "25"]);
}

function uniqueGeneratedValue(
  existingClaims: ClaimRecord[],
  field: "ProviderNPI" | "GroupId" | "GroupNumber",
  generate: () => string
) {
  const existingValues = new Set(existingClaims.map((claim) => String(claim[field] ?? "").trim()));

  for (let attempt = 0; attempt < 100; attempt += 1) {
    const candidate = generate();
    if (!existingValues.has(candidate)) return candidate;
  }

  return generate();
}

function randomChoice<T>(values: readonly T[]): T {
  return values[Math.floor(Math.random() * values.length)];
}

function randomInteger(min: number, max: number) {
  return Math.floor(randomBetween(min, max + 1));
}

function randomBetween(min: number, max: number) {
  return min + Math.random() * (max - min);
}

function randomMoney(min: number, max: number) {
  return roundMoney(randomBetween(min, max));
}

function roundMoney(value: number) {
  return Math.round(value * 100) / 100;
}

function randomDigits(length: number) {
  let value = String(randomInteger(1, 9));
  while (value.length < length) value += String(randomInteger(0, 9));
  return value;
}

function nextIdentifier(
  existingClaims: ClaimRecord[],
  field: "ClaimId" | "MemberId",
  fallbackPrefix: string
) {
  const sequences = new Map<
    string,
    { prefix: string; width: number; values: number[]; occurrences: number; lastIndex: number }
  >();

  existingClaims.forEach((claim, index) => {
    const value = String(claim[field] ?? "").trim();
    const match = value.match(/^(.*?)(\d+)$/);
    if (!match) return;

    const prefix = match[1];
    const numericPart = match[2];
    const key = `${prefix}\u0000${numericPart.length}`;
    const sequence = sequences.get(key) ?? {
      prefix,
      width: numericPart.length,
      values: [],
      occurrences: 0,
      lastIndex: index
    };

    sequence.values.push(Number(numericPart));
    sequence.occurrences += 1;
    sequence.lastIndex = index;
    sequences.set(key, sequence);
  });

  const preferredSequence = [...sequences.values()].sort(
    (left, right) => right.occurrences - left.occurrences || right.lastIndex - left.lastIndex
  )[0];

  if (!preferredSequence) {
    return `${fallbackPrefix}${String(existingClaims.length + 1).padStart(3, "0")}`;
  }

  const nextValue = Math.max(...preferredSequence.values) + 1;
  return `${preferredSequence.prefix}${String(nextValue).padStart(preferredSequence.width, "0")}`;
}

function nextServiceDate(existingClaims: ClaimRecord[]) {
  const parsedDates = existingClaims
    .map((claim) => parseClaimDate(String(claim.ServiceDateFrom ?? "").trim()))
    .filter((date): date is ParsedClaimDate => date !== null);

  const usDateCount = parsedDates.filter((date) => date.style === "us").length;
  const isoDateCount = parsedDates.filter((date) => date.style === "iso").length;
  const preferredStyle: ParsedClaimDate["style"] = isoDateCount > usDateCount ? "iso" : "us";
  const yearCounts = new Map<number, number>();
  parsedDates.forEach((date) => yearCounts.set(date.year, (yearCounts.get(date.year) ?? 0) + 1));
  const preferredYear =
    [...yearCounts.entries()].sort((left, right) => right[1] - left[1])[0]?.[0] ?? new Date().getFullYear();
  const usedDates = new Set(parsedDates.map((date) => `${date.year}-${date.month}-${date.day}`));
  const daysInYear = new Date(preferredYear, 1, 29).getMonth() === 1 ? 366 : 365;

  for (let attempt = 0; attempt < daysInYear; attempt += 1) {
    const generatedDate = new Date(preferredYear, 0, randomInteger(1, daysInYear));
    const candidate: ParsedClaimDate = {
      year: generatedDate.getFullYear(),
      month: generatedDate.getMonth() + 1,
      day: generatedDate.getDate(),
      style: preferredStyle
    };
    const dateKey = `${candidate.year}-${candidate.month}-${candidate.day}`;
    if (!usedDates.has(dateKey)) return formatClaimDate(candidate, preferredStyle);
  }

  const fallbackDate = new Date(preferredYear + 1, 0, 1);
  return formatClaimDate(
    {
      year: fallbackDate.getFullYear(),
      month: fallbackDate.getMonth() + 1,
      day: fallbackDate.getDate(),
      style: preferredStyle
    },
    preferredStyle
  );
}

type ParsedClaimDate = {
  year: number;
  month: number;
  day: number;
  style: "us" | "iso";
};

function parseClaimDate(value: string): ParsedClaimDate | null {
  const usMatch = value.match(/^(\d{1,2})\/(\d{1,2})\/(\d{4})$/);
  if (usMatch) {
    return {
      year: Number(usMatch[3]),
      month: Number(usMatch[1]),
      day: Number(usMatch[2]),
      style: "us"
    };
  }

  const isoMatch = value.match(/^(\d{4})-(\d{1,2})-(\d{1,2})$/);
  if (isoMatch) {
    return {
      year: Number(isoMatch[1]),
      month: Number(isoMatch[2]),
      day: Number(isoMatch[3]),
      style: "iso"
    };
  }

  return null;
}

function formatClaimDate(date: ParsedClaimDate, style: ParsedClaimDate["style"]) {
  if (style === "iso") {
    return `${date.year}-${String(date.month).padStart(2, "0")}-${String(date.day).padStart(2, "0")}`;
  }

  return `${date.month}/${date.day}/${date.year}`;
}

export default function ClaimWorkspace({
  loading,
  sampleData,
  syncing,
  onSync
}: ClaimWorkspaceProps) {
  const [claims, setClaims] = useState<ClaimRecord[]>([]);
  const [analysis, setAnalysis] = useState<AnalyzeResponse | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [sourceLabel, setSourceLabel] = useState("Manual entry");
  const [syncMessage, setSyncMessage] = useState<string | null>(null);
  const [syncError, setSyncError] = useState<string | null>(null);
  const seededRef = useRef(false);
  const fileInputRef = useRef<HTMLInputElement | null>(null);
  const resultsRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    if (!seededRef.current && sampleData?.realtime_claims.preview?.length) {
      seededRef.current = true;
      setClaims(sampleData.realtime_claims.preview);
      setSourceLabel("Sample realtime claims");
    }
  }, [sampleData]);

  const resetAssessment = () => {
    setAnalysis(null);
    setSyncMessage(null);
  };

  const replaceClaims = (nextClaims: ClaimRecord[], label: string) => {
    setClaims(nextClaims);
    setSourceLabel(label);
    resetAssessment();
  };

  const updateClaim = (index: number, column: string, value: string) => {
    setClaims((current) =>
      current.map((claim, claimIndex) => (claimIndex === index ? { ...claim, [column]: value } : claim))
    );
    resetAssessment();
  };

  const submitClaims = async () => {
    if (!claims.length) {
      setError("Add at least one claim for assessment.");
      return;
    }

    setBusy(true);
    setError(null);
    try {
      const result = await analyzeClaims(claims);
      setAnalysis(result);
      window.setTimeout(() => {
        const prefersReducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
        resultsRef.current?.scrollIntoView({
          behavior: prefersReducedMotion ? "auto" : "smooth",
          block: "start"
        });
      }, 0);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Claim assessment failed.");
    } finally {
      setBusy(false);
    }
  };

  const uploadCsv = async (file: File | null) => {
    if (!file) return;

    setBusy(true);
    setError(null);
    try {
      const parsedClaims = parseClaimsCsv(await file.text());
      if (!parsedClaims.length) {
        throw new Error("The CSV does not include claim rows.");
      }
      replaceClaims(parsedClaims, file.name);
    } catch (err) {
      setError(err instanceof Error ? err.message : "CSV upload failed.");
    } finally {
      setBusy(false);
    }
  };

  const runSync = async () => {
    setSyncError(null);
    setSyncMessage(null);
    try {
      const result = await onSync();
      setSyncMessage(`Synced ${formatDate(result.trained_at)}.`);
    } catch (err) {
      setSyncError(err instanceof Error ? err.message : "Engine sync failed.");
    }
  };

  return (
    <div className="space-y-4">
      <Card className="border-t-4 border-t-info">
        <CardHeader className="flex flex-col gap-3 lg:flex-row lg:items-center lg:justify-between">
          <div>
            <CardTitle>New Claim Batch</CardTitle>
            <p className="mt-1 text-sm text-muted">
              {loading
                ? "Loading test cases..."
                : `${sourceLabel} - ${claims.length} claim${claims.length === 1 ? "" : "s"}`}
            </p>
          </div>
          <div className="flex flex-wrap gap-2">
            <Button
              variant="secondary"
              disabled={syncing || loading}
              icon={
                syncing ? (
                  <ArrowsClockwise className="animate-spin" size={17} weight="bold" />
                ) : (
                  <ArrowsClockwise size={17} weight="bold" />
                )
              }
              onClick={() => {
                void runSync();
              }}
            >
              {syncing ? "Syncing" : "Sync Engine"}
            </Button>
            <input
              ref={fileInputRef}
              className="sr-only"
              type="file"
              accept=".csv,text/csv"
              onChange={(event) => {
                const file = event.currentTarget.files?.[0] || null;
                event.currentTarget.value = "";
                void uploadCsv(file);
              }}
            />
            <Button
              variant="secondary"
              disabled={busy || loading}
              icon={<UploadSimple size={17} weight="bold" />}
              onClick={() => fileInputRef.current?.click()}
            >
              Upload CSV
            </Button>
            <Button
              variant="secondary"
              disabled={loading}
              icon={<Plus size={17} weight="bold" />}
              onClick={() => replaceClaims([...claims, blankClaim(claims)], sourceLabel)}
            >
              Add Claim
            </Button>
            <Button
              disabled={busy || loading || !claims.length}
              icon={busy ? <ArrowsClockwise className="animate-spin" size={17} weight="bold" /> : <ClipboardText size={17} weight="bold" />}
              onClick={submitClaims}
            >
              {busy ? "Processing" : "Proceed"}
            </Button>
          </div>
        </CardHeader>
        <CardContent className="space-y-3">
          {error ? (
            <p className="flex items-start gap-2 rounded-lg border border-red-200 bg-red-50 p-3 text-sm text-danger">
              <WarningCircle className="mt-0.5 shrink-0" size={17} weight="fill" aria-hidden="true" />
              {error}
            </p>
          ) : null}
          {syncError ? (
            <p className="flex items-start gap-2 rounded-lg border border-red-200 bg-red-50 p-3 text-sm text-danger">
              <WarningCircle className="mt-0.5 shrink-0" size={17} weight="fill" aria-hidden="true" />
              {syncError}
            </p>
          ) : null}
          {syncMessage ? (
            <p className="flex items-start gap-2 rounded-lg border border-green-200 bg-green-50 p-3 text-sm text-success">
              <CheckCircle className="mt-0.5 shrink-0" size={17} weight="fill" aria-hidden="true" />
              {syncMessage}
            </p>
          ) : null}

          {loading ? (
            <div
              className="flex min-h-48 items-center justify-center gap-3 rounded-lg border border-line bg-slate-50/80 text-sm font-medium text-muted"
              role="status"
              aria-live="polite"
            >
              <ArrowsClockwise className="animate-spin text-action" size={22} weight="bold" aria-hidden="true" />
              Loading test cases...
            </div>
          ) : (
            <div className="overflow-x-auto">
              <Table className="min-w-[3740px]">
                <THead>
                  <TR>
                    {editableColumns.map((column) => (
                      <TH key={column}>{formatColumnLabel(column)}</TH>
                    ))}
                    <TH aria-label="Actions" />
                  </TR>
                </THead>
                <TBody>
                  {claims.map((claim, index) => (
                    <TR key={`${claim.ClaimId}-${index}`}>
                      {editableColumns.map((column) => (
                        <TD key={column}>
                          <Input
                            aria-label={`${formatColumnLabel(column)} for claim ${index + 1}`}
                            className={inputWidthForColumn(column)}
                            value={String(claim[column] ?? "")}
                            onChange={(event) => updateClaim(index, column, event.target.value)}
                          />
                        </TD>
                      ))}
                      <TD>
                        <Button
                          variant="ghost"
                          aria-label="Remove claim"
                          className="size-10 px-0 text-danger hover:bg-red-50"
                          icon={<Trash size={17} weight="bold" />}
                          onClick={() =>
                            replaceClaims(
                              claims.filter((_, claimIndex) => claimIndex !== index),
                              sourceLabel
                            )
                          }
                        />
                      </TD>
                    </TR>
                  ))}
                </TBody>
              </Table>
            </div>
          )}
        </CardContent>
      </Card>

      {analysis ? (
        <div ref={resultsRef}>
          <AssessmentResults analysis={analysis} />
        </div>
      ) : null}
    </div>
  );
}

function AssessmentResults({ analysis }: { analysis: AnalyzeResponse }) {
  const [expandedCards, setExpandedCards] = useState<Set<string>>(() => new Set());

  useEffect(() => {
    setExpandedCards(new Set());
  }, [analysis]);

  const toggleCard = (cardKey: string) => {
    setExpandedCards((current) => {
      const next = new Set(current);
      if (next.has(cardKey)) {
        next.delete(cardKey);
      } else {
        next.add(cardKey);
      }
      return next;
    });
  };

  return (
    <div className="space-y-4">
      <section className="rounded-lg border border-slate-950/20 bg-[#10151f] p-4 text-white shadow-panel">
        <p className="text-sm font-semibold text-blue-200">Assessment Results</p>
        <h2 className="mt-1 text-2xl font-semibold text-white">Investigation Summary</h2>
        <p className="mt-1 text-sm text-slate-300">
          Processed {analysis.count} claim{analysis.count === 1 ? "" : "s"} at{" "}
          {formatDate(analysis.processed_at)}.
        </p>
      </section>

      <BatchSummaryBox summary={analysis.batch_summary} />

      <div className="space-y-4">
        {analysis.assessments.map((assessment, index) => {
          const cardKey = `${assessment.claim_id}-${assessment.line_number}-${index}`;
          const contentId = `assessment-details-${index}`;
          const isCollapsed = !expandedCards.has(cardKey);

          return (
            <Card key={cardKey} className={`border-t-4 ${riskBorder(assessment.risk_level)}`}>
              <CardHeader className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
                <div>
                  <CardTitle>
                    Claim {assessment.claim_id} - Line {assessment.line_number}
                  </CardTitle>
                  <p className="mt-1 text-sm text-muted">
                    {assessment.procedure_code} {assessment.procedure_name}
                  </p>
                </div>
                <div className="flex flex-wrap items-center gap-2">
                  <RiskBadge level={assessment.risk_level} />
                  <Button
                    variant="secondary"
                    aria-label={isCollapsed ? "Expand claim analysis" : "Collapse claim analysis"}
                    aria-controls={contentId}
                    aria-expanded={!isCollapsed}
                    className="size-8 min-h-8 px-0 py-0"
                    icon={isCollapsed ? <CaretDown size={16} weight="bold" /> : <CaretUp size={16} weight="bold" />}
                    onClick={() => toggleCard(cardKey)}
                  />
                </div>
              </CardHeader>
              {!isCollapsed ? (
                <CardContent id={contentId} className="space-y-4">
                  <div className="grid gap-2 md:grid-cols-[repeat(3,minmax(0,1fr))_minmax(0,1.4fr)]">
                    <SummaryStat
                      label="Risk Score"
                      value={`${Math.round(assessment.final_risk_score * 100)}%`}
                      icon={<Gauge size={19} weight="duotone" />}
                      tone={assessment.risk_level === "High" ? "danger" : assessment.risk_level === "Medium" ? "warning" : "success"}
                    />
                    <SummaryStat
                      label="Payment Deviation"
                      value={`${Math.round(assessment.unexpected_pattern_score * 100)}%`}
                      // detail="Deviation from expected mean (30% risk-score weight)"
                      icon={<ChartLineUp size={19} weight="duotone" />}
                      tone="warning"
                    />
                    <SummaryStat
                      label="Rules Triggered"
                      value={assessment.rule_flag_count.toString()}
                      icon={<ShieldWarning size={19} weight="duotone" />}
                      tone={assessment.rule_flag_count > 0 ? "warning" : "success"}
                    />
                    <SummaryStat
                      label="Review Pattern"
                      value={
                        <div className="flex min-w-0 items-center justify-between gap-4">
                          <span className="min-w-0 truncate">{assessment.predicted_pattern}</span>
                          <span
                            className="flex shrink-0 items-center gap-1.5 border-l border-slate-200 pl-4 text-base text-info"
                            aria-label={`Pattern confidence: ${Math.round(assessment.confidence_level * 100)}%`}
                            title="Pattern confidence"
                          >
                            <SealCheck size={18} weight="duotone" aria-hidden="true" />
                            {Math.round(assessment.confidence_level * 100)}%
                          </span>
                        </div>
                      }
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
                    <ResultList title="Key Rules Triggered" items={assessment.narrative.key_risk_indicators} />
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

                  {/* <section className="rounded-lg border border-line bg-slate-50/80 p-4">
                    <h3 className="flex items-center gap-2 text-sm font-semibold text-ink">
                      <Target size={17} weight="duotone" aria-hidden="true" />
                      Detailed Claim Assessment
                    </h3>
                    <dl className="mt-3 grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
                      <Detail label="Member ID" value={assessment.member_id || "Not provided"} />
                      <Detail label="Provider" value={assessment.provider_npi} />
                      <Detail label="Category" value={assessment.category} />
                      <Detail label="Top Reason" value={assessment.top_reason} />
                      <Detail label="Recommended Action" value={assessment.recommended_action} />
                    </dl>
                  </section> */}
                </CardContent>
              ) : null}
            </Card>
          );
        })}
      </div>
    </div>
  );
}

function BatchSummaryBox({ summary }: { summary: BatchSummary }) {
  return (
    <section className="rounded-lg border border-line bg-white p-4 shadow-sm">
      <div className="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
        <div className="min-w-0">
          <h3 className="flex items-center gap-2 text-sm font-semibold text-ink">
            <ClipboardText size={17} weight="duotone" aria-hidden="true" />
            Assessment Overview
          </h3>
          <p className="mt-2 max-w-3xl text-sm leading-6 text-muted">{summary.summary}</p>
        </div>
        <div className="grid shrink-0 grid-cols-2 gap-2 sm:grid-cols-4 lg:min-w-[520px]">
          <BatchCount
            label="Frauds"
            value={summary.fraud_count}
            icon={<ShieldWarning size={16} weight="duotone" />}
            tone="danger"
          />
          <BatchCount
            label="Suspicious"
            value={summary.suspicious_count}
            icon={<WarningCircle size={16} weight="duotone" />}
            tone="warning"
          />
          <BatchCount
            label="Clean"
            value={summary.clean_count}
            icon={<CheckCircle size={16} weight="duotone" />}
            tone="success"
          />
          <BatchCount
            label="Avg Risk"
            value={`${Math.round(summary.average_risk_score * 100)}%`}
            icon={<Gauge size={16} weight="duotone" />}
            tone="info"
          />
        </div>
      </div>
    </section>
  );
}

function BatchCount({
  label,
  value,
  icon,
  tone
}: {
  label: string;
  value: number | string;
  icon: ReactNode;
  tone: "success" | "warning" | "danger" | "info";
}) {
  const toneStyles = {
    success: "border-green-200 bg-green-50 text-success",
    warning: "border-amber-200 bg-amber-50 text-warning",
    danger: "border-red-200 bg-red-50 text-danger",
    info: "border-sky-200 bg-sky-50 text-info"
  };

  return (
    <div className="min-h-20 rounded-lg border border-line bg-slate-50/80 p-3">
      <div className="flex items-center gap-2 text-xs font-semibold uppercase text-muted">
        <span className={`flex size-7 shrink-0 items-center justify-center rounded-lg border ${toneStyles[tone]}`} aria-hidden="true">
          {icon}
        </span>
        <span className="truncate">{label}</span>
      </div>
      <p className="mt-2 text-2xl font-semibold text-ink">{value}</p>
    </div>
  );
}

function SummaryStat({
  label,
  value,
  detail,
  icon,
  tone
}: {
  label: string;
  value: ReactNode;
  detail?: string;
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
      <div className="mt-2 break-words text-lg font-semibold text-ink">{value}</div>
      {detail ? <p className="mt-1 text-xs leading-5 text-muted">{detail}</p> : null}
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
            {title === "Key Rules Triggered" ? (
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

function Detail({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <dt className="text-xs font-semibold uppercase text-muted">{label}</dt>
      <dd className="mt-1 break-words text-sm text-ink">{value}</dd>
    </div>
  );
}

function riskBorder(level: string) {
  if (level === "High") return "border-t-danger";
  if (level === "Medium") return "border-t-warning";
  if (level === "Low") return "border-t-success";
  return "border-t-info";
}

function formatDate(value: string) {
  return new Date(value).toLocaleString();
}

function formatColumnLabel(column: string) {
  return column
    .replace(/_/g, " ")
    .replace(/([a-z0-9])([A-Z])/g, "$1 $2")
    .replace(/([A-Z]+)([A-Z][a-z])/g, "$1 $2")
    .replace(/\bId\b/g, "ID");
}

function inputWidthForColumn(column: string) {
  if (column === "LONG_DESCRIPTION" || column === "ProcedureName") return "min-w-72";
  if (column === "MemberId" || column === "ServiceDateFrom" || column === "ProviderNPI") return "min-w-40";
  if (column.includes("Amt") || column === "ClaimLineTotalPaid") return "min-w-32";
  return "min-w-28";
}

function parseClaimsCsv(text: string): ClaimRecord[] {
  const rows = parseCsvRows(text);
  if (rows.length < 2) return [];

  const [headerRow, ...dataRows] = rows;
  const headers = headerRow.map((header, index) => {
    const normalized = header.replace(/^\uFEFF/, "").trim();
    return canonicalClaimHeader(normalized) || `Column${index + 1}`;
  });

  return dataRows
    .map((row, rowIndex) => {
      const claim = headers.reduce((record, header, index) => {
        record[header] = row[index]?.trim() ?? "";
        return record;
      }, {} as ClaimRecord);

      if (!claim.ClaimId) {
        claim.ClaimId = `CSV${String(rowIndex + 1).padStart(3, "0")}`;
      }

      return claim;
    })
    .filter((claim) => Object.values(claim).some((value) => String(value ?? "").trim() !== ""));
}

function canonicalClaimHeader(header: string) {
  const compact = header.toLowerCase().replace(/[\s_-]+/g, "");
  if (compact === "memberid" || compact === "memeberid") return "MemberId";
  if (compact === "primarydiagnosispointer") return "Primary_Diagnosis_Pointer";
  if (compact === "primarydiagnosis") return "Primary_Diagnosis";
  if (compact === "longdescription") return "LONG_DESCRIPTION";
  return header;
}

function parseCsvRows(text: string): string[][] {
  const rows: string[][] = [];
  let row: string[] = [];
  let cell = "";
  let inQuotes = false;

  for (let index = 0; index < text.length; index += 1) {
    const char = text[index];

    if (char === "\"") {
      if (inQuotes && text[index + 1] === "\"") {
        cell += "\"";
        index += 1;
      } else {
        inQuotes = !inQuotes;
      }
      continue;
    }

    if (char === "," && !inQuotes) {
      row.push(cell);
      cell = "";
      continue;
    }

    if ((char === "\n" || char === "\r") && !inQuotes) {
      if (char === "\r" && text[index + 1] === "\n") {
        index += 1;
      }
      row.push(cell);
      if (row.some((value) => value.trim() !== "")) {
        rows.push(row);
      }
      row = [];
      cell = "";
      continue;
    }

    cell += char;
  }

  if (inQuotes) {
    throw new Error("The CSV has an unmatched quote.");
  }

  row.push(cell);
  if (row.some((value) => value.trim() !== "")) {
    rows.push(row);
  }

  return rows;
}
