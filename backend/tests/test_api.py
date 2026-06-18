from fastapi.testclient import TestClient

from main import app
from app.schemas.claim import validate_claim_payload


client = TestClient(app)
API_PREFIX = "/visionguardv2/api"
HEALTH_PATH = "/visionguardv2/health"
PRODUCTION_ORIGINS = (
    "https://d2brdeqy144bwg.cloudfront.net",
    "https://d3bkb5k71wphsh.cloudfront.net",
)


def test_production_origins_cors_preflight():
    for production_origin in PRODUCTION_ORIGINS:
        response = client.options(
            f"{API_PREFIX}/sample-data",
            headers={
                "Origin": production_origin,
                "Access-Control-Request-Method": "GET",
            },
        )

        assert response.status_code == 200
        assert response.headers["access-control-allow-origin"] == production_origin


def test_sample_data_and_status_endpoints():
    health = client.get(HEALTH_PATH)
    assert health.status_code == 200

    sample = client.get(f"{API_PREFIX}/sample-data")
    assert sample.status_code == 200
    assert sample.json()["historical_claims"]["record_count"] > 0

    status = client.get(f"{API_PREFIX}/training/status")
    assert status.status_code == 200
    assert "trained" in status.json()


def test_claim_analyze_json_endpoint():
    client.post(f"{API_PREFIX}/training/retrain")
    payload = {
        "claims": [
            {
                "ClaimId": "API001",
                "MemberId": "MEM-API-001",
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
    response = client.post(f"{API_PREFIX}/claims/analyze", json=payload)
    assert response.status_code == 200
    body = response.json()
    assert body["count"] == 1
    assert body["batch_summary"]["total_claims"] == 1
    assert body["batch_summary"]["fraud_count"] in {0, 1}
    assert body["batch_summary"]["summary"]
    assert body["assessments"][0]["member_id"] == "MEM-API-001"
    assert body["assessments"][0]["triggered_indicators"][0]["rule_id"] == "R009"


def test_claim_analyze_csv_preserves_member_id_leading_zeros():
    csv_payload = (
        "ClaimId,MemberId,ProcedureCode,AmtCharged,AmtEligible,ProviderNPI,State,LOB,CoverageCode\n"
        "CSV001,0012345,99213,120,100,1234567890,OH,COMM,PPO\n"
    )

    response = client.post(
        f"{API_PREFIX}/claims/analyze",
        files={"file": ("claims.csv", csv_payload, "text/csv")},
    )

    assert response.status_code == 200
    assert response.json()["assessments"][0]["member_id"] == "0012345"


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


def test_claim_payload_accepts_more_than_five_claims():
    claims = validate_claim_payload(
        {
            "claims": [
                {
                    "ClaimId": f"BATCH{i:03d}",
                    "ProcedureCode": "92014",
                    "AmtCharged": 150,
                    "AmtEligible": 120,
                }
                for i in range(8)
            ]
        }
    )

    assert len(claims) == 8


def test_claim_payload_normalizes_member_id_alias():
    claims = validate_claim_payload(
        {
            "claims": [
                {
                    "ClaimId": "MEMJSON1",
                    "Member ID": 123456,
                }
            ]
        }
    )

    assert claims[0]["MemberId"] == "123456"
