import pandas as pd

from app.pipelines.similarity import score_historical_similarity
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
