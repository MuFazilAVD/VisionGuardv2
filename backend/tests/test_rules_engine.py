import pandas as pd

from app.pipelines.rules_engine import apply_rules, executable_rule_definitions_for_workbook, rule_definitions_for_workbook


def test_realtime_rules_trigger_expected_flags():
    claims = pd.DataFrame(
        [
            {
                "ClaimId": "T1",
                "ProcedureCode": "92014",
                "Modifier": "59",
                "Modifier2": "",
                "Modifier3": "",
                "AmtCharged": 300,
                "AmtEligible": 100,
                "AllowedUnits": 2,
                "Primary_Diagnosis": "",
            },
            {
                "ClaimId": "T2",
                "ProcedureCode": "99213",
                "AmtCharged": 90,
                "AmtEligible": 100,
                "AllowedUnits": 1,
                "Primary_Diagnosis": "H52.4",
            },
        ]
    )

    scored = apply_rules(claims, mode="realtime")

    assert scored.loc[0, "R006_Modifier59_Flag"] == 1
    assert scored.loc[0, "R007_High_Billed_to_Allowed_Flag"] == 1
    assert scored.loc[0, "R008_Excessive_Units_Exam_Flag"] == 1
    assert scored.loc[0, "R017_Missing_Diagnosis_Flag"] == 1
    assert scored.loc[0, "Rule_Flag_Count"] == 4
    assert scored.loc[1, "R009_Invalid_Vision_Code_Flag"] == 1


def test_realtime_rules_parse_currency_amounts():
    claims = pd.DataFrame(
        [
            {
                "ClaimId": "CUR1",
                "ProcedureCode": "92014",
                "AmtCharged": "$300.00",
                "AmtEligible": "$100.00",
                "AllowedUnits": "1",
                "Primary_Diagnosis": "H52.4",
            }
        ]
    )

    scored = apply_rules(claims, mode="realtime")

    assert scored.loc[0, "AmtCharged"] == 300.0
    assert scored.loc[0, "AmtEligible"] == 100.0
    assert scored.loc[0, "R007_High_Billed_to_Allowed_Flag"] == 1


def test_realtime_rules_use_historical_claim_day_context():
    claims = pd.DataFrame(
        [
            {
                "ClaimId": "CTX1",
                "ServiceDateFrom": "2024-05-12",
                "ProcedureCode": "92014",
                "AmtCharged": 120,
                "AmtEligible": 100,
                "AllowedUnits": 1,
                "Primary_Diagnosis": "H52.4",
            }
        ]
    )
    historical_context = pd.DataFrame(
        [
            {
                "ClaimId": "CTX1",
                "ServiceDateFrom": "2024-05-12",
                "ProcedureCode": "92012",
                "AmtCharged": 90,
                "AmtEligible": 80,
                "AllowedUnits": 1,
                "Primary_Diagnosis": "H52.4",
            }
        ]
    )

    scored = apply_rules(claims, mode="realtime", context_df=historical_context)

    assert scored.loc[0, "R100_Two_Exams_One_Day"] == 1
    assert scored.loc[0, "R101_Exam_After_Comprehensive"] == 1


def test_business_rule_catalog_matches_pasted_rules():
    rules = rule_definitions_for_workbook()
    executable_rules = executable_rule_definitions_for_workbook()

    assert len(rules) == 75
    assert rules[0]["Section"] == "Operational Rules"
    assert rules[0]["Item"] == "1"
    assert rules[0]["Risk Level"] == "2"
    assert "Correct Coding Edits" in rules[0]["Operational Definition"]
    assert rules[-1]["Section"] == "Special"
    assert rules[-1]["Operational Definition"] == "PPE"

    modifier_59_rule = next(
        rule
        for rule in rules
        if rule["Section"] == "Operational Rules" and rule["Item"] == "38"
    )
    assert modifier_59_rule["Implementation Status"] == "Executable"
    assert modifier_59_rule["Executable Rule Ids"] == "R006"

    assert len(executable_rules) == 13
