# Data Model

## Claim Schema

The realtime sample establishes the canonical claim schema. Historical data uses the same schema plus `Flag`.

| Field | Type | Notes |
| --- | --- | --- |
| ClaimId | string | Claim identifier. |
| Gender | string | Common values: M, F, U. |
| Age | integer | Member age. |
| ServiceDateFrom | string/date | Parsed during processing. |
| PlaceOfService | string | Place of service code. |
| LineNumber | integer | Claim line number. |
| ProcedureCode | string | CPT/HCPCS-style procedure code. |
| ProcedureName | string | Procedure display name. |
| Modifier | string | Primary modifier. |
| Modifier2 | string | Secondary modifier. |
| Modifier3 | string | Tertiary modifier. |
| Primary_Diagnosis_Pointer | string | Diagnosis pointer. |
| Primary_Diagnosis | string | Primary diagnosis code. |
| LONG_DESCRIPTION | string | Diagnosis or service description. |
| ClaimLineTotalPaid | float | Paid amount. |
| AmtCharged | float | Charged amount. |
| AllowedUnits | float | Allowed unit count. |
| AmtDisallowed | float | Disallowed amount. |
| AmtEligible | float | Eligible or allowed amount. |
| AmtCopay | float | Copay amount. |
| AmtCoinsurance | float | Coinsurance amount. |
| AmtDeductible | float | Deductible amount. |
| ProviderNPI | string | Provider identifier. |
| GroupId | string | Group identifier. |
| GroupNumber | string | Group number. |
| LOB | string | Line of business. |
| CoverageCode | string | Coverage type. |
| State | string | Service/member state. |
| Flag | string | Historical only, supervised pattern label. |

## Historical Flag Values

The generated historical dataset includes:

- CCI Edits Claims
- Exam after Comprehensive
- Bilateral Claims
- Two Exams in One Day

## Rule Workbook Schema

`backend/app/data/rules.xlsx`

The workbook has two sheets:

- `Business Rules`: the business rule catalog from the supplied operational definitions.
- `Executable Rules`: the deterministic POC rules currently scored by code.

### `Business Rules`

| Column | Purpose |
| --- | --- |
| Section | Catalog section, for example Operational Rules, Shared Client Risks, or Special. |
| Item | Business item number or topic label. |
| Analysis | Business analysis or category label. |
| Risk Level | Numeric risk level from the supplied catalog. |
| Operational Definition | Business rule description. |
| Routine | `x` when the rule applies to routine claims. |
| Medical | `x` when the rule applies to medical claims. |
| Both | `x` when the rule applies to both routine and medical claims. |
| Frequency | Frequency marker from the supplied catalog. |
| Implementation Status | `Executable` when mapped to a current deterministic POC rule, otherwise `Catalog Only`. |
| Executable Rule Ids | Current POC rule ids mapped to the business rule. |
| Executable Flag Columns | Output columns produced by those POC rule ids. |
| Realtime Supported | Whether the mapped executable rule can run in realtime mode. |
| Implementation Notes | Notes about implemented scope or missing source data. |

### `Executable Rules`

| Column | Purpose |
| --- | --- |
| Rule Id | Stable executable rule id, for example R006. |
| Rule Name | Business-friendly executable rule name. |
| Description | Plain-language executable rule description. |
| Trigger Logic | Deterministic trigger definition. |
| Severity | Low, Medium, or High. |
| Category | Rule category used for business grouping. |
| Realtime Supported | Whether the executable rule can run in realtime mode. |

## Rule Output Schema

Historical rule columns:

- `R006_Modifier59_Flag`
- `R007_High_Billed_to_Allowed_Flag`
- `R008_Excessive_Units_Exam_Flag`
- `R009_Invalid_Vision_Code_Flag`
- `R013_Provider_High_Exam_Volume_Flag`
- `R014_Provider_High_Material_Volume_Flag`
- `R015_Provider_High_Avg_Billed_Flag`
- `R016_Provider_High_Addon_Usage_Flag`
- `R017_Missing_Diagnosis_Flag`
- `R100_Two_Exams_One_Day`
- `R101_Exam_After_Comprehensive`
- `R102_CCI_Edit`
- `R103_Bilateral`
- `Rule_Flag_Count`

Realtime rule columns:

- `R006_Modifier59_Flag`
- `R007_High_Billed_to_Allowed_Flag`
- `R008_Excessive_Units_Exam_Flag`
- `R009_Invalid_Vision_Code_Flag`
- `R017_Missing_Diagnosis_Flag`
- `R100_Two_Exams_One_Day`
- `R101_Exam_After_Comprehensive`
- `R102_CCI_Edit`
- `R103_Bilateral`
- `Rule_Flag_Count`

## Artifact Schema

### `metadata.json`

Contains:

- `artifact_version`
- `trained_at`
- `record_count`
- `numeric_features`
- `categorical_features`
- `classes`
- `index_to_label`
- `rule_mode`
- `realtime_supported_rules`
- `historical_rules`
- `risk_weights`
- `risk_thresholds`

### `training_metrics.json`

Contains:

- `trained_at`
- `accuracy`
- `f1_weighted`
- `train_records`
- `test_records`
- `class_counts`
- `dataset_statistics`
- `artifact_files`

### `anomaly_stats.json`

Contains:

- `features`
- `means`
- `stds`
- `max_anomaly_score`
- `computed_at`

### `feature_pipeline.joblib`

Scikit-Learn preprocessing pipeline containing:

- Numeric passthrough columns.
- One-hot encoding for categorical fields.

### `rf_model.joblib`

Scikit-Learn `RandomForestClassifier` trained on encoded features.

### `encoders.joblib`

Auxiliary encoding metadata. The current implementation stores a label encoder and feature lists.
