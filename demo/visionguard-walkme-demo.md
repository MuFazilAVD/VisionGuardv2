# VisionGuard Demo Walkthrough

## Purpose

VisionGuard is a proof-of-concept workspace for triaging vision claims. It combines business rules, learned review patterns, anomaly scoring, historical similarity, and plain-language summaries to help an analyst decide what needs review.

This walkthrough follows the current React/FastAPI application and its three seeded claims.

## 1. Open the workspace

The page opens on **New Claim Batch** and automatically loads three sample claims.

Point out that the grid is editable and horizontally scrollable. It contains the full claim schema, including **Member ID**, service, diagnosis, payment, provider, plan, and location fields.

Available actions:

- **Sync Engine** - rebuilds scoring artifacts from the current historical data and rules. This is optional for a normal demo.
- **Upload CSV** - replaces the grid with claims parsed in the browser. `MemberId`, `Member ID`, and the legacy `MemeberId` spelling are accepted.
- **Add Claim** - adds a prefilled claim row.
- **Trash icon** - removes a row.
- **Proceed** - submits the displayed batch for assessment.

Editing, adding, removing, or uploading claims clears any previous results.

## 2. Review the sample claims

Use the seeded rows to explain the inputs:

| Claim | Member | Key feature | Expected indicator |
| --- | --- | --- | --- |
| RT001 | MEM001 | Procedure `99213` is outside the configured vision-code families | CPT rule violation |
| RT002 | MEM002 | Procedure `92014` has modifier `59` and two units | Modifier 59; excessive units |
| RT003 | MEM003 | Procedure `99213` is outside the configured vision-code families | CPT rule violation |

`MemberId` matters because same-member, same-day rules can connect related claim lines even when their claim IDs differ. If Member ID is blank, those rules fall back to Claim ID.

## 3. Run the assessment

Click **Proceed**. The app sends the current rows to:

```text
POST /visionguardv2/api/claims/analyze
```

When processing finishes, the page scrolls to **Investigation Summary**.

The current seeded run should show approximately:

- **0 Frauds**
- **1 Suspicious**
- **2 Clean**
- **40% average risk**

Expected claim-level classifications:

| Claim | Risk | Main reason |
| --- | --- | --- |
| RT001 | Low | CPT rule violation |
| RT002 | Medium | Modifier 59 on vision codes |
| RT003 | Low | CPT rule violation |

Exact scores and predicted review patterns may change after retraining or data changes; focus the demo on the explanation and workflow.

## 4. Read the results

The **Assessment Overview** summarizes the whole batch. Below it, each claim appears as a collapsed card. Click the caret to expand a claim.

Each expanded card shows:

- **Risk Score** - the weighted score `S` computed by the engine. The UI displays `round(100 x S)%`.
- **Confidence Level** - `round(100 x P)%`. It starts with the highest pattern-model class probability and receives the historical ClaimId boost when applicable. It is a scoring signal, not the probability that fraud occurred.
- **Rules Triggered** - the raw count `C = sum(I_j)` of realtime rule flags, where each `I_j` is `1` when rule `j` triggers and `0` otherwise.
- **Review Pattern** - the pattern selected by the trained classifier, unless a historical similarity score of at least `0.85` replaces the displayed label.
- **Executive Summary** - concise business interpretation.
- **Findings, indicators, and recommendations** - the reasons and suggested next action.
- **Triggered Indicators** - rule name, severity, category, and description.

The displayed values can be read mathematically as:

```text
C = number of triggered realtime rules
C* = min(max(C, 0), 9)                    capped rule count
R = C* / 9                                when C* <= 1
R = 1/9 + (8/9)((C* - 1)/8)^0.75          when C* > 1
P_raw = max(pattern class probabilities)  raw pattern-confidence signal
M = 1 when ClaimId exists in history      exact historical-claim signal
P = P_raw + 0.70(1 - P_raw)               when M = 1; otherwise P = P_raw
U = normalized numeric anomaly distance   unexpectedness signal

B = 0.60R + 0.30P + 0.10U                 base risk score
S = smooth_escalation(B)                   final risk score
```

The exact ClaimId boost uses 70% of the remaining confidence headroom. For example, a raw pattern confidence of `0.40` becomes `0.40 + 0.70(0.60) = 0.82`. Blank ClaimIds never match. Matching is trimmed and case-insensitive. This boost changes confidence and final risk, but it does not replace the predicted pattern.

Using the current seeded artifacts, RT002 approximately triggers two rules with `P = 0.679671` and `U = 0.729820`:

```text
R = 1/9 + (8/9)(1/8)^0.75
  = 0.297977
B = 0.60(0.297977) + 0.30(0.679671) + 0.10(0.729820)
  = 0.455669
S = smooth_escalation(B)
  = 0.475982
```

The card displays **48%**, and the claim is **Medium** risk because `0.40 <= S < 0.55`. Scores are stored to six decimal places before the frontend converts them to percentages. The learned values can change after **Sync Engine** retrains the artifacts.

The **Assessment Overview** is computed directly from claim-level results:

```text
Frauds     = count(S >= 0.55)
Suspicious = count(0.40 <= S < 0.55)
Clean      = count(S < 0.40)
Avg Risk   = round(100 x (sum(S_i) / n))%
```

For RT002, highlight that two coding indicators and an unusual billing profile move it into **Medium** risk, making it the batch's selective-review candidate.

## 5. Explain the engine

VisionGuard assesses each claim through the following pipeline.

### 5.1 Normalize and derive inputs

Missing claim columns are added with blank or zero defaults. Text fields are trimmed, numeric fields are parsed, procedure codes are uppercased, and service dates are converted to dates.

The billed-to-allowed feature is:

```text
BilledAllowedRatio = AmtCharged / AmtEligible, when AmtEligible > 0
BilledAllowedRatio = 0, otherwise
```

### 5.2 Compute deterministic rule flags

Each supported rule produces a binary value:

```text
I_j(x) = 1, when claim x satisfies rule j
I_j(x) = 0, otherwise
C(x)   = sum from j=1 to 9 of I_j(x)
R(x)   = min(C(x) / 9, 1)
```

The nine realtime rules test modifier `59`, billed-to-allowed ratio greater than `2.0`, exam units greater than `1`, invalid vision-code families, missing diagnosis, multiple same-day exams, routine plus comprehensive same-day exams, configured CCI code conflicts, and bilateral modifiers `50`, `LT`, or `RT`.

Same-day rules group lines by `MemberId + ServiceDate`. When Member ID is blank, Claim ID is used instead. Matching historical lines for that member and date are included as context. Every triggered rule contributes one count to `C`; rule severity is shown for interpretation but does not give the rule extra mathematical weight.

### 5.3 Compute pattern confidence

The classifier is a 100-tree random forest with maximum tree depth `8`. It is trained on labeled historical claims using:

- Numeric features: age, rule count, charged amount, eligible amount, paid amount, allowed units, and billed-to-allowed ratio.
- One-hot encoded categorical features: procedure code, gender, state, line of business, and coverage code.

Unknown categorical values are ignored rather than causing scoring to fail. For class `k`, the forest averages the class probabilities from all trees:

```text
p_k(x)  = (1 / 100) x sum from t=1 to 100 of p_t,k(x)
k*      = argmax over k of p_k(x)
P_raw(x)= max over k of p_k(x)
P(x)    = P_raw(x) + 0.70(1 - P_raw(x)) when ClaimId exists in history
P(x)    = P_raw(x) otherwise
```

`k*` is the model's review-pattern label. `P_raw` is the model's original class confidence, while `P` is the **Confidence Level** used in scoring after any exact historical ClaimId boost. Neither is calibrated as fraud probability.

### 5.4 Compute numeric unexpectedness

Training stores the historical mean `mu_j`, sample standard deviation `sigma_j`, and maximum historical distance `D_max` for the seven numeric features. A zero or unavailable standard deviation is replaced with `1`.

For each feature:

```text
z_j(x) = (x_j - mu_j) / sigma_j
D(x)   = sqrt(sum over j of z_j(x)^2)
U(x)   = clip(D(x) / D_max, 0, 1)
```

`D` is the raw Euclidean distance from the historical numeric center. `U` is the normalized **Unexpected Pattern Score** used in final risk. The feature with the largest absolute z-score, `argmax |z_j|`, is reported as the main unexpectedness driver.

### 5.5 Compare with flagged historical claims

Only historical rows with a nonblank review-pattern label are eligible. If the incoming claim has a Member ID and historical Member IDs exist, candidates are restricted to that member. Otherwise, candidates must exactly match provider NPI, state, line of business, and coverage code.

The claim and each candidate are standardized with the same historical means and standard deviations across age, rule count, charged amount, eligible amount, paid amount, and allowed units. Similarity is cosine similarity:

```text
similarity(x, h) = (z_x dot z_h) / (||z_x|| x ||z_h||)
best_similarity  = max over candidate historical claims h
```

A best score of at least `0.85` replaces the displayed review-pattern label and drives the historical-match category and reason. A non-exam claim is prevented from matching the **Two Exams in One Day** pattern. Similarity does not directly enter the final risk formula. The separate exact ClaimId match can boost confidence whether or not cosine similarity reaches `0.85`.

### 5.6 Combine the risk signals

The engine first combines the three numeric signals:

```text
B(x) = 0.60R(x) + 0.30P(x) + 0.10U(x)
```

It then applies two bounded smoothstep escalation bands. The first gradually adds up to 12% of the remaining headroom as the base score moves from `0.40` to `0.55`. The second adds up to another 28% of remaining headroom as the base score moves from `0.55` to `0.75`. The final score is capped at `1.00` and rounded to six decimal places.

```text
Low    when S < 0.40
Medium when 0.40 <= S < 0.55
High   when S >= 0.55
```

The rule curve preserves `1 rule = 1/9`, accelerates the penalty for additional rules, and caps counts at nine:

```text
1 rule = 0.111111
2 rules = 0.297977
3 rules = 0.425381
4 rules = 0.537073
9+ rules = 1.000000
```

Rules provide 60% of the base score, pattern confidence provides 30%, and numeric unexpectedness provides 10%. An exact historical ClaimId match boosts pattern confidence by 70% of its remaining headroom before these weights are applied. Moderate escalation begins above 40%, with stronger escalation above 55%.

### 5.7 Generate the explanation

The selected risk level, pattern, indicators, historical match, top reason, and recommended action are passed to narrative generation. If no LLM is configured or the call fails, deterministic summaries are returned. Narrative text explains the computed result but never changes `R`, `P`, `U`, or `S`.

## Interpretation cautions

- The overview labels **Frauds**, **Suspicious**, and **Clean** currently map directly to High-, Medium-, and Low-risk counts. They are triage labels, not confirmed fraud findings or final claim dispositions.
- A Low-risk claim can still contain a High-severity rule indicator because overall risk combines several signals.
- Confidence is the pattern classification signal after any exact historical ClaimId boost; it is not fraud probability.
- Narrative text explains the result but does not determine the score.

## Close

VisionGuard turns editable claim batches into prioritized, explainable assessments. The analyst can see what triggered review, understand the broader pattern, and act on a recommendation without leaving the workspace.

Key implementation references:

- `frontend/src/pages/ClaimWorkspace.tsx`
- `backend/app/services/realtime_service.py`
- `backend/app/pipelines/rules_engine.py`
- `backend/app/pipelines/risk_scoring.py`
