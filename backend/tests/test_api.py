from fastapi.testclient import TestClient

from main import app
from app.schemas.claim import validate_claim_payload


client = TestClient(app)


def test_sample_data_and_status_endpoints():
    sample = client.get("/api/sample-data")
    assert sample.status_code == 200
    assert sample.json()["historical_claims"]["record_count"] >= 5000

    status = client.get("/api/training/status")
    assert status.status_code == 200
    assert "trained" in status.json()


def test_claim_analyze_json_endpoint():
    client.post("/api/training/retrain")
    payload = {
        "claims": [
            {
                "ClaimId": "API001",
                "Gender": "M",
                "Age": 67,
                "ServiceDateFrom": "2024-04-03",
                "PlaceOfService": "22",
                "LineNumber": 1,
                "ProcedureCode": "99213",
                "ProcedureName": "Office Visit Established Patient",
                "Modifier": "",
                "Modifier2": "",
                "Modifier3": "",
                "Primary_Diagnosis_Pointer": "1",
                "Primary_Diagnosis": "E11.9",
                "LONG_DESCRIPTION": "Diabetes type 2 without complications",
                "ClaimLineTotalPaid": 0,
                "AmtCharged": 180,
                "AllowedUnits": 1,
                "AmtDisallowed": 20,
                "AmtEligible": 150,
                "AmtCopay": 0,
                "AmtCoinsurance": 0,
                "AmtDeductible": 0,
                "ProviderNPI": "9988776655",
                "GroupId": "G2",
                "GroupNumber": "GRP200",
                "LOB": "MEDICARE",
                "CoverageCode": "HMO",
                "State": "FL",
            }
        ]
    }
    response = client.post("/api/claims/analyze", json=payload)
    assert response.status_code == 200
    body = response.json()
    assert body["count"] == 1
    assert body["assessments"][0]["triggered_indicators"][0]["rule_id"] == "R009"


def test_claim_payload_accepts_currency_strings():
    claims = validate_claim_payload(
        {
            "claims": [
                {
                    "ClaimId": "CURJSON1",
                    "AmtCharged": "$130.00",
                    "AmtEligible": "$58.35",
                    "ClaimLineTotalPaid": "$58.35",
                    "AllowedUnits": "1",
                }
            ]
        }
    )

    assert claims[0]["AmtCharged"] == 130.0
    assert claims[0]["AmtEligible"] == 58.35
