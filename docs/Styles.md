# Style and Design System

## Audience

The application is for claims analysts, investigators, and business stakeholders. It should feel operational, trustworthy, and efficient.

## Visual Direction

- Quiet operational workspace style.
- Modern claims operations cockpit: compact, high-contrast, precise, and confidence-building.
- Dense but readable information with clear scan paths for analyst workflows.
- Use a compact top shell with no left navigation rail and no secondary page navigation.
- No oversized marketing hero sections.
- No decorative gradient orbs or purely atmospheric backgrounds.
- Cards only for repeated result items and framed forms.
- No cards inside cards.
- Surfaces should feel layered and premium: use restrained borders, small shadows, semantic top bars, dark command bands, and compact headings.
- Avoid large blank white regions. Keep the workspace task-dense, with 12px to 16px gaps for operational sections.

## Color

The palette should avoid being dominated by a single hue. Color is semantic first and decorative second. Every color-coded state must also include a text label or icon.

- Neutral background: near-white canvas for sustained analyst use.
- Ink: dark neutral text for primary content.
- Slate: borders, table structure, and muted supporting text.
- Charcoal: command bands and table headers only. Use sparingly so the UI feels modern without becoming a dark theme.
- Blue: primary actions and informational emphasis.
- Sky: secondary information such as confidence and count metadata.
- Teal: stable data/evidence assets and supporting operational context.
- Green: success, ready states, completed refreshes, and low risk.
- Amber: caution, medium risk, pending attention, and incomplete readiness.
- Red: high risk, destructive actions, failures, and blocking errors.

### Semantic Meaning

- Low risk: green with check/shield iconography.
- Medium risk: amber with warning iconography.
- High risk: red with octagon/warning iconography.
- Ready/success: green with check or shield iconography.
- Running/informational: blue or sky with refresh, pulse, or document iconography.
- Data/evidence: teal with database, file, or fingerprint iconography.
- Remove/destructive: red text or red surface paired with a trash icon.

## Typography

- System font stack.
- No viewport-scaled font sizes.
- Headings should be compact inside panels.
- Letter spacing remains normal.

## Spacing

- Page gutters: 20px on desktop, 12px to 16px on mobile.
- Component gaps: 12px to 16px for most operational surfaces.
- Table cells: compact enough for repeated use, with denser row height than marketing/admin templates.
- Cards use radius 8px or less.
- Metric cards use compact content, semantic top bars, and no oversized empty interiors.

## Components

- Buttons include icons when the action is common and recognizable.
- Upload, sync, submit, delete, readiness, and assessment actions use Phosphor icons.
- Phosphor weights should communicate priority: bold/fill for direct actions and alerts, duotone for status tiles.
- Badges communicate risk level and status.
- Risk badges pair color, text, and icon so color is never the only cue.
- Tables are used for claim review and result details, with dark headers for stronger scanning and compact body rows.
- Textareas are used for longer editable claim descriptions.
- File upload must be triggered from a keyboard reachable button, not only a styled label.
- The workspace should begin with the claim data form, not a secondary command header or right-side status rail.

## Accessibility

- Interactive elements must be keyboard reachable.
- Color is not the only status indicator; text labels accompany risk colors.
- Iconography reinforces meaning but does not replace text labels for critical states.
- Inputs have visible labels.
- Focus states are visible.
- Text must not overlap or overflow controls on mobile.
- Motion is minimized for users who prefer reduced motion.
- Semantic colors should meet readable contrast against their surfaces and avoid using red/green alone for binary decisions.

## Business Language

Avoid visible text:

- Machine Learning
- Random Forest
- Features
- One Hot Encoding
- Classification Model
- Z Scores

Use:

- Assessment Engine
- Pattern Confidence
- Risk Indicators
- Investigation Findings
- Claim Assessment
- Review Recommendation
- Potential Concerns
