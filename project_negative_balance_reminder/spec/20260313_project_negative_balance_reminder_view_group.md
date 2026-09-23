# SPEC: Project negative balance reminder view grouping

## 1. Context
- Request date: 2026-03-13
- Requested by: user
- Scope: `project_negative_balance_reminder` project form layout

## 2. Goals
- Group `last_notification_date` and `renewal_period_days` under a titled
  section `Negative balance`.
- Keep consistent visual style with existing settings sections (e.g. Portal).

## 3. Non-goals
- No backend logic changes.
- No security/model changes.

## 4. Functional requirements
- Both fields must be shown inside the same titled group.
- Title must be `Negative balance`.

## 5. Technical design
- Update inherited project form view in
  `addons/trey-addons/project_negative_balance_reminder/views/project_views.xml`.

## 6. Validation plan
- Upgrade module and open project form settings section.
- Confirm both fields are in a dedicated titled section.

## 7. Risks and mitigations
- Risk: xpath anchored too broadly can place group in a wrong area.
- Mitigation: insert in the same parent region as settings groups.

## 8. Deliverables
- XML view update for grouped field presentation.
