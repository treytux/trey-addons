# SPEC: Remove hardcoded date from negative balance reminder

## 1. Context
- Request date: 2026-03-18
- Requested by: user
- Scope: `project_negative_balance_reminder` model and tests.

## 2. Problem
- The reminder logic uses a hardcoded date (`2025-08-01`), causing test and
  runtime behavior mismatch.

## 3. Goals
- Restore dynamic date behavior in model code.
- Make tests deterministic without relying on fixed past dates.

## 4. Non-goals
- No functional redesign of notification criteria.
- No view/controller changes.

## 5. Technical design
- In model: use `fields.Date.today()` as current date.
- In tests:
  - compare against current date where notification is expected.
  - set `last_notification_date` to current date for no-notify renewal test.

## 6. Validation plan
- Run:
  `oo exec trey_260317 --instance trey -u project_negative_balance_reminder --stop-after-init --test-enable --test-tags /project_negative_balance_reminder`
- Expect: 0 failures, 0 errors.

## 7. Risks and mitigations
- Risk: date-sensitive tests become flaky.
- Mitigation: use same `fields.Date.today()` value in setup/assert within each
  test.

## 8. Deliverables
- Updated model:
  `addons/trey-addons/project_negative_balance_reminder/models/project_project.py`
- Updated tests:
  `addons/trey-addons/project_negative_balance_reminder/tests/test_project_negative_balance_reminder.py`
