from __future__ import annotations

from dataclasses import asdict, dataclass
import logging
from typing import Literal

import numpy as np
import pandas as pd

from app.utils.number_parsing import clean_numeric_series


RuleMode = Literal["historical", "realtime"]

logger = logging.getLogger(__name__)

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


@dataclass(frozen=True)
class BusinessRuleDefinition:
    section: str
    item: str
    analysis: str
    risk_level: str
    operational_definition: str
    routine: str = ""
    medical: str = ""
    both: str = ""
    frequency: str = ""


@dataclass(frozen=True)
class BusinessRuleImplementation:
    rule_ids: tuple[str, ...]
    notes: str


def _indicator_marker(value: str) -> str:
    return "x" if value.strip().lower() == "x" else ""


def _business_rule(
    section: str,
    item: str,
    analysis: str,
    risk_level: str,
    operational_definition: str,
    *,
    routine: str = "",
    medical: str = "",
    both: str = "",
    frequency: str = "",
) -> BusinessRuleDefinition:
    return BusinessRuleDefinition(
        section=section,
        item=item,
        analysis=analysis,
        risk_level=risk_level,
        operational_definition=operational_definition.strip(),
        routine=_indicator_marker(routine),
        medical=_indicator_marker(medical),
        both=_indicator_marker(both),
        frequency=_indicator_marker(frequency),
    )


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
        "More than one distinct eye exam code appears for the same member on one service day.",
        "Same MemberId and ServiceDate contains more than one distinct exam code; ClaimId is used when MemberId is blank.",
        "Medium",
        "Utilization Pattern",
        True,
    ),
    RuleDefinition(
        "R101",
        "R101_Exam_After_Comprehensive",
        "Exam after comprehensive",
        "A routine exam appears for the same member and service day as a comprehensive exam.",
        "Same MemberId and ServiceDate contains a comprehensive exam and a routine exam; ClaimId is used when MemberId is blank.",
        "Medium",
        "Utilization Pattern",
        True,
    ),
    RuleDefinition(
        "R102",
        "R102_CCI_Edit",
        "CCI edit conflict",
        "Procedure codes for the same member and service day appear in a known CCI conflict pair.",
        "Same MemberId and ServiceDate contains one of the configured CCI code pairs; ClaimId is used when MemberId is blank.",
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
RULES_BY_ID = {rule.rule_id: rule for rule in RULE_DEFINITIONS}
HISTORICAL_RULE_COLUMNS = [rule.column for rule in RULE_DEFINITIONS]
REALTIME_RULE_COLUMNS = [rule.column for rule in RULE_DEFINITIONS if rule.realtime_supported]

BUSINESS_RULE_DEFINITIONS = [
    _business_rule('Operational Rules', '1', 'Coding Violations / Unbundling', '2', 'Review of CMS Correct Coding Edits, Peer-to-Peer  (PTP) and Medically Unlikely Edits (MUE)', medical='x'),
    _business_rule('Operational Rules', '2', 'Modifier Abuse FWA Pattern', '3', 'Bilateral Reimbursement for Status 1 Codes', medical='x'),
    _business_rule('Operational Rules', '3', 'Unbundling/ FWA Pattern', '1', 'Bilateral procedures submitted twice CPT codes with bilateral indicator = 2', medical='x'),
    _business_rule('Operational Rules', '4', 'FWA Pattern', '1', 'Exam Double Billing combination of Optometric Exam (92002, 92012, 92004, 92014, S0620, S0621) same day as E and M (CPT 99201 to 99215)', both='x'),
    _business_rule('Operational Rules', '5', 'FWA Pattern', '2', 'CPT Rule Violation, exam following a Comp. Exam CPT 92004/ 92014 followed by CPT (S0620, S0621, 92002, or 92012) or DX H52 or Z010 1 to 5 days following', medical='x'),
    _business_rule('Operational Rules', '6', 'Modifier Abuse FWA Pattern', '2', 'Exams same day Global Surgery Periods with or without modifiers', both='x'),
    _business_rule('Operational Rules', '7', 'Modifier Abuse FWA Pattern', '2', 'Exams during Global Surgery Periods', medical='x'),
    _business_rule('Operational Rules', '8', 'FWA Pattern', '1', 'Duplicate Claims Search', both='x'),
    _business_rule('Operational Rules', '9', 'Unbundling of Exam', '2', 'Routine Exam (S0620/ S0621) same day as refraction (92015), refraction is included', medical='x'),
    _business_rule('Operational Rules', '10', 'FWA Pattern', '2', 'Outlier review statistical review of provider services to the network', both='x'),
    _business_rule('Operational Rules', '11', 'FWA Pattern', '2', 'Outlier review statistical review of provider exams with and without additional services to the network', both='x'),
    _business_rule('Operational Rules', '12', 'Overutilization', '3', 'Frequency  medical optometry procedures to exam frequencies', both='x'),
    _business_rule('Operational Rules', '13', 'Unbundling of Exam', '3', "Tonometry Service (CPT 92100) same day as an exam, inclusive unless the provider performs the service 3X's", medical='x'),
    _business_rule('Operational Rules', '14', 'Unbundling of Exam', '2', 'Sensory Motor Exams (CPT 92060), inclusive to an exam unless there are clear and specific circumstances to document separately', medical='x'),
    _business_rule('Operational Rules', '15', 'Unbundling of Exam', '2', 'Fundus Photos (92250) and exam frequencies with routine DXs or new patient exams', medical='x'),
    _business_rule('Operational Rules', '16', 'Unbundling of Exam', '1', "Extended Visual Field Exams (CPT's 92081, 92082, or 92083) inclusive to an exam unless there are clear and specific circumstances to document separately", medical='x'),
    _business_rule('Operational Rules', '17', 'Unbundling of Exam', '2', "Gonioscopy (CPT's 92020) review to document separately as a separate procedure", medical='x'),
    _business_rule('Operational Rules', '18', 'FWA Pattern', '1', 'Services submitted with unspecified or other visual disturbances diagnosis codes', medical='x'),
    _business_rule('Operational Rules', '19', 'FWA Pattern', '3', 'Level 5 Evaluation and Management Exams (CPT 99205, 99215)', both='x'),
    _business_rule('Operational Rules', '20', 'FWA Pattern', '3', 'Excessive charges for Medically Necessary contacts', both='x'),
    _business_rule('Operational Rules', '21', 'FWA Pattern', '1', 'Opticians submitting exams', routine='x'),
    _business_rule('Operational Rules', '22', 'Coding Violation/ FWA Pattern', '2', 'New Patient for Established Patient exams within 3 years of first new pt exam', both='x'),
    _business_rule('Operational Rules', '23', 'Coding Violation/ FWA Pattern', '3', 'Vision Therapy (CPT 92065) and exams same day', medical='x'),
    _business_rule('Operational Rules', '24', 'FWA Pattern', '3', 'Vision Therapy Review (92065) and more than 1 units of service per day', medical='x'),
    _business_rule('Operational Rules', '25', 'FWA Pattern', '3', "Vision Therapy Review (92065) and/ or Rehabilitation Services (CPT 97's)", medical='x'),
    _business_rule('Operational Rules', '26', 'FWA Pattern', '2', 'Location of service reviews', both='x'),
    _business_rule('Operational Rules', '27', 'FWA Pattern', '3', 'Frequency of contact lens evaluations (CPT 92310) on the same day as eye exam', medical='x'),
    _business_rule('Operational Rules', '28', 'FWA Potential', '2', 'Submitting the same service under more than one policy (Same member with 2 distinct policies)', both='x'),
    _business_rule('Operational Rules', '29', 'FWA Potential Materials', '2', 'Materials dispensed without exams, potential services not rendered', routine='x'),
    _business_rule('Operational Rules', '30', 'FWA Potential Materials', '3', 'Family Orders, review for member abuse', routine='x'),
    _business_rule('Operational Rules', '31', 'FWA Pattern', '3', 'Material orders for patients without an exam in the calendar year', routine='x'),
    _business_rule('Operational Rules', '32', 'FWA Pattern', '2', 'Services provided related to open angle glaucoma diagnosis billing', medical='x'),
    _business_rule('Operational Rules', '33', 'FWA Pattern', '2', 'Repair Replace same day as new order', both='x'),
    _business_rule('Operational Rules', '34', 'FWA Pattern', '3', 'Providers services to patients <> in geographic area', both='x'),
    _business_rule('Operational Rules', '35', 'FWA Pattern', '2', 'Providers submitting services from multiple offices on the same day', both='x'),
    _business_rule('Operational Rules', '36', 'Fraud', '1', 'Charging members for RXs', routine='x'),
    _business_rule('Operational Rules', '37', 'FWA Pattern', '2', 'Provider utilization of routine vision diagnosis vs medical diagnosis codes', both='x'),
    _business_rule('Operational Rules', '38', 'Modifier Abuse FWA Pattern', '2', 'Exams and Medical Optometry procedures with modifier 59 (Docs vs. Techs)', medical='x'),
    _business_rule('Operational Rules', '39', 'Abuse Pattern', '2', 'Exams with modifier 25 for the same service (Drug Treatments) on multiple visits', medical='x'),
    _business_rule('Operational Rules', '40', 'FWA Internal', '3', 'Member and out of network payments (Direct Service Adjustments)'),
    _business_rule('Operational Rules', '41', 'FWA Potential Materials', '2', 'Materials: Practitioner Private Sale and submits claims', routine='x'),
    _business_rule('Operational Rules', '42', 'FWA Potential Materials', '2', 'Billing Sunglasses when not available as a member benefit V2020 with V2744', routine='x'),
    _business_rule('Operational Rules', '43', 'FWA Potential Materials', '2', 'Frequency of Repair and Replace, review for member or provider abuse', routine='x'),
    _business_rule('Operational Rules', '44', 'FWA Potential Materials', '3', 'Providers billing on same day over multiple years', routine='x'),
    _business_rule('Operational Rules', '45', 'FWA Pattern Surgery', '3', 'Eye lash removal (CPT 67820) splitting individual eye services after the 10 day rule', medical='x'),
    _business_rule('Operational Rules', '46', 'FWA Pattern Surgery', '3', 'Punctal Plugs (CPT 68761) splitting individual eye services after the 10 day rule', medical='x'),
    _business_rule('Operational Rules', '47', 'FWA Pattern Surgery', '3', 'Surgery; Cataract Surgery with additional procedures (MIG)', medical='x'),
    _business_rule('Operational Rules', '48', 'FWA Pattern Surgery', '3', 'Surgery; Cataract Surgery, Major CPT (66982) v Minor (66984), Simple v Extensive', medical='x'),
    _business_rule('Operational Rules', '49', 'FWA Pattern Surgery', '3', 'Surgery sessions (61793,66762,67109,67141,67145,67208,67210,67218,67220,67229,G0185,G0186,G0187,G0251,G0340,G0424)', medical='x'),
    _business_rule('Operational Rules', '50', 'FWA Pattern Surgery', '3', 'Surgery; Frequency of multiple YAG laser sessions (CPT 66821)', medical='x'),
    _business_rule('Operational Rules', '51', 'FWA Pattern Surgery', '3', 'Surgery: Injections with no Jcodes (11900, 64612) potential cosmetic injections (Collagen, Botox)', medical='x'),
    _business_rule('Operational Rules', '52', 'FWA Pattern Surgery', '3', 'Surgery; Multiple Stage billing (CPT 66802,66821,66840,66915,66982,66983,66984,67031,67102,67103,67104,67106,67113,67971,67973,67974,67975)', medical='x'),
    _business_rule('Operational Rules', '53', 'FWA Pattern Drugs', '3', 'Drugs, High Cost and Frequency of treatments (CPT J0178, J2778, J9035, J2503)', medical='x'),
    _business_rule('Operational Rules', '54', 'FWA Pattern Drugs', '3', "Drugs; Botox (CPT 64612 & C9018, C9278, J0585, J0586, J0587, J0588, J0860, J1155, Q2040) for non-spasm related DX's", medical='x'),
    _business_rule('Operational Rules', '55', 'FWA Pattern Labs', '3', 'Labs; (CPT 83861 & CLIA Waiver) or Tear Analysis', medical='x'),
    _business_rule('Operational Rules', '56', 'FWA Pattern Surgery', '3', 'Surgery: Trichiasis (67825) cosmetic vs. medically necessary', medical='x'),
    _business_rule('Operational Rules', '57', 'FWA Pattern Surgery', '3', 'Surgery: Blepharoplasty (15823, 67904) cosmetic vs. medically necessary', medical='x'),
    _business_rule('Operational Rules', '58', 'Upcoding Materials', '3', 'Material Upcoding, Polycarb (V2763/ 4)', both='x'),
    _business_rule('Operational Rules', '59', 'Upcoding Materials', '3', 'Material Upcoding, V2700 thru V2799 compared to population', both='x'),
    _business_rule('Operational Rules', '60', 'Upcoding Materials', '3', 'Material Upcoding, Single (V21X) vs Bifocal (V22X) vs Trifocal (V23X)', routine='x'),
    _business_rule('Operational Rules', '61', 'FWA Potential', '3', 'Blind Services (ICD-10 H54.*)', medical='x'),
    _business_rule('Operational Rules', '62', 'FWA Potential', '3', 'Lasik then glasses or contacts', both='x'),
    _business_rule('Operational Rules', '63', 'FWA Potential', '3', 'Out of Network reimbursement to In Network Providers', both='x'),
    _business_rule('Operational Rules', '64', 'FWA Potential', '3', 'Age related Diagnosis review', medical='x'),
    _business_rule('Operational Rules', '65', 'FWA Potential', '3', 'Standard vs Oversize frame (V2020 v V2025)', routine='x', medical='x'),
    _business_rule('Shared Client Risks', '1', 'FWA Potential', '1', 'Exam Double Billing, exams services submitted to both Versant Health and Medical plans for the same patient on the same day'),
    _business_rule('Shared Client Risks', '3', 'FWA Potential', '1', 'Contracted versant Health providers submitting routine services to Medical'),
    _business_rule('Shared Client Risks', '2', 'FWA Potential', '1', 'Refractions billed to Medical plans for Versant Health Routine Exams'),
    _business_rule('Shared Client Risks', '4', 'FWA Potential', '2', 'Review of Medical Plan services to Versant analytics'),
    _business_rule('Shared Client Risks', '5', 'FWA Potential', '2', 'Exams provided during Global Surgery Periods'),
    _business_rule('Shared Client Risks', '6', 'FWA Potential', '2', 'Surgeries, Major v Minor, Simple v Extensive'),
    _business_rule('Special', 'CMS', 'CMS', '', 'Multiple Payment Reduction (MPR)'),
    _business_rule('Special', 'CMS', 'CMS', '', 'Telehealth'),
    _business_rule('Special', 'CMS', 'CMS', '', 'Pandemic Billing'),
    _business_rule('Special', 'CMS', 'CMS', '', 'PPE'),
]

_BUSINESS_RULE_IMPLEMENTATIONS = {
    ("Operational Rules", "1"): BusinessRuleImplementation(
        ("R102",),
        "POC checks configured same-day CCI conflict pairs; full PTP and MUE edit tables are not loaded.",
    ),
    ("Operational Rules", "2"): BusinessRuleImplementation(
        ("R103",),
        "POC flags bilateral, left, and right modifiers; CMS status indicator data is not loaded.",
    ),
    ("Operational Rules", "3"): BusinessRuleImplementation(
        ("R103",),
        "POC flags bilateral, left, and right modifiers; bilateral indicator 2 requires CMS fee schedule data.",
    ),
    ("Operational Rules", "4"): BusinessRuleImplementation(
        ("R100",),
        "POC flags multiple exam codes on the same claim service day; E/M pairing is catalog-only.",
    ),
    ("Operational Rules", "5"): BusinessRuleImplementation(
        ("R101",),
        "POC flags comprehensive and routine exams on the same claim service day; the 1-5 day lookback needs member history.",
    ),
    ("Operational Rules", "10"): BusinessRuleImplementation(
        ("R013", "R014", "R015", "R016"),
        "Historical POC provider outlier flags cover exam volume, material volume, average billed amount, and add-on usage.",
    ),
    ("Operational Rules", "11"): BusinessRuleImplementation(
        ("R013",),
        "Historical POC flags provider exam volume at or above the 99th percentile.",
    ),
    ("Operational Rules", "12"): BusinessRuleImplementation(
        ("R013",),
        "Historical POC provider exam volume is a frequency proxy until medical optometry procedure families are modeled.",
    ),
    ("Operational Rules", "20"): BusinessRuleImplementation(
        ("R007",),
        "POC uses billed-to-allowed ratio greater than 2.0 as the current excessive-charge signal.",
    ),
    ("Operational Rules", "24"): BusinessRuleImplementation(
        ("R008",),
        "POC flags allowed units greater than 1 on exam codes; the 92065-specific unit rule remains catalog-only.",
    ),
    ("Operational Rules", "38"): BusinessRuleImplementation(
        ("R006",),
        "POC flags modifier 59 on vision exam or material procedure codes.",
    ),
    ("Shared Client Risks", "1"): BusinessRuleImplementation(
        ("R100",),
        "POC flags duplicate exam combinations within current claim-day data; cross-plan matching requires medical plan feeds.",
    ),
}


CANONICAL_CLAIM_COLUMNS = [
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
    logger.info("Normalizing claims frame with shape=%s", df.shape)
    result = df.copy()
    for column in CANONICAL_CLAIM_COLUMNS:
        if column not in result.columns:
            result[column] = "" if column in STRING_CLAIM_COLUMNS else 0

    for column in STRING_CLAIM_COLUMNS:
        result[column] = result[column].fillna("").astype(str).str.strip()

    for column in NUMERIC_CLAIM_COLUMNS:
        result[column] = clean_numeric_series(result[column], index=result.index)

    result["ProcedureCode"] = result["ProcedureCode"].astype(str).str.strip().str.upper()
    result["ServiceDate"] = pd.to_datetime(result["ServiceDateFrom"], format="mixed", errors="coerce")
    logger.info("Claims normalization complete with shape=%s", result.shape)
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
    logger.info(
        "Applying %s rules to %d row(s); context_rows=%s",
        mode,
        len(df),
        len(context_df) if context_df is not None else 0,
    )
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
    logger.info(
        "%s rules applied: columns=%d total_flags=%d",
        mode,
        len(rule_columns),
        int(result["Rule_Flag_Count"].sum()),
    )
    return result


def _apply_claim_day_context_rules(result: pd.DataFrame, context_df: pd.DataFrame | None = None) -> pd.DataFrame:
    logger.info("Applying claim-day context rules to %d source row(s)", len(result))
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

    logger.info("Claim-day rule context combined row count=%d", len(combined))
    combined = _score_claim_day_rules(combined)
    scored = combined[combined["_is_realtime_source"]].copy()
    scored = scored.sort_values("_source_row").drop(columns=["_source_row", "_is_realtime_source"])
    logger.info("Claim-day context rules applied")
    return scored.reset_index(drop=True)


def _matching_claim_day_context(incoming: pd.DataFrame, context: pd.DataFrame) -> pd.DataFrame:
    logger.info("Finding matching claim-day context rows")
    incoming = incoming.copy()
    context = context.copy()
    incoming["_claim_subject_key"] = _claim_subject_key(incoming)
    context["_claim_subject_key"] = _claim_subject_key(context)
    incoming_keys = incoming[["_claim_subject_key", "ServiceDate"]].drop_duplicates()
    if incoming_keys.empty:
        logger.info("No incoming claim-day keys found")
        return context.iloc[0:0].copy()
    matched = context.merge(incoming_keys, on=["_claim_subject_key", "ServiceDate"], how="inner")
    matched = matched.drop(columns=["_claim_subject_key"])
    logger.info("Matched %d claim-day context row(s)", len(matched))
    return matched


def _claim_subject_key(df: pd.DataFrame) -> pd.Series:
    member_id = df["MemberId"].fillna("").astype(str).str.strip()
    claim_id = df["ClaimId"].fillna("").astype(str).str.strip()
    return pd.Series(
        np.where(member_id.ne(""), "M|" + member_id, "C|" + claim_id),
        index=df.index,
        dtype="object",
    )


def _claim_day_key(df: pd.DataFrame) -> pd.Series:
    service_day = pd.to_datetime(df["ServiceDate"], errors="coerce").dt.strftime("%Y-%m-%d").fillna("")
    return _claim_subject_key(df) + "|" + service_day


def _has_cci_pair(codes: set[str]) -> bool:
    return any(code in codes and bool(conflicts & codes) for code, conflicts in CCI_CODE_PAIRS.items())


def _score_claim_day_rules(df: pd.DataFrame) -> pd.DataFrame:
    logger.info("Scoring claim-day rules for %d row(s)", len(df))
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
    logger.info("Claim-day rules scored")
    return result.drop(columns=["_claim_day_key", "_procedure_code_set"])


def _apply_provider_rules(result: pd.DataFrame, procedure: pd.Series, charged: pd.Series) -> pd.DataFrame:
    logger.info("Applying historical provider rules to %d row(s)", len(result))
    result = result.copy()
    result["is_exam"] = procedure.isin(EXAM_CODES).astype(int)
    exam_counts = result.groupby("ProviderNPI")["is_exam"].sum()
    exam_threshold = _safe_quantile(exam_counts, 0.99)
    result["provider_exam_count"] = result["ProviderNPI"].map(exam_counts).fillna(0)
    result["R013_Provider_High_Exam_Volume_Flag"] = (result["provider_exam_count"] >= exam_threshold).astype(int)
    logger.info("Provider exam volume threshold=%.6f", exam_threshold)

    result["is_material"] = procedure.str.startswith("V").astype(int)
    material_counts = result.groupby("ProviderNPI")["is_material"].sum()
    material_threshold = _safe_quantile(material_counts, 0.99)
    result["provider_material_count"] = result["ProviderNPI"].map(material_counts).fillna(0)
    result["R014_Provider_High_Material_Volume_Flag"] = (
        result["provider_material_count"] >= material_threshold
    ).astype(int)
    logger.info("Provider material volume threshold=%.6f", material_threshold)

    provider_avg_billed = charged.groupby(result["ProviderNPI"]).mean()
    billed_threshold = _safe_quantile(provider_avg_billed, 0.99)
    result["provider_avg_billed"] = result["ProviderNPI"].map(provider_avg_billed).fillna(0.0)
    result["R015_Provider_High_Avg_Billed_Flag"] = (
        result["provider_avg_billed"] >= billed_threshold
    ).astype(int)
    logger.info("Provider average billed threshold=%.6f", billed_threshold)

    result["is_addon"] = procedure.isin(ADDON_CODES).astype(int)
    addon_count = result.groupby("ProviderNPI")["is_addon"].sum()
    material_for_ratio = result.groupby("ProviderNPI")["is_material"].sum()
    addon_ratio = (addon_count / material_for_ratio.replace(0, np.nan)).fillna(0.0)
    addon_threshold = _safe_quantile(addon_ratio, 0.99)
    result["provider_addon_ratio"] = result["ProviderNPI"].map(addon_ratio).fillna(0.0)
    result["R016_Provider_High_Addon_Usage_Flag"] = (
        result["provider_addon_ratio"] >= addon_threshold
    ).astype(int)
    logger.info("Provider add-on usage threshold=%.6f", addon_threshold)

    logger.info("Historical provider rules applied")
    return result


def _business_rule_realtime_status(rule_ids: tuple[str, ...]) -> str:
    if not rule_ids:
        return ""

    statuses = {RULES_BY_ID[rule_id].realtime_supported for rule_id in rule_ids}
    if statuses == {True}:
        return "Yes"
    if statuses == {False}:
        return "No"
    return "Mixed"


def rule_definitions_for_workbook() -> list[dict[str, str]]:
    logger.info("Building business rule catalog rows")
    rows = []
    catalog_only_note = (
        "Cataloged from business rules; deterministic implementation requires additional source data "
        "or adjudication context."
    )
    for business_rule in BUSINESS_RULE_DEFINITIONS:
        implementation = _BUSINESS_RULE_IMPLEMENTATIONS.get(
            (business_rule.section, business_rule.item),
            BusinessRuleImplementation((), catalog_only_note),
        )
        rule_ids = implementation.rule_ids
        rows.append(
            {
                "Section": business_rule.section,
                "Item": business_rule.item,
                "Analysis": business_rule.analysis,
                "Risk Level": business_rule.risk_level,
                "Operational Definition": business_rule.operational_definition,
                "Routine": business_rule.routine,
                "Medical": business_rule.medical,
                "Both": business_rule.both,
                "Frequency": business_rule.frequency,
                "Implementation Status": "Executable" if rule_ids else "Catalog Only",
                "Executable Rule Ids": ", ".join(rule_ids),
                "Executable Flag Columns": ", ".join(RULES_BY_ID[rule_id].column for rule_id in rule_ids),
                "Realtime Supported": _business_rule_realtime_status(rule_ids),
                "Implementation Notes": implementation.notes,
            }
        )
    logger.info("Built %d business rule catalog row(s)", len(rows))
    return rows


def executable_rule_definitions_for_workbook() -> list[dict[str, str]]:
    logger.info("Building executable rule definition rows")
    rows = [
        {
            "Rule Id": rule.rule_id,
            "Rule Name": rule.name,
            "Description": rule.description,
            "Trigger Logic": rule.trigger_logic,
            "Severity": rule.severity,
            "Category": rule.category,
            "Realtime Supported": "Yes" if rule.realtime_supported else "No",
        }
        for rule in RULE_DEFINITIONS
    ]
    logger.info("Built %d executable rule definition row(s)", len(rows))
    return rows


def triggered_indicators(row: pd.Series, mode: RuleMode) -> list[dict[str, str]]:
    logger.info("Collecting triggered indicators for mode=%s", mode)
    columns = HISTORICAL_RULE_COLUMNS if mode == "historical" else REALTIME_RULE_COLUMNS
    indicators = []
    for column in columns:
        if int(row.get(column, 0) or 0) > 0:
            indicators.append(asdict(RULES_BY_COLUMN[column]))
    logger.info("Collected %d triggered indicator(s)", len(indicators))
    return indicators
