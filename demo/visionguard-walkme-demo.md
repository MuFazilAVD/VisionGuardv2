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
| RT001 | MEM001 | Procedure `99213` is outside the configured vision-code families | Invalid CPT for vision plan |
| RT002 | MEM002 | Procedure `92014` has modifier `59` and two units | Modifier 59; excessive units |
| RT003 | MEM003 | Procedure `99213` is outside the configured vision-code families | Invalid CPT for vision plan |

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
| RT001 | Low | Invalid CPT for vision plan |
| RT002 | Medium | Modifier 59 on vision codes |
| RT003 | Low | Invalid CPT for vision plan |

Exact scores and predicted review patterns may change after retraining or data changes; focus the demo on the explanation and workflow.

## 4. Read the results

The **Assessment Overview** summarizes the whole batch. Below it, each claim appears as a collapsed card. Click the caret to expand a claim.

Each expanded card shows:

- **Risk Score** - combined score from rules, pattern confidence, and unexpectedness.
- **Confidence Level** - confidence in the predicted review pattern, not the probability that fraud occurred.
- **Risk Indicators** - number of deterministic rules triggered.
- **Review Pattern** - the learned or historically matched pattern.
- **Executive Summary** - concise business interpretation.
- **Findings, indicators, and recommendations** - the reasons and suggested next action.
- **Triggered Indicators** - rule name, severity, category, and description.
- **Detailed Claim Assessment** - Member ID, provider, category, top reason, and recommended action.

For RT002, highlight that two coding indicators and an unusual billing profile move it into **Medium** risk, making it the batch's selective-review candidate.

## 5. Explain the engine

VisionGuard assesses each claim through complementary signals:

1. **Rules** identify explainable issues such as invalid vision codes, high billed-to-allowed ratios, excessive units, missing diagnoses, same-day exam combinations, CCI conflicts, and bilateral modifiers.
2. **Pattern scoring** estimates which known review pattern the claim most resembles.
3. **Anomaly scoring** measures how unusual its numeric profile is relative to historical claims.
4. **Historical similarity** first looks for relevant same-member history, then falls back to comparable claim context. A strong match can override the model's pattern label.
5. **Narrative generation** converts the result into business language. If no LLM is configured, deterministic summaries are used and scoring continues normally.

The final risk score weights rules at 40%, pattern confidence at 30%, and anomaly score at 30%. Scores below 50% are Low, 50-74% are Medium, and 75% or above are High.

## Interpretation cautions

- The overview labels **Frauds**, **Suspicious**, and **Clean** currently map directly to High-, Medium-, and Low-risk counts. They are triage labels, not confirmed fraud findings or final claim dispositions.
- A Low-risk claim can still contain a High-severity rule indicator because overall risk combines several signals.
- Confidence describes pattern classification confidence; it is not fraud probability.
- Narrative text explains the result but does not determine the score.

## Close

VisionGuard turns editable claim batches into prioritized, explainable assessments. The analyst can see what triggered review, understand the broader pattern, and act on a recommendation without leaving the workspace.

Key implementation references:

- `frontend/src/pages/ClaimWorkspace.tsx`
- `backend/app/services/realtime_service.py`
- `backend/app/pipelines/rules_engine.py`
- `backend/app/pipelines/risk_scoring.py`
