from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Literal

import numpy as np
import pandas as pd

from app.utils.number_parsing import clean_numeric_series


RuleMode = Literal["historical", "realtime"]

EXAM_CODES = {"92002", "92004", "92012", "92014", "S0620", "S0621"}
ADDON_CODES = {"V2750", "V2755", "V2760"}
COMPREHENSIVE_EXAM_CODES = {"92004", "92014"}
ROUTINE_EXAM_CODES = {"92002", "92012"}
CCI_CODE_PAIRS = {
    "92285": {"92250", "92235"},
    "92250": {"92285", "92235"},
    "92235": {"92250", "92285"},
}


@dataclass(frozen=True)
class RuleDefinition:
    rule_id: str
    column: str
    name: str
    description: str
    trigger_logic: str
    severity: str
    category: str
    realtime_supported: bool


RULE_DEFINITIONS = [
    RuleDefinition(
        "R006",
        "R006_Modifier59_Flag",
        "Modifier 59 on vision codes",
        "Modifier 59 appears on a vision exam or material procedure.",
        "Procedure code begins with 92 or V, and any modifier equals 59.",
        "Medium",
        "Coding Review",
        True,
    ),
    RuleDefinition(
        "R007",
        "R007_High_Billed_to_Allowed_Flag",
        "High billed-to-allowed ratio",
        "The billed amount is more than twice the eligible amount.",
        "AmtEligible is greater than 0 and AmtCharged / AmtEligible is greater than 2.0.",
        "High",
        "Billing Concern",
        True,
    ),
    RuleDefinition(
        "R008",
        "R008_Excessive_Units_Exam_Flag",
        "Excessive units on exam codes",
        "More than one unit is allowed on a routine exam code.",
        "ProcedureCode is an exam code and AllowedUnits is greater than 1.",
        "Medium",
        "Coding Review",
        True,
    ),
    RuleDefinition(
        "R009",
        "R009_Invalid_Vision_Code_Flag",
        "Invalid CPT for vision plan",
        "The procedure code does not match expected vision plan code families.",
        "ProcedureCode does not start with 92 or V.",
        "High",
        "Billing Concern",
        True,
    ),
    RuleDefinition(
        "R013",
        "R013_Provider_High_Exam_Volume_Flag",
        "Provider high exam volume",
        "Provider exam volume is at or above the historical 99th percentile.",
        "Provider exam count is greater than or equal to the 99th percentile.",
        "Medium",
        "Provider Pattern",
        False,
    ),
    RuleDefinition(
        "R014",
        "R014_Provider_High_Material_Volume_Flag",
        "Provider high material volume",
        "Provider material volume is at or above the historical 99th percentile.",
        "Provider material count is greater than or equal to the 99th percentile.",
        "Medium",
        "Provider Pattern",
        False,
    ),
    RuleDefinition(
        "R015",
        "R015_Provider_High_Avg_Billed_Flag",
        "Provider high average billed amount",
        "Provider average billed amount is at or above the historical 99th percentile.",
        "Provider average AmtCharged is greater than or equal to the 99th percentile.",
        "High",
        "Provider Pattern",
        False,
    ),
    RuleDefinition(
        "R016",
        "R016_Provider_High_Addon_Usage_Flag",
        "Provider high add-on usage",
        "Provider add-on usage ratio is at or above the historical 99th percentile.",
        "Provider add-on count divided by material count is greater than or equal to the 99th percentile.",
        "Medium",
        "Provider Pattern",
        False,
    ),
    RuleDefinition(
        "R017",
        "R017_Missing_Diagnosis_Flag",
        "Missing diagnosis",
        "Primary diagnosis is missing.",
        "Primary_Diagnosis is null or empty.",
        "High",
        "Documentation Gap",
        True,
    ),
    RuleDefinition(
        "R100",
        "R100_Two_Exams_One_Day",
        "Two exams in one day",
        "More than one distinct eye exam code appears on the same claim service day.",
        "Same ClaimId and ServiceDate contains more than one distinct exam code.",
        "Medium",
        "Utilization Pattern",
        True,
    ),
    RuleDefinition(
        "R101",
        "R101_Exam_After_Comprehensive",
        "Exam after comprehensive",
        "A routine exam appears on the same claim service day as a comprehensive exam.",
        "Same ClaimId and ServiceDate contains a comprehensive exam and a routine exam.",
        "Medium",
        "Utilization Pattern",
        True,
    ),
    RuleDefinition(
        "R102",
        "R102_CCI_Edit",
        "CCI edit conflict",
        "Procedure codes on the same claim service day appear in a known CCI conflict pair.",
        "Same ClaimId and ServiceDate contains one of the configured CCI code pairs.",
        "High",
        "Coding Review",
        True,
    ),
    RuleDefinition(
        "R103",
        "R103_Bilateral",
        "Bilateral modifier",
        "A bilateral or left/right modifier appears on the claim line.",
        "Modifier, Modifier2, or Modifier3 is 50, LT, or RT.",
        "Medium",
        "Coding Review",
        True,
    ),
]

RULES_BY_COLUMN = {rule.column: rule for rule in RULE_DEFINITIONS}
HISTORICAL_RULE_COLUMNS = [rule.column for rule in RULE_DEFINITIONS]
REALTIME_RULE_COLUMNS = [rule.column for rule in RULE_DEFINITIONS if rule.realtime_supported]


CANONICAL_CLAIM_COLUMNS = [
    "ClaimId",
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
    "State",
]

NUMERIC_CLAIM_COLUMNS = [
    "Age",
    "LineNumber",
    "ClaimLineTotalPaid",
    "AmtCharged",
    "AllowedUnits",
    "AmtDisallowed",
    "AmtEligible",
    "AmtCopay",
    "AmtCoinsurance",
    "AmtDeductible",
]

STRING_CLAIM_COLUMNS = [column for column in CANONICAL_CLAIM_COLUMNS if column not in NUMERIC_CLAIM_COLUMNS]


def normalize_claims(df: pd.DataFrame) -> pd.DataFrame:
    result = df.copy()
    for column in CANONICAL_CLAIM_COLUMNS:
        if column not in result.columns:
            result[column] = "" if column in STRING_CLAIM_COLUMNS else 0

    for column in STRING_CLAIM_COLUMNS:
        result[column] = result[column].fillna("").astype(str).str.strip()

    for column in NUMERIC_CLAIM_COLUMNS:
        result[column] = clean_numeric_series(result[column], index=result.index)

    result["ProcedureCode"] = result["ProcedureCode"].astype(str).str.strip().str.upper()
    result["ServiceDate"] = pd.to_datetime(result["ServiceDateFrom"], errors="coerce")
    return result


def _vision_code_mask(series: pd.Series) -> pd.Series:
    code = series.fillna("").astype(str).str.upper().str.strip()
    return code.str.startswith("92") | code.str.startswith("V")


def _safe_quantile(series: pd.Series, q: float) -> float:
    clean = pd.to_numeric(series, errors="coerce").dropna()
    if clean.empty:
        return float("inf")
    return float(np.quantile(clean, q))


def apply_rules(df: pd.DataFrame, mode: RuleMode, context_df: pd.DataFrame | None = None) -> pd.DataFrame:
    result = normalize_claims(df)
    procedure = result["ProcedureCode"].fillna("").astype(str).str.upper().str.strip()
    is_vision = _vision_code_mask(procedure)

    modifiers = (
        result[["Modifier", "Modifier2", "Modifier3"]]
        .fillna("")
        .astype(str)
        .apply(lambda col: col.str.strip())
    )
    result["R006_Modifier59_Flag"] = (is_vision & modifiers.eq("59").any(axis=1)).astype(int)

    eligible = pd.to_numeric(result["AmtEligible"], errors="coerce").fillna(0.0)
    charged = pd.to_numeric(result["AmtCharged"], errors="coerce").fillna(0.0)
    result["R007_High_Billed_to_Allowed_Flag"] = ((eligible > 0) & ((charged / eligible) > 2.0)).astype(int)

    allowed_units = pd.to_numeric(result["AllowedUnits"], errors="coerce").fillna(0.0)
    result["R008_Excessive_Units_Exam_Flag"] = (procedure.isin(EXAM_CODES) & (allowed_units > 1)).astype(int)
    result["R009_Invalid_Vision_Code_Flag"] = (~is_vision).astype(int)

    diagnosis = result["Primary_Diagnosis"].fillna("").astype(str).str.strip()
    result["R017_Missing_Diagnosis_Flag"] = (diagnosis == "").astype(int)
    result = _apply_claim_day_context_rules(result, context_df)

    if mode == "historical":
        procedure = result["ProcedureCode"].fillna("").astype(str).str.upper().str.strip()
        charged = pd.to_numeric(result["AmtCharged"], errors="coerce").fillna(0.0)
        result = _apply_provider_rules(result, procedure, charged)
        rule_columns = HISTORICAL_RULE_COLUMNS
    else:
        rule_columns = REALTIME_RULE_COLUMNS

    result["Rule_Flag_Count"] = result[rule_columns].sum(axis=1).astype(int)
    return result


def _apply_claim_day_context_rules(result: pd.DataFrame, context_df: pd.DataFrame | None = None) -> pd.DataFrame:
    base = result.copy().reset_index(drop=True)
    base["_source_row"] = np.arange(len(base))
    base["_is_realtime_source"] = True

    if context_df is not None and not context_df.empty:
        context = normalize_claims(context_df)
        context = _matching_claim_day_context(base, context)
        context["_source_row"] = -1
        context["_is_realtime_source"] = False
        combined = pd.concat([base, context], ignore_index=True, sort=False)
    else:
        combined = base

    combined = _score_claim_day_rules(combined)
    scored = combined[combined["_is_realtime_source"]].copy()
    scored = scored.sort_values("_source_row").drop(columns=["_source_row", "_is_realtime_source"])
    return scored.reset_index(drop=True)


def _matching_claim_day_context(incoming: pd.DataFrame, context: pd.DataFrame) -> pd.DataFrame:
    incoming_keys = incoming[["ClaimId", "ServiceDate"]].drop_duplicates()
    if incoming_keys.empty:
        return context.iloc[0:0].copy()
    return context.merge(incoming_keys, on=["ClaimId", "ServiceDate"], how="inner")


def _claim_day_key(df: pd.DataFrame) -> pd.Series:
    service_day = pd.to_datetime(df["ServiceDate"], errors="coerce").dt.strftime("%Y-%m-%d").fillna("")
    return df["ClaimId"].fillna("").astype(str).str.strip() + "|" + service_day


def _has_cci_pair(codes: set[str]) -> bool:
    return any(code in codes and bool(conflicts & codes) for code, conflicts in CCI_CODE_PAIRS.items())


def _score_claim_day_rules(df: pd.DataFrame) -> pd.DataFrame:
    result = df.copy()
    result["_claim_day_key"] = _claim_day_key(result)
    code_sets = result.groupby("_claim_day_key")["ProcedureCode"].agg(
        lambda values: frozenset(values.fillna("").astype(str).str.upper().str.strip())
    )
    result["_procedure_code_set"] = result["_claim_day_key"].map(code_sets)

    result["R100_Two_Exams_One_Day"] = result["_procedure_code_set"].map(
        lambda codes: len(set(codes) & EXAM_CODES) > 1
    ).astype(int)
    result["R101_Exam_After_Comprehensive"] = result["_procedure_code_set"].map(
        lambda codes: bool(set(codes) & COMPREHENSIVE_EXAM_CODES) and bool(set(codes) & ROUTINE_EXAM_CODES)
    ).astype(int)
    result["R102_CCI_Edit"] = result["_procedure_code_set"].map(_has_cci_pair).astype(int)

    modifiers = (
        result[["Modifier", "Modifier2", "Modifier3"]]
        .fillna("")
        .astype(str)
        .apply(lambda col: col.str.strip().str.upper())
    )
    result["R103_Bilateral"] = modifiers.isin({"50", "LT", "RT"}).any(axis=1).astype(int)
    return result.drop(columns=["_claim_day_key", "_procedure_code_set"])


def _apply_provider_rules(result: pd.DataFrame, procedure: pd.Series, charged: pd.Series) -> pd.DataFrame:
    result = result.copy()
    result["is_exam"] = procedure.isin(EXAM_CODES).astype(int)
    exam_counts = result.groupby("ProviderNPI")["is_exam"].sum()
    exam_threshold = _safe_quantile(exam_counts, 0.99)
    result["provider_exam_count"] = result["ProviderNPI"].map(exam_counts).fillna(0)
    result["R013_Provider_High_Exam_Volume_Flag"] = (result["provider_exam_count"] >= exam_threshold).astype(int)

    result["is_material"] = procedure.str.startswith("V").astype(int)
    material_counts = result.groupby("ProviderNPI")["is_material"].sum()
    material_threshold = _safe_quantile(material_counts, 0.99)
    result["provider_material_count"] = result["ProviderNPI"].map(material_counts).fillna(0)
    result["R014_Provider_High_Material_Volume_Flag"] = (
        result["provider_material_count"] >= material_threshold
    ).astype(int)

    provider_avg_billed = charged.groupby(result["ProviderNPI"]).mean()
    billed_threshold = _safe_quantile(provider_avg_billed, 0.99)
    result["provider_avg_billed"] = result["ProviderNPI"].map(provider_avg_billed).fillna(0.0)
    result["R015_Provider_High_Avg_Billed_Flag"] = (
        result["provider_avg_billed"] >= billed_threshold
    ).astype(int)

    result["is_addon"] = procedure.isin(ADDON_CODES).astype(int)
    addon_count = result.groupby("ProviderNPI")["is_addon"].sum()
    material_for_ratio = result.groupby("ProviderNPI")["is_material"].sum()
    addon_ratio = (addon_count / material_for_ratio.replace(0, np.nan)).fillna(0.0)
    addon_threshold = _safe_quantile(addon_ratio, 0.99)
    result["provider_addon_ratio"] = result["ProviderNPI"].map(addon_ratio).fillna(0.0)
    result["R016_Provider_High_Addon_Usage_Flag"] = (
        result["provider_addon_ratio"] >= addon_threshold
    ).astype(int)

    return result


def rule_definitions_for_workbook() -> list[dict[str, str]]:
    return [
        {
            "Rule Id": rule.rule_id,
            "Rule Name": rule.name,
            "Description": rule.description,
            "Trigger Logic": rule.trigger_logic,
            "Severity": rule.severity,
            "Category": rule.category,
        }
        for rule in RULE_DEFINITIONS
    ]


def triggered_indicators(row: pd.Series, mode: RuleMode) -> list[dict[str, str]]:
    columns = HISTORICAL_RULE_COLUMNS if mode == "historical" else REALTIME_RULE_COLUMNS
    indicators = []
    for column in columns:
        if int(row.get(column, 0) or 0) > 0:
            indicators.append(asdict(RULES_BY_COLUMN[column]))
    return indicators
