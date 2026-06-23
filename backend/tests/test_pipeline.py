import pandas as pd

from app.pipelines.similarity import score_historical_similarity
from app.pipelines.risk_scoring import (
    assign_risk_level,
    calculate_final_risk_score,
    escalate_risk_score,
    normalize_rule_count,
)
from app.services.realtime_service import RealtimeService
from app.services.training_service import TrainingService


def test_training_and_realtime_pipeline_runs_from_scratch():
    training = TrainingService().retrain()
    assert training["status"] == "trained"
    assert training["metrics"]["train_records"] > 0

    claim = {
        "ClaimId": "PX001",
        "Gender": "F",
        "Age": 45,
        "ServiceDateFrom": "2024-05-12",
        "PlaceOfService": "11",
        "LineNumber": 1,
        "ProcedureCode": "92014",
        "ProcedureName": "Comprehensive Eye Exam",
        "Modifier": "59",
        "Modifier2": "",
        "Modifier3": "",
        "Primary_Diagnosis_Pointer": "1",
        "Primary_Diagnosis": "",
        "LONG_DESCRIPTION": "Routine eye exam",
        "ClaimLineTotalPaid": 80,
        "AmtCharged": 250,
        "AllowedUnits": 2,
        "AmtDisallowed": 0,
        "AmtEligible": 100,
        "AmtCopay": 20,
        "AmtCoinsurance": 0,
        "AmtDeductible": 0,
        "ProviderNPI": "1234567890",
        "GroupId": "G1",
        "GroupNumber": "GRP100",
        "LOB": "COMM",
        "CoverageCode": "PPO",
        "State": "OH",
    }
    result = RealtimeService().analyze_claims([claim])
    assessment = result["assessments"][0]
    assert assessment["risk_level"] in {"Low", "Medium", "High"}
    assert assessment["rule_flag_count"] >= 4
    assert assessment["narrative"]["metadata"]["llm_success"] in {True, False}


def test_similarity_layer_promotes_close_historical_match():
    realtime = {
        "ClaimId": "RTSIM1",
        "LineNumber": 1,
        "ProviderNPI": "111",
        "State": "OH",
        "LOB": "COMM",
        "CoverageCode": "PPO",
        "ProcedureCode": "92014",
        "Age": 45,
        "Rule_Flag_Count": 2,
        "AmtCharged": 120,
        "AmtEligible": 100,
        "ClaimLineTotalPaid": 80,
        "AllowedUnits": 1,
    }
    historical = {
        **realtime,
        "ClaimId": "HISTSIM1",
        "Flag": "Exam after Comprehensive",
    }
    anomaly_stats = {
        "means": {
            "Age": 40,
            "Rule_Flag_Count": 1,
            "AmtCharged": 100,
            "AmtEligible": 90,
            "ClaimLineTotalPaid": 70,
            "AllowedUnits": 1,
        },
        "stds": {
            "Age": 10,
            "Rule_Flag_Count": 1,
            "AmtCharged": 20,
            "AmtEligible": 20,
            "ClaimLineTotalPaid": 20,
            "AllowedUnits": 1,
        },
    }

    result = score_historical_similarity(
        realtime=pd.DataFrame([realtime]),
        historical=pd.DataFrame([historical]),
        anomaly_stats=anomaly_stats,
    )[0]

    assert result["similarity_above_threshold"] is True
    assert result["historical_pattern"] == "Exam after Comprehensive"


def test_similarity_uses_same_member_history_before_population_keys():
    realtime = {
        "ClaimId": "RT-MEMBER",
        "MemberId": "MEM-1",
        "LineNumber": 1,
        "ProviderNPI": "111",
        "State": "OH",
        "LOB": "COMM",
        "CoverageCode": "PPO",
        "ProcedureCode": "92014",
        "Age": 45,
        "Rule_Flag_Count": 2,
        "AmtCharged": 120,
        "AmtEligible": 100,
        "ClaimLineTotalPaid": 80,
        "AllowedUnits": 1,
    }
    historical = [
        {
            **realtime,
            "ClaimId": "HIST-SAME-MEMBER",
            "ProviderNPI": "999",
            "State": "TX",
            "LOB": "MEDICARE",
            "CoverageCode": "HMO",
            "Flag": "Exam after Comprehensive",
        },
        {
            **realtime,
            "ClaimId": "HIST-OTHER-MEMBER",
            "MemberId": "MEM-2",
            "Flag": "CCI Edits Claims",
        },
    ]
    anomaly_stats = {
        "means": {feature: 0 for feature in ["Age", "Rule_Flag_Count", "AmtCharged", "AmtEligible", "ClaimLineTotalPaid", "AllowedUnits"]},
        "stds": {feature: 1 for feature in ["Age", "Rule_Flag_Count", "AmtCharged", "AmtEligible", "ClaimLineTotalPaid", "AllowedUnits"]},
    }

    result = score_historical_similarity(
        realtime=pd.DataFrame([realtime]),
        historical=pd.DataFrame(historical),
        anomaly_stats=anomaly_stats,
    )[0]

    assert result["similarity_above_threshold"] is True
    assert result["historical_claim_id"] == "HIST-SAME-MEMBER"
    assert result["historical_member_id"] == "MEM-1"


def test_realtime_claim_lines_are_aggregated_after_individual_scoring():
    service = object.__new__(RealtimeService)
    line_assessments = [
        {
            "claim_id": "CLUB-1",
            "member_id": "MEM-1",
            "line_number": line_number,
            "provider_npi": "111",
            "procedure_code": f"CODE-{line_number}",
            "procedure_name": f"Procedure {line_number}",
            "risk_level": "Low",
            "final_risk_score": 0.2 + (line_number / 100),
            "confidence_level": confidence,
            "unexpected_pattern_score": anomaly,
            "rule_flag_count": rule_count,
            "triggered_indicators": indicators,
            "predicted_pattern": pattern,
            "category": "Coding Review" if indicators else "Billing Pattern",
            "top_reason": indicators[0]["name"] if indicators else "Unexpected amount",
            "recommended_action": "Review.",
            "historical_match": {
                "similarity_score": 0.0,
                "above_threshold": False,
                "pattern": "",
                "pattern_family": "",
                "confidence": 0.0,
                "case_priority": "",
            },
            "details": {
                "raw_unexpected_pattern_score": raw_anomaly,
            },
        }
        for line_number, confidence, anomaly, raw_anomaly, rule_count, indicators, pattern in [
            (
                1,
                0.45,
                0.10,
                1.0,
                1,
                [{
                    "rule_id": "R001",
                    "name": "Rule one",
                    "description": "First rule",
                    "severity": "Medium",
                    "category": "Coding Review",
                }],
                "Pattern A",
            ),
            (
                2,
                0.90,
                0.20,
                2.0,
                2,
                [
                    {
                        "rule_id": "R001",
                        "name": "Rule one",
                        "description": "First rule",
                        "severity": "Medium",
                        "category": "Coding Review",
                    },
                    {
                        "rule_id": "R002",
                        "name": "Rule two",
                        "description": "Second rule",
                        "severity": "High",
                        "category": "Billing Review",
                    },
                ],
                "Pattern B",
            ),
            (3, 0.60, 0.30, 3.0, 0, [], "Pattern C"),
            (
                4,
                0.70,
                0.40,
                4.0,
                1,
                [{
                    "rule_id": "R002",
                    "name": "Rule two",
                    "description": "Second rule",
                    "severity": "High",
                    "category": "Billing Review",
                }],
                "Pattern D",
            ),
        ]
    ]

    assessments = service._aggregate_claim_assessments(line_assessments)

    assert len(assessments) == 1
    assessment = assessments[0]
    assert assessment["line_count"] == 4
    assert assessment["line_numbers"] == [1, 2, 3, 4]
    assert assessment["line_number"] == 2
    assert assessment["unexpected_pattern_score"] == 0.25
    assert assessment["details"]["raw_unexpected_pattern_score"] == 2.5
    assert assessment["confidence_level"] == 0.9
    assert assessment["predicted_pattern"] == "Pattern B"
    assert assessment["rule_flag_count"] == 4
    assert assessment["triggered_indicators"][0]["occurrence_count"] == 2
    assert assessment["triggered_indicators"][0]["line_numbers"] == [1, 2]
    assert assessment["triggered_indicators"][1]["occurrence_count"] == 2
    assert assessment["triggered_indicators"][1]["line_numbers"] == [2, 4]
    assert len(assessment["details"]["line_assessments"]) == 4
    assert assessment["final_risk_score"] == calculate_final_risk_score(
        normalize_rule_count(4),
        0.9,
        0.25,
    )


def test_rule_count_curve_accelerates_after_first_rule_and_caps_at_nine():
    scores = [normalize_rule_count(count) for count in range(11)]

    assert scores[0] == 0.0
    assert scores[1] == 1 / 9
    assert scores[2] > 2 / 9
    assert scores[3] > 3 / 9
    assert scores[9] == 1.0
    assert scores[10] == 1.0
    assert scores == sorted(scores)


def test_risk_escalation_is_smooth_progressive_and_bounded():
    assert escalate_risk_score(0.40) == 0.40
    assert escalate_risk_score(0.45) > 0.45
    assert escalate_risk_score(0.55) > escalate_risk_score(0.50)
    assert escalate_risk_score(0.60) - 0.60 > escalate_risk_score(0.45) - 0.45
    assert escalate_risk_score(1.00) == 1.00
    assert escalate_risk_score(1.50) == 1.00

    samples = [escalate_risk_score(index / 100) for index in range(101)]
    assert samples == sorted(samples)
    assert all(0.0 <= score <= 1.0 for score in samples)


def test_risk_levels_use_forty_and_fifty_five_percent_thresholds():
    assert assign_risk_level(0.399999) == "Low"
    assert assign_risk_level(0.40) == "Medium"
    assert assign_risk_level(0.549999) == "Medium"
    assert assign_risk_level(0.55) == "High"
