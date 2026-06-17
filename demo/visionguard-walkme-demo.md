# VisionGuard WalkMe Demo

This demo script walks through the current VisionGuard web page from both a business and technical perspective. It is based on the actual React/FastAPI implementation and on a browser-equivalent run of the seeded sample claims.

## Demo Context

VisionGuard is a claims risk assessment proof of concept. The visible user experience is intentionally focused on business review language: claims, risk indicators, confidence, investigation findings, review patterns, and recommended actions.

Technically, the application is a Vite React frontend backed by a FastAPI service. The frontend renders a single analyst workspace. The backend owns sample data, training, rule evaluation, model scoring, anomaly scoring, historical similarity checks, and narrative generation.

Relevant source files:

- Frontend shell: `frontend/src/components/Layout.tsx`
- Main page: `frontend/src/pages/ClaimWorkspace.tsx`
- Frontend API client: `frontend/src/services/api.ts`
- Backend claims endpoint: `backend/app/api/claims.py`
- Realtime service: `backend/app/services/realtime_service.py`
- Rules engine: `backend/app/pipelines/rules_engine.py`
- Risk scoring math: `backend/app/pipelines/risk_scoring.py`
- Seed realtime claims: `realtime_claims.csv`

The frontend build was verified with `npm run build`.

## Opening The Web Page

When you open the VisionGuard page, the first impression is a compact analyst workspace rather than a marketing or dashboard landing page. The screen is built for someone who wants to load claim rows, inspect the claim fields, run assessment, and immediately read the returned results.

The page background is a pale blue-gray canvas. Technically this comes from the CSS variable and Tailwind token `canvas`, set to `#edf2f7`. The body also has two faint grid gradients: one vertical and one horizontal, each spaced every 28 pixels. Business-wise, this gives the page a controlled workbench feeling without distracting from claims data.

The entire app uses the Inter/system sans-serif stack declared in `frontend/src/index.css`. The global text color is `#121826`, named `ink` in the Tailwind configuration. The design language is restrained: borders, soft shadows, compact controls, and dense tabular data.

## Header

At the very top is a sticky header. It stays at the top while you scroll because the header has `sticky top-0 z-20`.

The header has:

- A white translucent background: `bg-white/92`
- A subtle bottom border: `border-b border-line/80`
- A blur effect behind it: `backdrop-blur`
- A max content width of `1440px`
- Horizontal padding that increases at larger viewport sizes

On the left is a square icon tile. The tile is 40 by 40 pixels because it uses the `size-10` utility. It has a blue-tinted background, a border, a slight shadow, and a Phosphor `ShieldCheckered` icon. Business meaning: this is a guarded claims assessment product. Technical meaning: the icon is imported from `@phosphor-icons/react` in `Layout.tsx`.

Next to the icon are two text elements:

- `VisionGuard`
- `Claims Risk Assessment`

`VisionGuard` is small, blue, and semibold. It is the product label. `Claims Risk Assessment` is the main page title, rendered as an `h1`. It can truncate if the viewport is narrow, because it uses `truncate`.

## Page Body

Below the header is the main workspace. It is centered with the same `1440px` max width as the header. The page uses compact padding: `px-3 py-4` on small viewports, increasing slightly on larger screens.

The main page currently renders one major card: `New Claim Batch`. Beneath it, after assessment, the results section appears on the same page.

## New Claim Batch Card

The top card has a rounded border, a light panel background, and a soft shadow. Its top border is highlighted with the `info` color. The business meaning is that this is the primary intake area.

The card title is:

```text
New Claim Batch
```

Directly underneath is:

```text
Sample realtime claims - 3 claims
```

That line is dynamic. It comes from the React state variable `sourceLabel` and the number of claim rows in the `claims` state array.

On first page load, `App.tsx` calls `getSampleData()`, which calls:

```text
GET /visionguard/api/sample-data
```

The backend `SampleDataService` returns summaries for:

- Historical claims
- Rules
- Realtime sample claims

The frontend looks specifically at `sampleData.realtime_claims.preview`. If it has rows and the page has not already seeded claims, the frontend places those preview rows into the editable grid and changes the source label to `Sample realtime claims`.

The seeded file is:

```text
realtime_claims.csv
```

It contains three sample rows: `RT001`, `RT002`, and `RT003`.

## Action Buttons

The header area of the card has four user-facing buttons.

### Sync Engine

The first button says:

```text
Sync Engine
```

It uses the `secondary` button style, so it appears as a white button with a border and dark text. It includes a Phosphor `ArrowsClockwise` icon.

Business meaning: refresh the assessment engine so it reflects the current generated historical data and rules.

Technical behavior:

1. The button calls `runSync()`.
2. `runSync()` calls the `onSync` prop.
3. `onSync` is defined in `App.tsx` as `syncEngine()`.
4. `syncEngine()` calls `retrainAssessmentEngine()`.
5. `retrainAssessmentEngine()` sends:

```text
POST /visionguard/api/training/retrain
```

The backend training flow:

1. Ensures sample data exists.
2. Loads `backend/app/data/historical_claims.csv`.
3. Loads `backend/app/data/rules.xlsx`.
4. Applies historical rules.
5. Prepares numeric and categorical scoring fields.
6. Trains a scikit-learn random forest classifier.
7. Computes anomaly statistics.
8. Writes artifacts to `backend/artifacts`.

The current local training artifact metadata shows:

- Artifact version: `20260617T100328Z`
- Trained at: `2026-06-17T10:03:28.147345+00:00`
- Historical records: `8000`
- Training records: `6400`
- Test records: `1600`
- Accuracy: `0.900625`
- Weighted F1: `0.901003`

Those metrics do not appear on the page, but they explain what the engine sync refreshes.

While the sync is running, the button changes from `Sync Engine` to `Syncing`, and the arrow icon spins. The button is disabled while syncing or while the initial sample data is loading.

On success, the page shows a green inline message:

```text
Synced [formatted date].
```

On failure, it shows a red inline error message.

### Upload CSV

The second button says:

```text
Upload CSV
```

It uses a Phosphor `UploadSimple` icon.

Business meaning: an analyst can bring a claim batch from a CSV file.

Technical behavior:

1. The visible button programmatically clicks a hidden file input.
2. The hidden input accepts `.csv,text/csv`.
3. When a file is selected, the frontend reads it as text.
4. `parseClaimsCsv()` parses it in the browser.
5. The parsed rows replace the current claims grid.
6. The source label changes to the uploaded file name.
7. Existing analysis results are cleared because the input data changed.

The CSV parser supports:

- Comma-separated fields
- Quoted fields
- Escaped double quotes inside quoted values
- CRLF and LF line endings
- Byte-order mark removal from the first header

Upload does not automatically submit the claims. The analyst must still click `Proceed`.

### Add Claim

The third button says:

```text
Add Claim
```

It uses a Phosphor `Plus` icon.

Business meaning: an analyst can manually add another claim line to the batch.

Technical behavior:

1. The button calls `blankClaim()`.
2. A new default claim object is appended to the current `claims` array.
3. Existing results are cleared.

The generated default claim has fields such as:

- Claim ID beginning with `NEW`
- Gender `U`
- Age `40`
- Service date `2024-06-01`
- Procedure code `92014`
- Procedure name `Comprehensive Eye Exam`
- Charged amount `150`
- Eligible amount `120`
- Provider NPI `1234567890`
- State `OH`

### Proceed

The fourth button says:

```text
Proceed
```

It uses a Phosphor `ClipboardText` icon.

Business meaning: submit the current claim batch for risk assessment.

Technical behavior:

1. If there are no claim rows, it sets the error message:

```text
Add at least one claim for assessment.
```

2. If there are claim rows, it sets `busy` to `true`.
3. It clears previous errors.
4. It calls `analyzeClaims(claims)`.
5. The API client sends:

```text
POST /visionguard/api/claims/analyze
```

with JSON:

```json
{
  "claims": [...]
}
```

6. When the response returns, the frontend stores it in `analysis`.
7. The results section appears below the input card.
8. The page scrolls to the results section using `scrollIntoView`.

While processing, the button text changes to:

```text
Processing
```

and the icon becomes a spinning `ArrowsClockwise`.

## Error And Status Messages

There are three possible inline message blocks inside the card body:

- Assessment or upload error
- Sync error
- Sync success message

Error blocks are red-tinted, use a `WarningCircle` icon, and display the returned error message. Success blocks are green-tinted, use a `CheckCircle` icon, and display the sync confirmation.

Business meaning: the analyst gets immediate contextual feedback without leaving the workspace.

Technical meaning: these are conditional React render blocks based on `error`, `syncError`, and `syncMessage`.

## Editable Claims Table

The table is horizontally scrollable because it contains the full incoming claim schema. It is given a minimum width of `3600px`, so the user can inspect many columns without cramming all fields into unreadable widths.

The table header is dark slate with uppercase white text. Each body cell contains an editable input.

The row hover state uses a pale blue background: `hover:bg-blue-50/55`.

Every edit calls:

```text
updateClaim(index, column, value)
```

That updates only the edited field on that row and clears existing assessment results.

### Column List And Meaning

The visible editable columns are:

1. `ClaimId`
2. `Gender`
3. `Age`
4. `ServiceDateFrom`
5. `PlaceOfService`
6. `LineNumber`
7. `ProcedureCode`
8. `ProcedureName`
9. `Modifier`
10. `Modifier2`
11. `Modifier3`
12. `Primary_Diagnosis_Pointer`
13. `Primary_Diagnosis`
14. `LONG_DESCRIPTION`
15. `ClaimLineTotalPaid`
16. `AmtCharged`
17. `AllowedUnits`
18. `AmtDisallowed`
19. `AmtEligible`
20. `AmtCopay`
21. `AmtCoinsurance`
22. `AmtDeductible`
23. `ProviderNPI`
24. `GroupId`
25. `GroupNumber`
26. `LOB`
27. `CoverageCode`
28. `State`

Business definitions:

- `ClaimId`: Claim identifier.
- `Gender`: Member gender value, commonly `M`, `F`, or `U`.
- `Age`: Member age.
- `ServiceDateFrom`: Date of service.
- `PlaceOfService`: Place where service occurred, such as office or outpatient setting.
- `LineNumber`: Claim line number.
- `ProcedureCode`: CPT/HCPCS-style code.
- `ProcedureName`: Human-readable procedure description.
- `Modifier`, `Modifier2`, `Modifier3`: Coding modifiers that can affect billing validity.
- `Primary_Diagnosis_Pointer`: Pointer to the primary diagnosis.
- `Primary_Diagnosis`: Diagnosis code.
- `LONG_DESCRIPTION`: Diagnosis or service description.
- `ClaimLineTotalPaid`: Amount paid on the line.
- `AmtCharged`: Amount billed by the provider.
- `AllowedUnits`: Units allowed or billed for the line.
- `AmtDisallowed`: Amount not allowed.
- `AmtEligible`: Eligible or allowed amount.
- `AmtCopay`: Member copay.
- `AmtCoinsurance`: Member coinsurance.
- `AmtDeductible`: Deductible amount.
- `ProviderNPI`: Provider identifier.
- `GroupId`: Group identifier.
- `GroupNumber`: Group number.
- `LOB`: Line of business.
- `CoverageCode`: Coverage type.
- `State`: State associated with the claim context.

Technical notes:

- Labels are generated by replacing underscores with spaces.
- `LONG_DESCRIPTION` and `ProcedureName` receive wider inputs.
- `ServiceDateFrom` and `ProviderNPI` receive medium-width inputs.
- Amount fields receive amount-oriented width.
- All values are posted as the current frontend state values.
- Backend validation trims strings and parses numeric fields.

## Initial Seeded Rows

### Row 1: RT001

```text
ClaimId: RT001
Gender: F
Age: 45
ServiceDateFrom: 5/12/2024
PlaceOfService: 11
LineNumber: 1
ProcedureCode: 99213
ProcedureName: Office Visit Established Patient
Modifier: 25
Modifier2: blank
Modifier3: blank
Primary_Diagnosis_Pointer: 1
Primary_Diagnosis: H52.4
LONG_DESCRIPTION: Routine eye exam
ClaimLineTotalPaid: 80
AmtCharged: 120
AllowedUnits: 1
AmtDisallowed: 0
AmtEligible: 100
AmtCopay: 20
AmtCoinsurance: 0
AmtDeductible: 0
ProviderNPI: 1234567890
GroupId: G1
GroupNumber: GRP100
LOB: COMM
CoverageCode: PPO
State: OH
```

Business reading: this is a commercial PPO claim in Ohio for a 45-year-old female member. The service is an office visit code, not a typical vision-plan code. The charged amount is 120 and eligible amount is 100.

Technical reading: `99213` does not start with `92` or `V`, so it can trigger the invalid vision-plan code rule.

### Row 2: RT002

```text
ClaimId: RT002
Gender: M
Age: 67
ServiceDateFrom: 4/3/2024
PlaceOfService: 22
LineNumber: 1
ProcedureCode: 92014
ProcedureName: Comprehensive Eye Exam
Modifier: 59
Modifier2: blank
Modifier3: blank
Primary_Diagnosis_Pointer: 1
Primary_Diagnosis: E11.9
LONG_DESCRIPTION: Diabetes type 2 without complications
ClaimLineTotalPaid: 0
AmtCharged: 180
AllowedUnits: 2
AmtDisallowed: 20
AmtEligible: 150
AmtCopay: 0
AmtCoinsurance: 0
AmtDeductible: 0
ProviderNPI: 9988776655
GroupId: G2
GroupNumber: GRP200
LOB: MEDICARE
CoverageCode: HMO
State: FL
```

Business reading: this is a Medicare HMO claim in Florida for a 67-year-old male member. It is a comprehensive eye exam. It has modifier `59` and two allowed units, both of which are review-relevant.

Technical reading: `92014` is a vision exam code. Modifier `59` triggers `R006`, and `AllowedUnits = 2` triggers `R008`.

### Row 3: RT003

```text
ClaimId: RT003
Gender: F
Age: 32
ServiceDateFrom: 6/1/2024
PlaceOfService: 11
LineNumber: 1
ProcedureCode: 99213
ProcedureName: Office Visit Established Patient
Modifier: blank
Modifier2: blank
Modifier3: blank
Primary_Diagnosis_Pointer: 1
Primary_Diagnosis: J02.9
LONG_DESCRIPTION: Acute pharyngitis, unspecified
ClaimLineTotalPaid: 50
AmtCharged: 95
AllowedUnits: 1
AmtDisallowed: 0
AmtEligible: 90
AmtCopay: 5
AmtCoinsurance: 0
AmtDeductible: 0
ProviderNPI: 5566778899
GroupId: G3
GroupNumber: GRP300
LOB: COMM
CoverageCode: EPO
State: TX
```

Business reading: this is a commercial EPO claim in Texas for a 32-year-old female member. It is also an office visit code, not a vision-plan code.

Technical reading: `99213` triggers `R009` because it does not start with `92` or `V`.

## Clicking Proceed

When we click `Proceed`, the frontend sends the current claims to:

```text
POST /visionguard/api/claims/analyze
```

The backend does the following:

1. Validates the request body.
2. Converts blank numeric fields to zero.
3. Parses numeric strings, including values such as `$130.00`.
4. Trims string fields.
5. Builds a pandas DataFrame.
6. Loads or refreshes training artifacts if needed.
7. Applies realtime rules.
8. Computes `BilledAllowedRatio`.
9. Prepares numeric and categorical assessment inputs.
10. Scores the pattern classifier.
11. Computes confidence from the maximum predicted probability.
12. Computes unexpected-pattern score from anomaly statistics.
13. Scores historical similarity.
14. Computes final risk score.
15. Assigns risk level.
16. Generates narrative text through the LLM service or deterministic fallback.
17. Returns structured JSON.

The actual browser-equivalent response used for this demo had:

```text
processed_at: 2026-06-17T10:24:36.371886+00:00
count: 3
```

The UI displays this as:

```text
Processed 3 claims at [localized date/time].
```

## Result Header

The results area appears below the claim table and begins with a dark section.

It says:

```text
Assessment Results
Investigation Summary
Processed 3 claims at [date/time].
```

Business meaning: the analyst is now looking at assessment output rather than editable input.

Technical meaning: this section renders only when `analysis` is non-null. It uses the API response fields `analysis.count` and `analysis.processed_at`.

## Result Card Structure

Each claim receives one result card. The top border color depends on risk level:

- High: red
- Medium: amber
- Low: green
- Other or unknown: blue/info

Each card header contains:

- Claim ID
- Line number
- Procedure code
- Procedure name
- Risk badge

Each card body contains:

1. Four summary stat tiles
2. Executive summary
3. Three narrative list cards
4. Triggered indicators table
5. Detailed claim assessment section

## Summary Stat Tiles

Each result card has four tiles:

### Risk Score

This is the rounded percentage version of `final_risk_score`.

Frontend calculation:

```text
Math.round(final_risk_score * 100) + "%"
```

Backend calculation:

```text
0.4 * normalized_rule_count
+ 0.3 * confidence_level
+ 0.3 * unexpected_pattern_score
```

The normalized rule count uses the realtime-supported rule denominator. In the current code and metadata, the denominator is `9`.

### Confidence Level

This is the rounded percentage version of `confidence_level`.

Frontend calculation:

```text
Math.round(confidence_level * 100) + "%"
```

Business meaning: how strongly the assessment engine associated the claim with the returned review pattern.

Technical meaning: this is the maximum predicted probability from the classifier's probability vector.

### Risk Indicators

This is `rule_flag_count`.

Business meaning: how many deterministic rules fired.

Technical meaning: the sum of the realtime-supported rule columns for that row.

### Review Pattern

This is `predicted_pattern`.

Business meaning: the pattern family the claim most resembles.

Technical meaning: the classifier predicts a class label, unless a historical similarity match exceeds the threshold and overrides the pattern.

## Current Realtime Rules

The current code supports these realtime rule indicators:

1. `R006`: Modifier 59 on vision codes
2. `R007`: High billed-to-allowed ratio
3. `R008`: Excessive units on exam codes
4. `R009`: Invalid CPT for vision plan
5. `R017`: Missing diagnosis
6. `R100`: Two exams in one day
7. `R101`: Exam after comprehensive
8. `R102`: CCI edit conflict
9. `R103`: Bilateral modifier

Provider aggregation rules exist for historical training but are not realtime-supported:

- `R013`
- `R014`
- `R015`
- `R016`

## Result 1: Claim RT001

The first result card title is:

```text
Claim RT001 - Line 1
```

Subtitle:

```text
99213 Office Visit Established Patient
```

Risk badge:

```text
Low
```

### RT001 Summary Numbers

Visible tile values:

```text
Risk Score: 19%
Confidence Level: 40%
Risk Indicators: 1
Review Pattern: CCI Edits Claims
```

Raw API values:

```text
final_risk_score: 0.192486
confidence_level: 0.403332
unexpected_pattern_score: 0.090141
rule_flag_count: 1
predicted_pattern: CCI Edits Claims
```

Risk score math:

```text
normalized_rule_count = 1 / 9 = 0.111111
rules component = 0.4 * 0.111111 = 0.044444
pattern component = 0.3 * 0.403332 = 0.1209996
unexpected component = 0.3 * 0.090141 = 0.0270423
final = 0.044444 + 0.1209996 + 0.0270423 = 0.192486
```

The UI rounds `0.192486 * 100` to `19%`.

### RT001 Business Explanation

This claim is low risk overall, but it has one billing concern. The procedure code `99213` is an office visit code. VisionGuard's realtime rule expects vision-plan code families to start with `92` or `V`. Since `99213` does not start with either, the claim triggers:

```text
R009 Invalid CPT for vision plan
```

The charged amount is `120`. The eligible amount is `100`. The billed-to-allowed ratio is:

```text
120 / 100 = 1.2
```

That does not trigger the high billed-to-allowed rule because `R007` requires a ratio greater than `2.0`.

There are no excessive units because `AllowedUnits` is `1`.

There is no missing diagnosis because `Primary_Diagnosis` is `H52.4`.

There is no Modifier 59 issue because the modifier is `25`, not `59`.

### RT001 Executive Summary

Visible text:

```text
This claim is rated Low risk with 1 review indicator(s). The main concern is invalid cpt for vision plan.
```

This came from the deterministic fallback narrative because no OpenAI API key/model is configured.

Fallback metadata:

```text
model_used: deterministic-fallback
llm_success: false
fallback_reason: OPENAI_API_KEY or OPENAI_MODEL is not configured
```

The metadata is returned by the API but is not rendered on the page.

### RT001 Narrative Lists

Investigation Findings:

```text
Overall claim assessment score is 0.19.
Primary review focus: Invalid CPT for vision plan.
```

Key Risk Indicators:

```text
Invalid CPT for vision plan
```

Review Recommendations:

```text
No immediate action required; retain for routine monitoring.
```

### RT001 Triggered Indicators Table

The table contains:

```text
Indicator: Invalid CPT for vision plan
Severity: High
Category: Billing Concern
Description: The procedure code does not match expected vision plan code families.
```

The severity badge is red because `High` maps to the high-risk badge style.

Important distinction: the indicator severity is `High`, but the overall claim risk is `Low`. That is because the final score combines rule count, pattern confidence, and unexpected-pattern score. One high-severity rule by itself did not push the total score over the medium threshold.

### RT001 Detailed Claim Assessment

Visible fields:

```text
Provider: 1234567890
Category: Billing Concern
Top Reason: Invalid CPT for vision plan
Recommended Action: No immediate action required; retain for routine monitoring.
```

## Result 2: Claim RT002

The second result card title is:

```text
Claim RT002 - Line 1
```

Subtitle:

```text
92014 Comprehensive Eye Exam
```

Risk badge:

```text
Low
```

### RT002 Summary Numbers

Visible tile values:

```text
Risk Score: 48%
Confidence Level: 39%
Risk Indicators: 2
Review Pattern: Exam after Comprehensive
```

Raw API values from the browser-equivalent flow:

```text
final_risk_score: 0.475773
confidence_level: 0.392619
unexpected_pattern_score: 0.896995
rule_flag_count: 2
predicted_pattern: Exam after Comprehensive
```

Risk score math:

```text
normalized_rule_count = 2 / 9 = 0.222222
rules component = 0.4 * 0.222222 = 0.088889
pattern component = 0.3 * 0.392619 = 0.117786
unexpected component = 0.3 * 0.896995 = 0.269099
final = 0.088889 + 0.117786 + 0.269099 = 0.475773
```

The UI rounds `0.475773 * 100` to `48%`.

### RT002 Business Explanation

This claim is still low risk overall, but it is close to the medium threshold of `0.50`. It has two coding review indicators.

The procedure code is `92014`, which is a comprehensive eye exam code. Modifier `59` is present. The rule engine checks whether a vision code starts with `92` or `V` and whether any of the three modifier fields equals `59`. That condition is true, so it triggers:

```text
R006 Modifier 59 on vision codes
```

The claim also has:

```text
AllowedUnits: 2
```

Because `92014` is an exam code and the allowed units are greater than `1`, it triggers:

```text
R008 Excessive units on exam codes
```

The charged amount is `180`. The eligible amount is `150`. The billed-to-allowed ratio is:

```text
180 / 150 = 1.2
```

That does not trigger `R007` because the rule requires a ratio greater than `2.0`.

There is no missing diagnosis because `Primary_Diagnosis` is `E11.9`.

There is no invalid vision code because `92014` starts with `92`.

### RT002 Executive Summary

Visible text:

```text
This claim is rated Low risk with 2 review indicator(s). The main concern is modifier 59 on vision codes.
```

The top reason is the first triggered indicator returned by the rules list. In current rule order, `R006` comes before `R008`, so `Modifier 59 on vision codes` becomes the top reason.

### RT002 Narrative Lists

Investigation Findings:

```text
Overall claim assessment score is 0.48.
Primary review focus: Modifier 59 on vision codes.
```

Key Risk Indicators:

```text
Modifier 59 on vision codes
Excessive units on exam codes
```

Review Recommendations:

```text
No immediate action required; retain for routine monitoring.
```

The recommendation is routine monitoring because the overall risk level is still `Low`.

### RT002 Triggered Indicators Table

First row:

```text
Indicator: Modifier 59 on vision codes
Severity: Medium
Category: Coding Review
Description: Modifier 59 appears on a vision exam or material procedure.
```

Second row:

```text
Indicator: Excessive units on exam codes
Severity: Medium
Category: Coding Review
Description: More than one unit is allowed on a routine exam code.
```

Both severity badges are amber because `Medium` maps to the medium badge style.

### RT002 Detailed Claim Assessment

Visible fields:

```text
Provider: 9988776655
Category: Coding Review
Top Reason: Modifier 59 on vision codes
Recommended Action: No immediate action required; retain for routine monitoring.
```

## Result 3: Claim RT003

The third result card title is:

```text
Claim RT003 - Line 1
```

Subtitle:

```text
99213 Office Visit Established Patient
```

Risk badge:

```text
Low
```

### RT003 Summary Numbers

Visible tile values:

```text
Risk Score: 26%
Confidence Level: 54%
Risk Indicators: 1
Review Pattern: CCI Edits Claims
```

Raw API values:

```text
final_risk_score: 0.262195
confidence_level: 0.542258
unexpected_pattern_score: 0.183576
rule_flag_count: 1
predicted_pattern: CCI Edits Claims
```

Risk score math:

```text
normalized_rule_count = 1 / 9 = 0.111111
rules component = 0.4 * 0.111111 = 0.044444
pattern component = 0.3 * 0.542258 = 0.162677
unexpected component = 0.3 * 0.183576 = 0.055073
final = 0.044444 + 0.162677 + 0.055073 = 0.262195
```

The UI rounds `0.262195 * 100` to `26%`.

### RT003 Business Explanation

This claim is low risk overall and has one billing concern. Like RT001, the procedure code is `99213`, which does not start with `92` or `V`. It therefore triggers:

```text
R009 Invalid CPT for vision plan
```

The charged amount is `95`. The eligible amount is `90`. The billed-to-allowed ratio is:

```text
95 / 90 = 1.055556
```

This does not trigger `R007`.

There is no excessive-unit concern because `AllowedUnits` is `1`.

There is no missing diagnosis because `Primary_Diagnosis` is `J02.9`.

There is no modifier concern because the modifier fields are blank.

### RT003 Executive Summary

Visible text:

```text
This claim is rated Low risk with 1 review indicator(s). The main concern is invalid cpt for vision plan.
```

### RT003 Narrative Lists

Investigation Findings:

```text
Overall claim assessment score is 0.26.
Primary review focus: Invalid CPT for vision plan.
```

Key Risk Indicators:

```text
Invalid CPT for vision plan
```

Review Recommendations:

```text
No immediate action required; retain for routine monitoring.
```

### RT003 Triggered Indicators Table

The table contains:

```text
Indicator: Invalid CPT for vision plan
Severity: High
Category: Billing Concern
Description: The procedure code does not match expected vision plan code families.
```

### RT003 Detailed Claim Assessment

Visible fields:

```text
Provider: 5566778899
Category: Billing Concern
Top Reason: Invalid CPT for vision plan
Recommended Action: No immediate action required; retain for routine monitoring.
```

## Backend Scoring Layers

### Layer 1: Deterministic Rules

Rules are explicit business logic. They check things like invalid vision codes, excessive units, modifier usage, missing diagnosis, same-day exam combinations, CCI edit conflicts, and bilateral modifiers.

Business value: deterministic rules provide explainable risk indicators.

Technical source: `backend/app/pipelines/rules_engine.py`.

### Layer 2: Review Pattern Confidence

The model predicts one of these known historical pattern labels:

- `Bilateral Claims`
- `CCI Edits Claims`
- `Exam after Comprehensive`
- `Two Exams in One Day`

Business value: the app identifies which kind of review pattern the claim resembles.

Technical source: scikit-learn random forest artifacts in `backend/artifacts`, loaded by `RealtimeService`.

Inputs include numeric fields:

- `Age`
- `Rule_Flag_Count`
- `AmtCharged`
- `AmtEligible`
- `ClaimLineTotalPaid`
- `AllowedUnits`
- `BilledAllowedRatio`

Inputs include categorical fields:

- `ProcedureCode`
- `Gender`
- `State`
- `LOB`
- `CoverageCode`

### Layer 3: Unexpected Pattern Score

The anomaly layer compares each claim's numeric profile against training statistics.

The current anomaly statistics include means such as:

```text
Age mean: 54.7235
Rule_Flag_Count mean: 0.552625
AmtCharged mean: 143.50987
AmtEligible mean: 101.74556375
ClaimLineTotalPaid mean: 89.88546375
AllowedUnits mean: 1.015
BilledAllowedRatio mean: 1.362365923464226
```

It also stores standard deviations and a maximum anomaly score:

```text
max_anomaly_score: 9.581840541614149
```

Business value: the app can spot claims that are unusual even if only a small number of deterministic rules fire.

Technical source: `backend/app/pipelines/anomaly.py`.

### Historical Similarity

The service also compares the realtime claim to historical flagged claims using shared keys:

- `ProviderNPI`
- `State`
- `LOB`
- `CoverageCode`

Then it compares numeric vectors. If similarity is at least `0.85`, the historical pattern can override the model pattern.

In this sample run, all three claims had:

```text
similarity_score: 0.0
similarity_above_threshold: false
historical_pattern: NONE
```

Those fields are returned inside `details`, but the current UI does not display them.

## Narrative Generation

The backend tries to use an LLM if these environment variables are configured:

- `OPENAI_API_KEY`
- `OPENAI_MODEL`
- Optional `OPENAI_BASE_URL`

If they are missing or the LLM call fails, scoring still succeeds. The service generates deterministic fallback text.

In the current local run, all three narratives used:

```text
model_used: deterministic-fallback
llm_success: false
fallback_reason: OPENAI_API_KEY or OPENAI_MODEL is not configured
```

Business value: analysts always receive readable summaries, even without LLM configuration.

Technical source: `backend/app/services/llm_service.py`.

## What The UI Does Not Display Yet

The backend returns extra diagnostic details that are useful technically but not currently visible in the React page:

- `billed_allowed_ratio`
- `unexpected_pattern_driver`
- `raw_unexpected_pattern_score`
- `rule_count_normalization_denominator`
- `similarity_score`
- `similarity_above_threshold`
- `historical_pattern`
- `historical_pattern_family`
- `historical_pattern_confidence`
- `historical_case_priority`
- `historical_claim_id`
- `historical_line_number`
- `ml_predicted_pattern`
- `service_date`
- `gender`
- `age`

Business reason for hiding them: the current page keeps the analyst view concise.

Technical note: these values are available in `assessment.details` if a future results view needs deeper audit explainability.

## End Of Demo Summary

At the end of the demo, the audience should understand that VisionGuard provides a single-page claims assessment workflow:

1. Load sample or uploaded claims.
2. Edit every claim field inline.
3. Sync the assessment engine if needed.
4. Submit claims with `Proceed`.
5. Read risk score, confidence, indicators, pattern, findings, recommendations, and detailed claim assessment.

From a business perspective, the app turns raw claim rows into review-ready claim assessments.

From a technical perspective, the app combines deterministic rules, trained pattern confidence, anomaly scoring, historical similarity, and narrative generation into a structured API response rendered by React.
