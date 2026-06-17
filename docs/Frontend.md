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
        tabs.tsx
        textarea.tsx
    pages/
      Dashboard.tsx
      Retraining.tsx
      ClaimReview.tsx
      Results.tsx
    services/
      api.ts
    types/
      api.ts
    App.tsx
    main.tsx
    index.css
```

## Routes and Views

The app uses a simple in-app navigation model:

- Dashboard
- Retraining
- Claim Review
- Results

## Dashboard

Displays:

- Training status.
- Last refresh.
- Dataset statistics.
- Claim processing status.

Business labels:

- "Assessment Engine"
- "Historical Claims"
- "Editable Rules"
- "Recent Processing"

## Retraining Screen

Allows:

- One-click retraining.
- Progress status.
- Metrics summary.

Business labels:

- "Refresh Assessment Engine"
- "Validation Accuracy" may be shown as "Validation Quality".
- "Training records" may be shown as "Historical records used".

## Claim Review Screen

Allows:

- Upload CSV.
- Load sample claims.
- View claims.
- Edit claims inline.
- Submit for analysis.

Required behavior:

- Submit one to five claims.
- Keep financial fields editable.
- Keep procedure, diagnosis, and modifier fields editable.

## Results Screen

Displays:

- Executive Summary.
- Risk Level.
- Findings.
- Triggered Indicators.
- Review Recommendations.
- Detailed Claim Assessment.

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

- Training status is fetched on app load and after retraining.
- Claim rows are stored in the Claim Review page.
- Analysis results are stored at the app level so the Results screen can render the latest assessment.

This is sufficient for the POC. A later production build could add React Query or a centralized store if workflows become larger.

## API Configuration

The frontend reads:

```text
VITE_API_BASE_URL
```

Default behavior:

- Development: `http://localhost:8000`
- Production: `https://d2brdeqy144bwg.cloudfront.net`

