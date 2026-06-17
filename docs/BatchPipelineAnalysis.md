# Batch Pipeline Reverse Engineering

## Source

The source is `batch.py`, exported from a Fabric/Synapse PySpark notebook. The export is malformed: much of the JSON quoting and code punctuation is missing. However, the step headings, code fragments, Spark table names, output messages, and embedded execution output preserve the pipeline logic.

## Batch Purpose

The batch pipeline performs historical processing:

1. Load historical claims from a Lakehouse CSV.
2. Load rules from an Excel workbook.
3. Clean both datasets for Delta table compatibility.
4. Apply deterministic claim rules.
5. Train a multiclass supervised pattern model.
6. Persist Spark ML artifacts.
7. Compute numeric anomaly scores.
8. Combine the three risk layers.
9. Generate deterministic explanations.
10. Produce gold tables and metadata tables.

## Step 1: Load Claims

Notebook behavior:

- Reads `Files/claims.csv` using `spark.read.csv`.
- Uses `header=True`.
- Uses `inferSchema=True`.
- Displays first five rows.
- Prints schema.

Modern replacement:

- Read `backend/app/data/historical_claims.csv` using Pandas.
- Generate the file if missing.
- Preserve the canonical claim schema plus `Flag`.

## Step 2: Load Rules Excel

Notebook behavior:

- Uses Pandas to read `lakehouse/default/Files/Sample_Rules_For_ML.xlsx`.
- Converts all columns to string before creating a Spark DataFrame.
- Displays rows and schema.

Modern replacement:

- Use OpenPyXL/Pandas to read `backend/app/data/rules.xlsx`.
- Keep rules editable by business users.

## Step 3: Clean Rules Table Header

Notebook behavior:

- Reads Excel with `header=None`.
- Uses row 3 as the header.
- Drops rows above row 3.
- Drops rows where `Item` is null.
- Resets index.
- Converts all columns to string.
- Converts Pandas DataFrame to Spark.

Modern replacement:

- Use a direct explicit header with the required business columns:
  - Rule Id
  - Rule Name
  - Description
  - Trigger Logic
  - Severity
  - Category

The new rules workbook is simpler and intentionally business-editable.

## Step 4: Clean Columns and Save Raw Tables

Notebook behavior:

- Cleans claim and rule column names by replacing spaces with underscores.
- Removes Delta-disallowed characters.
- Saves claims to `claims_raw` Delta table.
- Saves rules to `rules_raw` Delta table.

Modern replacement:

- Use canonical field names directly.
- Avoid Delta tables.
- Keep source files as CSV and Excel.

## Step 5: Deterministic Rules Engine

The notebook labels this as "RULES ENGINE v1" and states that it implements nine rules supported by the current dataset.

### Typed Columns

The notebook creates:

- `ServiceDate` from `ServiceDateFrom`.
- `AmtCharged_num`
- `AmtEligible_num`
- `ClaimLineTotalPaid_num`
- `AmtDisallowed_num`
- `AmtCopay_num`
- `AmtCoinsurance_num`
- `AmtDeductible_num`

Modern replacement:

- Numeric columns are coerced with Pandas `to_numeric`.
- Dates are parsed with Pandas `to_datetime`.
- Original API-facing field names are preserved.

### Helper Code Sets

Exam codes:

- 92002
- 92004
- 92012
- 92014
- S0620
- S0621

Add-on codes:

- V2750
- V2755
- V2760

### R006: Modifier 59 on Vision Codes

Trigger:

- `ProcedureCode` starts with `92` or `V`.
- Any of `Modifier`, `Modifier2`, or `Modifier3` equals `59`.

Output column:

- `R006_Modifier59_Flag`

### R007: High Billed-to-Allowed Ratio

Trigger:

- `AmtEligible_num > 0`.
- `AmtCharged_num / AmtEligible_num > 2.0`.

Output column:

- `R007_High_Billed_to_Allowed_Flag`

### R008: Excessive Units for Exam Codes

Trigger:

- `ProcedureCode` is one of the exam codes.
- `AllowedUnits > 1`.

Output column:

- `R008_Excessive_Units_Exam_Flag`

### R009: Invalid CPT for Vision Plan

Trigger:

- `ProcedureCode` does not start with `92`.
- `ProcedureCode` does not start with `V`.

Output column:

- `R009_Invalid_Vision_Code_Flag`

### R013: Provider High Exam Volume

Historical aggregation rule:

1. Mark each claim as `is_exam` when `ProcedureCode` is an exam code.
2. Group by `ProviderNPI`.
3. Sum `is_exam` to `provider_exam_count`.
4. Compute approximately the 99th percentile threshold.
5. Flag providers with count greater than or equal to that threshold.

Output column:

- `R013_Provider_High_Exam_Volume_Flag`

Realtime exclusion:

- Not applied in realtime because incoming claims do not provide provider history.

### R014: Provider High Material Volume

Historical aggregation rule:

1. Mark each claim as `is_material` when `ProcedureCode` starts with `V`.
2. Group by `ProviderNPI`.
3. Sum `is_material` to `provider_material_count`.
4. Compute approximately the 99th percentile threshold.
5. Flag providers with count greater than or equal to that threshold.

Output column:

- `R014_Provider_High_Material_Volume_Flag`

### R015: Provider High Average Billed Amount

Historical aggregation rule:

1. Group by `ProviderNPI`.
2. Average `AmtCharged_num` to `provider_avg_billed`.
3. Compute approximately the 99th percentile threshold.
4. Flag providers with average greater than or equal to that threshold.

Output column:

- `R015_Provider_High_Avg_Billed_Flag`

### R016: Provider High Add-on Usage

Historical aggregation rule:

1. Mark add-on claims using add-on codes V2750, V2755, and V2760.
2. Mark material claims where `ProcedureCode` starts with `V`.
3. Group by `ProviderNPI`.
4. Compute `provider_addon_count`.
5. Compute `provider_material_count_for_ratio`.
6. Compute `provider_addon_ratio = provider_addon_count / provider_material_count_for_ratio`.
7. Compute approximately the 99th percentile threshold.
8. Flag providers with ratio greater than or equal to that threshold.

Output column:

- `R016_Provider_High_Addon_Usage_Flag`

### R017: Missing Diagnosis

Trigger:

- `Primary_Diagnosis` is null.
- Or `Primary_Diagnosis` is empty after trimming.

Output column:

- `R017_Missing_Diagnosis_Flag`

### Rule Flag Count

Notebook sums all nine historical rule columns:

```text
Rule_Flag_Count = sum(all historical rule flags)
```

Output table:

- `claims_with_rules`

## Step 6: Supervised Pattern Model

The notebook uses a multiclass supervised classifier. It is not binary fraud detection.

### Input Table

- Reads `claims_with_rules`.
- Keeps only rows where `Flag` is not null and not empty.

### Numeric Cleaning

Numeric fields are null-filled with zero:

- Age
- Rule_Flag_Count
- AmtCharged_num
- AmtEligible_num
- ClaimLineTotalPaid_num
- AllowedUnits

### Feature Engineering

Creates:

```text
BilledAllowedRatio =
  AmtCharged_num / AmtEligible_num when AmtEligible_num > 0
  else 0
```

### Categorical Cleaning

Categorical fields are null-filled or empty-filled with `UNKNOWN`:

- ProcedureCode
- Gender
- State
- LOB
- CoverageCode

### Label

The target column is `Flag`.

Known class mapping printed by the notebook:

```text
0 -> CCI Edits Claims
1 -> Exam after Comprehensive
2 -> Bilateral Claims
3 -> Two Exams in One day
```

Note: The user-facing requirement spells the last value as `Two Exams in One Day`. The POC normalizes to that capitalization.

### Spark Pipeline Stages

Notebook stages:

1. `StringIndexer` for `Flag` to `FraudPatternLabel`.
2. `StringIndexer` for each categorical field.
3. `OneHotEncoder` for each indexed categorical field.
4. `VectorAssembler`.
5. `RandomForestClassifier`.

### Model Inputs

Numeric features:

- Age
- Rule_Flag_Count
- AmtCharged_num
- AmtEligible_num
- ClaimLineTotalPaid_num
- AllowedUnits
- BilledAllowedRatio

Encoded categorical features:

- ProcedureCode
- Gender
- State
- LOB
- CoverageCode

### Classifier Settings

Recovered notebook settings:

- `RandomForestClassifier`
- `maxDepth=8`
- `numTrees=100`
- `seed=42`
- `predictionCol=PredictedPatternLabel`
- `probabilityCol=PredictedProbabilities`

### Metrics

The notebook evaluates:

- Accuracy
- F1 score

### ML Risk Score

The notebook computes:

```text
ML_RiskScore = max(PredictedProbabilities)
```

Output table:

- `claims_with_risk_ml`

## Artifact Persistence

The notebook saves Spark artifacts under `Files/fraud_artifacts`:

- One `StringIndexerModel` per categorical field.
- One `OneHotEncoderModel` per categorical field.
- `assembler`
- `rf_model`
- Python `metadata.pkl`.

The metadata contains:

- `index_to_label`
- `numeric_features`
- `categorical_features`

Modern replacement:

- `feature_pipeline.joblib`
- `rf_model.joblib`
- `encoders.joblib`
- `metadata.json`
- `anomaly_stats.json`
- `training_metrics.json`

## Step 7: Numeric Anomaly Encoder and Three-Layer Risk Score

Input tables:

- `claims_with_rules`
- `claims_with_risk_ml`

Numeric features:

- Age
- Rule_Flag_Count
- AmtCharged_num
- AmtEligible_num
- ClaimLineTotalPaid_num
- AllowedUnits
- BilledAllowedRatio

The notebook:

1. Fills null numeric values with zero.
2. Computes `BilledAllowedRatio`.
3. Computes mean and standard deviation for each numeric feature.
4. Replaces missing or zero standard deviation with `1.0`.
5. Computes z-score columns `Z_<feature>`.
6. Computes:

```text
AnomalyScore = sqrt(sum(zscore^2))
```

7. Computes max anomaly score.
8. Computes:

```text
AnomalyScore_Normalized = AnomalyScore / max_anom
```

9. Joins `ML_RiskScore` from the supervised output by `ClaimId` and `LineNumber`.
10. Computes `Rule_Flag_Count_Normalized` by dividing by max historical rule count in the joined dataset.
11. Fills missing `ML_RiskScore` with 0.
12. Computes:

```text
Combined_3Layer_RiskScore =
  0.4 * Rule_Flag_Count_Normalized
  + 0.3 * ML_RiskScore_Filled
  + 0.3 * AnomalyScore_Normalized
```

Output table:

- `claims_with_risk_deep`

## Steps 8 and 9: Explainability and Gold Table

The notebook creates:

- `TriggeredRulesText`
- `TopAnomalyFeature`
- `Short_Explanation`
- `Long_Explanation`
- `AI_Case_Summary`

Then it selects a Power BI-ready gold table:

- Claim identity fields
- Provider and service fields
- Risk layer fields
- Numeric financial fields
- Explanations

The POC replaces hardcoded explanation text with LLM-backed business narrative generation.

## Step 10: Metadata, Confidence, Priority, Family

The notebook creates:

- `anomaly_stats` Delta table with feature, mean, and standard deviation.
- `rule_metadata` Delta table with rule name, description, severity, and category.
- `fraud_scoring_gold_enhanced` with:
  - `FraudPatternConfidence = ML_RiskScore`
  - `CasePriority`
  - `FraudPatternFamily`

Recovered priority thresholds:

- High: final score >= 0.85
- Medium: final score >= 0.60
- Low otherwise

The user requirement overrides realtime risk level thresholds for the POC:

- High >= 0.75
- Medium >= 0.50
- Low < 0.50

## Dependencies Removed

The modern implementation removes:

- Spark
- Delta tables
- Fabric Lakehouse APIs
- Synapse widgets
- `notebookutils`
- `mssparkutils`
- Spark ML artifacts
- MLflow run widgets

