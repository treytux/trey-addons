# HR Leave Mail Force Company Notification

## Scope

Force time off notification emails to render with the employee company.

## Behavior

- Applies only to records rendered through `mail.thread` with model `hr.leave`.
- Uses `employee_company_id` as `force_email_company` when available.
- Keeps the standard mail rendering behavior for all other models.

## Validation

- Install the module with `hr_holidays`.
- Trigger a time off notification for an employee whose company differs from
  the current environment company.
- Confirm the rendered notification header uses the employee company logo and
  contact data.
