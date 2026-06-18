# Realtime Pipeline Reverse Engineering

## Source

The source is `realtime.py`, a valid JSON notebook export from Fabric/Synapse PySpark. It contains 11 cells.

## Realtime Purpose

The realtime pipeline scores one uploaded batch of incoming claims using previously trained artifacts. It applies only rules that can be evaluated from the incoming claim fields and then combines rule, supervised pattern, and anomaly layers into a final business risk assessment.

## Realtime Step 1: Load Incoming Claims

Notebook behavior:

- Looks for `Files/realtime_claims.csv`.
- Uses `mssparkutils.fs.ls("Files/")` to check existence.
- If missing, creates an empty Spark DataFrame.
- If present, reads CSV with `header=True` and `inferSchema=True`.
- Displays rows and schema.

Modern replacement:

- Accept CSV upload or JSON payload through `POST /visionguardv2/api/claims/analyze`.
- Accept one or more claims in a request.
- Use the same canonical schema as `realtime_claims.csv`.
- Preserve `MemberId` as an identifier and use it for member-level historical context; do not use it as a raw model feature.

## Realtime Step 2: Normalize Types

Notebook behavior:

- Casts `ProcedureCode`, `Modifier`, `Modifier2`, and `Modifier3` to string.
- Casts amount fields to double:
  - `AmtCharged_num`
  - `AmtEligible_num`
  - `ClaimLineTotalPaid_num`
  - `AmtDisallowed_num`
  - `AmtCopay_num`
  - `AmtCoinsurance_num`
  - `AmtDeductible_num`
- Parses `ServiceDate` from `ServiceDateFrom` using `yyyy-MM-dd`.

Modern replacement:

- Use flexible date parsing because the sample CSV contains `5/12/2024` format.
- Preserve original field names in API responses and add computed fields in the assessment output.

## Realtime Step 3: Apply Deterministic Rules

Realtime applies only:

- R006
- R007
- R008
- R009
- R017

Provider-level aggregation rules are deliberately excluded.

### R006: Modifier 59 on Vision Codes

Trigger:

- `ProcedureCode` starts with `92` or `V`.
- `Modifier`, `Modifier2`, or `Modifier3` equals `59`.

### R007: High Billed-to-Allowed Ratio

Trigger:

- `AmtEligible_num > 0`.
- `AmtCharged_num / AmtEligible_num > 2.0`.

### R008: Excessive Units for Exam Codes

Exam codes:

- 92002
- 92004
- 92012
- 92014
- S0620
- S0621

Trigger:

- `ProcedureCode` is an exam code.
- `AllowedUnits > 1`.

### R009: Invalid CPT for Vision Plan

Trigger:

- `ProcedureCode` does not start with `92` or `V`.

### R017: Missing Diagnosis

Trigger:

- `Primary_Diagnosis` is null or empty after trimming.

## Realtime Step 4: Rule Count

The notebook sums the five realtime-supported flags:

```text
Rule_Flag_Count =
  R006 + R007 + R008 + R009 + R017
```

## Realtime Step 5: Supervised Pattern Scoring

The notebook:

1. Starts from rule-scored realtime claims.
2. Computes `BilledAllowedRatio`.
3. Fills numeric nulls with zero.
4. Fills categorical null or empty values with `UNKNOWN`.
5. Loads `metadata.pkl` from `Files/fraud_artifacts`.
6. Loads one `StringIndexerModel` per categorical field.
7. Loads one `OneHotEncoderModel` per categorical field.
8. Loads `assembler`.
9. Loads `rf_model`.
10. Transforms incoming rows.
11. Computes `ML_RiskScore = max(probability vector)`.

Modern replacement:

- Load local joblib feature pipeline and model.
- Keep the same input fields.
- Return predicted pattern and pattern confidence.
- Do not expose technical model terms in UI.

## Realtime Step 6: Numeric Anomaly Scoring

The notebook:

1. Loads `anomaly_stats` Spark table.
2. Builds a dictionary of feature -> mean/std.
3. Computes z-score for each numeric feature.
4. Computes L2 anomaly score.
5. Normalizes by the maximum anomaly score within the incoming realtime batch.

Modern replacement:

- Load `backend/artifacts/anomaly_stats.json`.
- Use training means, standard deviations, and training max anomaly score.
- Compute the same L2 formula.
- Clip normalized anomaly score to 1.0.

## Realtime Step 7: Final Risk Score

Notebook behavior:

```text
Rule_Flag_Count_Normalized = Rule_Flag_Count / 5.0
Final_RiskScore =
  0.4 * Rule_Flag_Count_Normalized
  + 0.3 * ML_RiskScore
  + 0.3 * AnomalyScore_Normalized
```

Modern replacement:

- Preserve exact weights.
- Preserve realtime rule normalization by five supported rules.

## Realtime Step 8: Explainability

The notebook builds deterministic explanation text:

- `TriggeredRulesText`
- `TopAnomalyFeature`
- `ML_Explanation`
- `Short_Explanation`
- `Long_Explanation`
- `AI_Case_Summary`

The notebook uses phrases such as "ML model" and "anomaly detector." These are not allowed in the new UI. The backend can retain technical field names for artifact compatibility, but the frontend and narrative text must use business-friendly language:

- Rules Triggered
- Investigation findings
- Claim assessment
- Review recommendation
- Potential concerns
- Confidence level

## Realtime Step 8.5: Risk Level, Top Reason, Category, Recommended Action

The notebook adds business outputs:

- `Risk_Level`
- `Top_Reason`
- `Category`
- `Recommended_Action`

Embedded output shows examples:

- Invalid vision code becomes `Billing Anomaly`.
- Modifier 59 plus excessive units becomes `Coding Irregularity`.
- Recommended actions vary by risk level and reason.

Modern replacement:

- Use deterministic category and action fallback.
- Let LLM generation produce richer narrative sections when configured.

## Realtime Step 8.6: Final Narrative

The notebook creates a polished deterministic `Final_Narrative`.

Modern replacement:

- Implement `generate_for_claim(claim_data: dict)`.
- Call the LLM endpoint configured by:
  - `OPENAI_BASE_URL`
  - `OPENAI_API_KEY`
  - `OPENAI_MODEL`
- Return deterministic fallback narrative if LLM fails.
- Always return metadata:
  - `model_used`
  - `llm_success`
  - `fallback_reason`

## Realtime Step 9: Final Gold Layer

The notebook selects a final Power BI-ready set of fields:

- ClaimId
- MemberId
- LineNumber
- ServiceDate
- ProcedureCode
- ProcedureName
- ProviderNPI
- State
- LOB
- CoverageCode
- Rule_Flag_Count
- Rule_Flag_Count_Normalized
- TriggeredRulesText
- ML_RiskScore
- ML_Explanation
- AnomalyScore
- AnomalyScore_Normalized
- TopAnomalyFeature
- Final_RiskScore
- Risk_Level
- Short_Explanation
- Long_Explanation
- AI_Case_Summary
- Top_Reason
- Category
- Recommended_Action
- Final_Narrative
- Numeric billing fields

Modern replacement:

- Return structured JSON assessments from the API.
- The frontend renders business fields, not raw Spark table outputs.

## Sample Realtime Output Observed

The embedded notebook output shows three sample claims:

- `RT001`: invalid non-vision code, Medium risk, final score about 0.544.
- `RT002`: modifier 59 plus excessive units, Medium risk, final score about 0.660.
- `RT003`: invalid non-vision code, Low risk, final score about 0.488.

Exact scores will differ in the POC because the unavailable historical training dataset must be regenerated.
