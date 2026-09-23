# Academy student limit setting

## Scope

Add a persistent, company-specific general setting under the Academy section
to enable or disable activity student-limit validation.

## Behavior

- The setting is stored on `res.company` and enabled by default to preserve the
  existing behavior.
- Student-limit validation is implemented in
  `academy.activity._check_student_limit()`.
- Enrollment creation and activation call that method only when the setting
  is enabled.
