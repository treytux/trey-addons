# SPEC: Fix failing tests in project_negative_balance_reminder

## 1. Context
- Request date: 2026-03-18
- Requested by: user
- Scope: failing tests in
  `project_negative_balance_reminder/tests/test_project_negative_balance_reminder.py`.

## 2. Problem
- Tests patch `_is_maintenance_project`, but that method no longer exists in
  model `project.project` inherited by the module.
- Current implementation uses `_get_notify_candidates_domain()` plus
  `_has_negative_balance()`.

## 3. Goals
- Remove obsolete patches and align test setup with current behavior.
- Keep the original business intent of each test case.

## 4. Non-goals
- No functional changes in module logic.
- No controller/view/i18n changes.

## 5. Technical design
- Replace patches of `_is_maintenance_project` with:
  - `_get_notify_candidates_domain` patches for candidate selection, and
  - `_has_negative_balance` patches where needed to keep tests deterministic.
- Preserve assertions about `last_notification_date`.

## 6. Validation plan
- Run module tests:
  `oo exec trey_260317 --instance trey -u project_negative_balance_reminder --stop-after-init --test-enable --test-tags /project_negative_balance_reminder`

## 7. Risks and mitigations
- Risk: tests may still depend on data outside their fixture.
- Mitigation: patch candidate domain to target only the created project.

## 8. Deliverables
- Updated test file:
  `addons/trey-addons/project_negative_balance_reminder/tests/test_project_negative_balance_reminder.py`.
