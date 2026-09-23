# SPEC: Project negative balance reminder ORM domain optimization

## 1. Context
- Request date: 2026-03-13
- Requested by: user
- Scope: `project_negative_balance_reminder` candidate selection

## 2. Goals
- Avoid iterating over all projects in `check_and_notify_negative_balance`.
- Move static eligibility checks to ORM domain filters.
- Keep functional behavior for notification cadence.

## 3. Non-goals
- Redesign notification template/content.
- Change reminder cadence semantics (`_should_notify`).

## 4. Functional requirements
- Candidate search must exclude archived/inactive projects.
- Candidate search must exclude template projects (`is_template`).
- Candidate search must include only projects with timesheets enabled.
- Candidate search should include maintenance contract filter when available:
  `contract_lite_line_id.product_id.is_maintenance = True`.
- Candidate search should include `current_balance < 0` directly in domain when
  the field supports search; otherwise fallback to Python filtering.

## 5. Technical design
- Module(s):
  - `project_negative_balance_reminder`
- Main change:
  - Build a dynamic domain based on existing model fields to avoid invalid
    domain clauses in databases where some optional fields are unavailable.
- Data model/security:
  - No schema or ACL changes.

## 6. Validation plan
- Run module tests for `project_negative_balance_reminder`.
- Manually verify no notification is sent for archived/template/non-timesheet
  projects.

## 7. Risks and mitigations
- Risk: `current_balance` is computed and may not be searchable.
- Mitigation: detect field capabilities and fallback to in-memory filtering.

## 8. Deliverables
- Update candidate search logic in:
  `addons/trey-addons/project_negative_balance_reminder/models/project_project.py`

## 9. Rollback plan
- Restore previous `search([])` and Python-side filtering sequence.
