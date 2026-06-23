export type TrainingStatus = {
  trained: boolean;
  last_training_date: string | null;
  metrics: Record<string, unknown> | null;
  artifact_version: string | null;
  artifacts: string[];
};

export type TrainingResponse = {
  status: string;
  trained_at: string;
  metrics: Record<string, unknown>;
  artifact_version: string;
};

export type DatasetSummary = {
  path: string;
  record_count: number;
  preview: ClaimRecord[];
};

export type SampleDataResponse = {
  historical_claims: DatasetSummary;
  rules: DatasetSummary;
  realtime_claims: DatasetSummary;
};

export type ClaimRecord = {
  ClaimId: string;
  MemberId?: string;
  Gender?: string;
  Age?: number | string;
  ServiceDateFrom?: string;
  PlaceOfService?: string;
  LineNumber?: number | string;
  ProcedureCode?: string;
  ProcedureName?: string;
  Modifier?: string;
  Modifier2?: string;
  Modifier3?: string;
  Primary_Diagnosis_Pointer?: string;
  Primary_Diagnosis?: string;
  LONG_DESCRIPTION?: string;
  ClaimLineTotalPaid?: number | string;
  AmtCharged?: number | string;
  AllowedUnits?: number | string;
  AmtDisallowed?: number | string;
  AmtEligible?: number | string;
  AmtCopay?: number | string;
  AmtCoinsurance?: number | string;
  AmtDeductible?: number | string;
  ProviderNPI?: string;
  GroupId?: string;
  GroupNumber?: string;
  LOB?: string;
  CoverageCode?: string;
  State?: string;
  [key: string]: unknown;
};

export type TriggeredIndicator = {
  rule_id: string;
  name: string;
  description: string;
  severity: "Low" | "Medium" | "High" | string;
  category: string;
  occurrence_count: number;
  line_numbers: number[];
};

export type ClaimNarrative = {
  executive_summary: string;
  investigation_findings: string[];
  key_risk_indicators: string[];
  risk_classification: string;
  recommended_review_actions: string[];
  metadata: {
    model_used: string;
    llm_success: boolean;
    fallback_reason: string | null;
  };
};

export type ClaimAssessment = {
  claim_id: string;
  member_id: string;
  line_number: number;
  line_numbers: number[];
  line_count: number;
  provider_npi: string;
  procedure_code: string;
  procedure_name: string;
  risk_level: "Low" | "Medium" | "High" | string;
  final_risk_score: number;
  confidence_level: number;
  unexpected_pattern_score: number;
  rule_flag_count: number;
  triggered_indicators: TriggeredIndicator[];
  predicted_pattern: string;
  category: string;
  top_reason: string;
  recommended_action: string;
  narrative: ClaimNarrative;
  details: Record<string, unknown>;
};

export type BatchSummary = {
  total_claims: number;
  fraud_count: number;
  suspicious_count: number;
  clean_count: number;
  high_risk_count: number;
  medium_risk_count: number;
  low_risk_count: number;
  review_count: number;
  average_risk_score: number;
  summary: string;
  metadata: {
    model_used: string;
    llm_success: boolean;
    fallback_reason: string | null;
  };
};

export type AnalyzeResponse = {
  processed_at: string;
  count: number;
  batch_summary: BatchSummary;
  assessments: ClaimAssessment[];
};
