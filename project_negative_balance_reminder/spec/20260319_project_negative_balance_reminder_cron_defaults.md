# SPEC: project_negative_balance_reminder cron default safety values

## 1. Context
- Request date: 2026-03-19
- Requested by: user
- Scope: `project_negative_balance_reminder` data and manifest metadata.

## 2. Problem
- The scheduled action for negative balance reminders was configured to run
  daily and active by default.
- New Trey guideline requires new `ir.cron` records to be created disabled by
  default and with `interval_number = -1` unless explicitly requested.

## 3. Goals
- Align module cron defaults with Trey cron convention.
- Record module version bump associated with this data-level behavior change.

## 4. Non-goals
- No change in reminder business logic (`check_and_notify_negative_balance`).
- No test refactor or i18n updates.
- No changes in cron code payload or interval type.

## 5. Technical design
- Update `data/ir_cron_data.xml` record
  `project_negative_balance_reminder`:
  - set `<field name="interval_number">-1</field>`.
  - set `<field name="active" eval="False"/>`.
  - keep `interval_type` as `days`.
- Update module version in `__manifest__.py` from `16.0.1.3.0` to
  `16.0.1.4.0`.

## 6. Validation plan
- Upgrade the module in target DB:
  `oo exec <db_name> --instance <instance> -u project_negative_balance_reminder --stop-after-init`
- Verify in UI (Technical > Automation > Scheduled Actions) that
  `project_negative_balance_reminder` cron is inactive after upgrade.
- Verify XML data contains:
  - `interval_number = -1`
  - `active = False`

## 7. Risks and mitigations
- Risk: environments expecting automatic execution after upgrade may stop
  sending reminders.
- Mitigation: communicate the new default and explicitly activate cron per
  environment when desired.

## 8. Deliverables
- Updated file:
  `addons/trey-addons/project_negative_balance_reminder/data/ir_cron_data.xml`
- Updated file:
  `addons/trey-addons/project_negative_balance_reminder/__manifest__.py`

## 9. Rollback plan
- Restore previous cron defaults:
  - `interval_number = 1`
  - `active = True`
- Revert manifest version bump accordingly.
