# Frontend Documentation

## Overview

The frontend is a Vite React TypeScript application under `frontend/`. It is designed for claims analysts, investigators, and business stakeholders.

Visible UI language avoids technical model terminology. Internal API fields may include compatibility names, but screen labels use business terms.

## Structure

```text
frontend/
  src/
    components/
      Layout.tsx
      MetricCard.tsx
      RiskBadge.tsx
      ui/
        badge.tsx
        button.tsx
        card.tsx
        input.tsx
        table.tsx
        textarea.tsx
    pages/
      ClaimWorkspace.tsx
    services/
      api.ts
    types/
      api.ts
    App.tsx
    main.tsx
    index.css
```

## Application Flow

The app is a single-page analyst workspace. It does not use a left navigation rail, dashboard view, separate results view, or secondary command header. `App.tsx` renders:

- `Layout.tsx` for the compact brand header.
- `ClaimWorkspace.tsx` for engine sync, claim data upload, submission, and results.

## Shell

The shell provides:

- Sticky top brand header.
- No desktop left rail.
- No mobile horizontal navigation.

## Engine Sync

Retraining is reduced to a single workflow button:

- "Sync Engine" calls `POST /api/training/retrain`.
- The workspace refreshes sample data after sync.
- Sync feedback is shown inline only when the action completes or fails.

## Claim Workspace

Allows:

- Upload CSV.
- Load sample realtime claims on first app load.
- Add or remove claim rows.
- View claims.
- Edit claims inline.
- Proceed to assessment.

CSV upload behavior:

- CSV files are parsed in the browser.
- Uploaded rows populate the editable claim table.
- Upload does not submit automatically.
- Clicking "Proceed" submits the current table data.

Required behavior:

- Submit one or more claims.
- Render the full incoming claim schema: `ClaimId`, `Gender`, `Age`, `ServiceDateFrom`, `PlaceOfService`, `LineNumber`, `ProcedureCode`, `ProcedureName`, `Modifier`, `Modifier2`, `Modifier3`, `Primary_Diagnosis_Pointer`, `Primary_Diagnosis`, `LONG_DESCRIPTION`, `ClaimLineTotalPaid`, `AmtCharged`, `AllowedUnits`, `AmtDisallowed`, `AmtEligible`, `AmtCopay`, `AmtCoinsurance`, `AmtDeductible`, `ProviderNPI`, `GroupId`, `GroupNumber`, `LOB`, `CoverageCode`, and `State`.
- Keep financial fields editable.
- Keep procedure, diagnosis, and modifier fields editable.
- Clear stale assessment results whenever the claim data changes.

## Results

Displays:

- Executive Summary.
- Risk Level.
- Findings.
- Triggered Indicators.
- Review Recommendations.
- Detailed Claim Assessment.

Results render below the claim table on the same page. After "Proceed" completes, the frontend scrolls to the newly rendered results region.

Visible language avoids:

- Machine Learning
- Random Forest
- Features
- One Hot Encoding
- Classification Model
- Z Scores

Preferred language:

- Risk Indicators
- Investigation Findings
- Claim Assessment
- Review Recommendation
- Potential Concerns
- Confidence Level

## State Management

The POC uses React component state:

- Sample data is fetched on app load and after engine sync.
- Claim rows are stored in `ClaimWorkspace.tsx`.
- Analysis results are stored in `ClaimWorkspace.tsx` and rendered below the claim table.

This is sufficient for the POC. A later production build could add React Query or a centralized store if workflows become larger.

## API Configuration

The frontend reads:

```text
VITE_API_BASE_URL
```

Default behavior:

- Development: `http://localhost:8000`
- Production: `https://d2brdeqy144bwg.cloudfront.net`
