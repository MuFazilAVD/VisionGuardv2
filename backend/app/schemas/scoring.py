from typing import Any

from pydantic import BaseModel


class TriggeredIndicator(BaseModel):
    rule_id: str
    name: str
    description: str
    severity: str
    category: str


class NarrativeMetadata(BaseModel):
    model_used: str
    llm_success: bool
    fallback_reason: str | None = None


class ClaimNarrative(BaseModel):
    executive_summary: str
    investigation_findings: list[str]
    key_risk_indicators: list[str]
    risk_classification: str
    recommended_review_actions: list[str]
    metadata: NarrativeMetadata


class ClaimAssessment(BaseModel):
    claim_id: str
    member_id: str
    line_number: int
    provider_npi: str
    procedure_code: str
    procedure_name: str
    risk_level: str
    final_risk_score: float
    confidence_level: float
    unexpected_pattern_score: float
    rule_flag_count: int
    triggered_indicators: list[TriggeredIndicator]
    predicted_pattern: str
    category: str
    top_reason: str
    recommended_action: str
    narrative: ClaimNarrative
    details: dict[str, Any]


class BatchSummary(BaseModel):
    total_claims: int
    fraud_count: int
    suspicious_count: int
    clean_count: int
    high_risk_count: int
    medium_risk_count: int
    low_risk_count: int
    review_count: int
    average_risk_score: float
    summary: str
    metadata: NarrativeMetadata


class AnalyzeResponse(BaseModel):
    processed_at: str
    count: int
    batch_summary: BatchSummary
    assessments: list[ClaimAssessment]
