import { ClipboardText, Plus, Rows, Trash, UploadSimple, WarningCircle } from "@phosphor-icons/react";
import { useEffect, useRef, useState } from "react";

import { Button } from "../components/ui/button";
import { Badge } from "../components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "../components/ui/card";
import { Input } from "../components/ui/input";
import { Table, TBody, TD, TH, THead, TR } from "../components/ui/table";
import { analyzeClaims, analyzeCsv } from "../services/api";
import type { AnalyzeResponse, ClaimRecord, SampleDataResponse } from "../types/api";

const editableColumns = [
  "ClaimId",
  "ProcedureCode",
  "Modifier",
  "Primary_Diagnosis",
  "AmtCharged",
  "AmtEligible",
  "AllowedUnits",
  "State"
];

function blankClaim(): ClaimRecord {
  return {
    ClaimId: `NEW${Date.now().toString().slice(-5)}`,
    Gender: "U",
    Age: 40,
    ServiceDateFrom: "2024-06-01",
    PlaceOfService: "11",
    LineNumber: 1,
    ProcedureCode: "92014",
    ProcedureName: "Comprehensive Eye Exam",
    Modifier: "",
    Modifier2: "",
    Modifier3: "",
    Primary_Diagnosis_Pointer: "1",
    Primary_Diagnosis: "H52.4",
    LONG_DESCRIPTION: "Routine eye exam",
    ClaimLineTotalPaid: 0,
    AmtCharged: 150,
    AllowedUnits: 1,
    AmtDisallowed: 0,
    AmtEligible: 120,
    AmtCopay: 0,
    AmtCoinsurance: 0,
    AmtDeductible: 0,
    ProviderNPI: "1234567890",
    GroupId: "G1",
    GroupNumber: "GRP100",
    LOB: "COMM",
    CoverageCode: "PPO",
    State: "OH"
  };
}

export default function ClaimReview({
  sampleData,
  onAnalysis
}: {
  sampleData: SampleDataResponse | null;
  onAnalysis: (result: AnalyzeResponse) => void;
}) {
  const [claims, setClaims] = useState<ClaimRecord[]>([blankClaim()]);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement | null>(null);

  useEffect(() => {
    if (sampleData?.realtime_claims.preview?.length) {
      setClaims(sampleData.realtime_claims.preview.slice(0, 5));
    }
  }, [sampleData]);

  const updateClaim = (index: number, column: string, value: string) => {
    setClaims((current) =>
      current.map((claim, claimIndex) => (claimIndex === index ? { ...claim, [column]: value } : claim))
    );
  };

  const submitClaims = async () => {
    setBusy(true);
    setError(null);
    try {
      const result = await analyzeClaims(claims.slice(0, 5));
      onAnalysis(result);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Claim review failed.");
    } finally {
      setBusy(false);
    }
  };

  const uploadCsv = async (file: File | null) => {
    if (!file) return;
    setBusy(true);
    setError(null);
    try {
      const result = await analyzeCsv(file);
      onAnalysis(result);
    } catch (err) {
      setError(err instanceof Error ? err.message : "CSV review failed.");
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="space-y-4">
      <section className="rounded-lg border border-slate-950/20 bg-[#10151f] p-4 text-white shadow-panel">
        <div className="flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
        <div>
            <p className="text-sm font-semibold text-blue-200">Claim Review</p>
            <h2 className="mt-1 text-2xl font-semibold text-white">Prepare Claim Set</h2>
            <p className="mt-1 max-w-3xl text-sm text-slate-300">
            Upload a small claim file or adjust the claim details before assessment.
          </p>
        </div>
        <div className="flex flex-wrap gap-2">
          <input
            ref={fileInputRef}
            className="sr-only"
            type="file"
            accept=".csv"
            onChange={(event) => {
              void uploadCsv(event.target.files?.[0] || null);
              event.currentTarget.value = "";
            }}
          />
          <Button
            variant="secondary"
            className="border-white/15 bg-white/10 text-white hover:bg-white/15"
            icon={<UploadSimple size={17} weight="bold" />}
            disabled={busy}
            onClick={() => fileInputRef.current?.click()}
          >
            Upload CSV
          </Button>
          <Button
            variant="secondary"
            className="border-white/15 bg-white/10 text-white hover:bg-white/15"
            icon={<Plus size={17} weight="bold" />}
            disabled={claims.length >= 5}
            onClick={() => setClaims((current) => [...current, blankClaim()].slice(0, 5))}
          >
            Add Claim
          </Button>
          <Button disabled={busy || claims.length === 0} icon={<ClipboardText size={17} weight="bold" />} onClick={submitClaims}>
            {busy ? "Reviewing" : "Run Assessment"}
          </Button>
        </div>
        </div>
      </section>

      {error ? (
        <p className="flex items-start gap-2 rounded-lg border border-red-200 bg-red-50 p-3 text-sm text-danger">
          <WarningCircle className="mt-0.5 shrink-0" size={17} weight="fill" aria-hidden="true" />
          {error}
        </p>
      ) : null}

      <Card className="border-t-4 border-t-info">
        <CardHeader className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
          <CardTitle>Claims Ready For Review</CardTitle>
          <Badge className="border-sky-200 bg-sky-50 text-info">
            <Rows size={14} weight="fill" aria-hidden="true" />
            {claims.length}/5 claims
          </Badge>
        </CardHeader>
        <CardContent className="overflow-x-auto">
          <Table className="min-w-[1040px]">
            <THead>
              <TR>
                {editableColumns.map((column) => (
                  <TH key={column}>{column.replace(/_/g, " ")}</TH>
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
                        aria-label={`${column} for claim ${index + 1}`}
                        className="min-w-28"
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
                      onClick={() => setClaims((current) => current.filter((_, claimIndex) => claimIndex !== index))}
                    />
                  </TD>
                </TR>
              ))}
            </TBody>
          </Table>
          <p className="mt-3 text-sm text-muted">Realtime review accepts one to five claims at a time.</p>
        </CardContent>
      </Card>
    </div>
  );
}
