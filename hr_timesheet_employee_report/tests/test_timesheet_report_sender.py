###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from datetime import date
from unittest.mock import patch

from odoo import fields
from odoo.tests.common import SavepointCase


class TestTimesheetReportSender(SavepointCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.report_sender = cls.env['timesheet.report.sender']
        cls.partner = cls.env.user.partner_id
        cls.project = cls.env['project.project'].create({
            'name': 'Timesheet report test project',
        })
        cls.leave_type = cls.env['hr.leave.type'].create({
            'name': 'Timesheet report leave type',
            'leave_validation_type': 'hr',
            'requires_allocation': 'no',
            'time_type': 'leave',
        })

    @classmethod
    def _create_calendar(cls):
        calendar = cls.env['resource.calendar'].create({
            'name': 'Timesheet report 40h',
            'hours_per_day': 8.0,
        })
        for day in range(5):
            cls.env['resource.calendar.attendance'].create({
                'calendar_id': calendar.id,
                'dayofweek': str(day),
                'hour_from': 8.0,
                'hour_to': 12.0,
                'name': f'Morning {day}',
            })
            cls.env['resource.calendar.attendance'].create({
                'calendar_id': calendar.id,
                'dayofweek': str(day),
                'hour_from': 13.0,
                'hour_to': 17.0,
                'name': f'Afternoon {day}',
            })
        return calendar

    @classmethod
    def _create_employee(cls, name, calendar):
        return cls.env['hr.employee'].create({
            'name': name,
            'resource_calendar_id': calendar.id,
        })

    @classmethod
    def _create_timesheet(
            cls, employee, line_date, hours, real_time=None, unit_amount=None):
        if real_time is None:
            real_time = hours
        if unit_amount is None:
            unit_amount = hours
        cls.env['account.analytic.line'].create({
            'name': f'Line {employee.name} {line_date}',
            'account_id': cls.project.analytic_account_id.id,
            'date': line_date,
            'employee_id': employee.id,
            'project_id': cls.project.id,
            'real_time': real_time,
            'unit_amount': unit_amount,
        })

    @classmethod
    def _create_leave(cls, employee, date_from, date_to, validated=True):
        leave = cls.env['hr.leave'].with_context(
            mail_create_nolog=True,
            mail_notrack=True).create({
                'employee_id': employee.id,
                'holiday_status_id': cls.leave_type.id,
                'name': 'Test leave',
                'request_date_from': date_from,
                'request_date_to': date_to,
            })
        if validated:
            leave.action_validate()
        return leave

    @staticmethod
    def _freeze_today():
        return patch.object(
            fields.Date,
            'today',
            return_value=date(2026, 3, 15))

    def _get_lines_by_employee_name(self):
        with self._freeze_today():
            report_data = self.report_sender._get_report_data()
        lines = report_data['report_lines']
        return {line['employee_name']: line for line in lines}

    def test_variation_positive_negative_and_na(self):
        calendar = self._create_calendar()
        employee_pos = self._create_employee('Employee Positive', calendar)
        employee_neg = self._create_employee('Employee Negative', calendar)
        employee_na = self._create_employee('Employee NA', calendar)
        self._create_timesheet(employee_pos, '2026-02-10', 10.0)
        self._create_timesheet(employee_pos, '2026-03-10', 15.0)
        self._create_timesheet(employee_neg, '2026-02-10', 10.0)
        self._create_timesheet(employee_neg, '2026-03-10', 5.0)
        self._create_timesheet(employee_na, '2026-03-10', 4.0)
        lines_by_name = self._get_lines_by_employee_name()
        self.assertAlmostEqual(
            lines_by_name['Employee Positive']['variation_pct'],
            50.0)
        self.assertAlmostEqual(
            lines_by_name['Employee Negative']['variation_pct'],
            -50.0)
        self.assertIsNone(lines_by_name['Employee NA']['variation_pct'])

    def test_available_hours_without_absences(self):
        calendar = self._create_calendar()
        employee = self._create_employee('Employee No Absence', calendar)
        self._create_timesheet(employee, '2026-03-05', 8.0)
        lines_by_name = self._get_lines_by_employee_name()
        line = lines_by_name['Employee No Absence']
        self.assertGreater(line['available_hours_month'], 0.0)
        self.assertEqual(line['absence_hours_month'], 0.0)
        self.assertAlmostEqual(
            line['net_available_hours_month'],
            line['available_hours_month'])

    def test_available_hours_with_validated_absence(self):
        calendar = self._create_calendar()
        employee = self._create_employee('Employee Validated Leave', calendar)
        self._create_timesheet(employee, '2026-03-05', 8.0)
        self._create_leave(employee, '2026-03-10', '2026-03-10')
        lines_by_name = self._get_lines_by_employee_name()
        line = lines_by_name['Employee Validated Leave']
        self.assertGreater(line['absence_hours_month'], 0.0)
        self.assertAlmostEqual(
            line['net_available_hours_month'],
            line['available_hours_month'] - line['absence_hours_month'])
        self.assertAlmostEqual(line['cur_month_hours'], 8.0)

    def test_current_month_hours_discount_validated_absence_hours(self):
        calendar = self._create_calendar()
        employee = self._create_employee('Employee Discount Leave', calendar)
        self._create_timesheet(
            employee, '2026-02-10', 0.0, real_time=150.0, unit_amount=122.75)
        self._create_timesheet(
            employee, '2026-03-10', 0.0, real_time=36.5, unit_amount=108.0)
        with patch.object(
            type(self.report_sender),
            '_get_employee_available_and_absence_hours',
            return_value=(176.0, 80.0)
        ):
            lines_by_name = self._get_lines_by_employee_name()
        line = lines_by_name['Employee Discount Leave']
        self.assertAlmostEqual(line['absence_hours_month'], 80.0)
        self.assertAlmostEqual(line['cur_month_hours'], 28.0)
        self.assertAlmostEqual(line['cur_month_real_time'], 36.5)
        self.assertAlmostEqual(line['prev_month_hours'], 122.75)
        self.assertAlmostEqual(line['prev_month_real_time'], 150.0)
        self.assertEqual(round(line['variation_pct'], 2), -75.67)

    def test_non_validated_absence_is_ignored(self):
        calendar = self._create_calendar()
        employee = self._create_employee('Employee Draft Leave', calendar)
        self._create_timesheet(employee, '2026-03-05', 8.0)
        self._create_leave(
            employee, '2026-03-12', '2026-03-12', validated=False)
        lines_by_name = self._get_lines_by_employee_name()
        line = lines_by_name['Employee Draft Leave']
        self.assertEqual(line['absence_hours_month'], 0.0)

    def test_employee_without_timesheets_does_not_break_report(self):
        calendar = self._create_calendar()
        employee = self._create_employee('Employee No Timesheet', calendar)
        with self._freeze_today():
            report_data = self.report_sender._get_report_data()
        employee_names = [
            line.get('employee_name') for line in report_data['report_lines']
        ]
        self.assertNotIn(employee.name, employee_names)

    def test_template_render_includes_new_columns_and_na(self):
        calendar = self._create_calendar()
        employee = self._create_employee('Employee Template NA', calendar)
        self._create_timesheet(employee, '2026-03-05', 8.0)
        with self._freeze_today():
            ctx = self.report_sender._get_report_data()
        template = self.env.ref(
            'hr_timesheet_employee_report.'
            'email_template_employee_timesheet_report')
        body_html = template.with_context(**ctx)._render_field(
            'body_html', [self.partner.id])[self.partner.id]
        self.assertIn('% Variation', body_html)
        self.assertIn('Worked / Absence hours', body_html)
        self.assertIn('N/A', body_html)

    def test_send_email_dispatches_when_valid_recipients_exist(self):
        calendar = self._create_calendar()
        employee = self._create_employee('Employee Send Mail', calendar)
        self._create_timesheet(employee, '2026-03-05', 8.0)
        user_group = self.env.ref('base.group_user')
        recipient_user = self.env['res.users'].with_context(
            no_reset_password=True
        ).create({
            'email': 'timesheet_recipient@example.com',
            'groups_id': [(6, 0, [user_group.id])],
            'login': 'timesheet_recipient',
            'name': 'Timesheet Recipient',
        })
        group = self.env.ref(
            'hr_timesheet_employee_report.group_timesheet_report_recipients')
        group.write({'users': [(4, recipient_user.id)]})
        with self._freeze_today(), patch(
            'odoo.addons.mail.models.mail_template.'
            'MailTemplate.send_mail',
            return_value=True
        ) as mocked_send_mail:
            self.report_sender._send_employee_timesheet_report_email()
        self.assertGreaterEqual(mocked_send_mail.call_count, 1)
        self.assertTrue(mocked_send_mail.call_args.kwargs.get('force_send'))

    def test_employee_without_calendar_uses_zero_hours(self):
        calendar = self._create_calendar()
        employee = self._create_employee('Employee Without Calendar', calendar)
        employee.write({'resource_calendar_id': False})
        self._create_timesheet(employee, '2026-03-05', 8.0)
        lines_by_name = self._get_lines_by_employee_name()
        line = lines_by_name['Employee Without Calendar']
        self.assertEqual(line['available_hours_month'], 0.0)
        self.assertEqual(line['absence_hours_month'], 0.0)
        self.assertEqual(line['net_available_hours_month'], 0.0)

    def test_validated_absence_cross_month_counts_only_current_overlap(self):
        calendar = self._create_calendar()
        employee = self._create_employee(
            'Employee Cross Month Leave', calendar)
        self._create_timesheet(employee, '2026-03-05', 8.0)
        leave = self._create_leave(employee, '2026-02-27', '2026-03-03')
        lines_by_name = self._get_lines_by_employee_name()
        line = lines_by_name['Employee Cross Month Leave']
        month_start = date(2026, 3, 1)
        month_end = date(2026, 3, 31)
        leave_start = fields.Datetime.to_datetime(leave.date_from).date()
        leave_end = fields.Datetime.to_datetime(leave.date_to).date()
        overlap_start = max(leave_start, month_start)
        overlap_end = min(leave_end, month_end)
        expected_days = 0
        for current_date in self.report_sender._iter_dates(
                overlap_start, overlap_end):
            if current_date.weekday() < 5:
                expected_days += 1
        expected_absence_hours = expected_days * calendar.hours_per_day
        self.assertAlmostEqual(
            line['absence_hours_month'], expected_absence_hours)

    def test_send_email_without_report_lines_does_not_dispatch(self):
        with self._freeze_today(), patch(
            'odoo.addons.mail.models.mail_template.'
            'MailTemplate.send_mail',
            return_value=True
        ) as mocked_send_mail:
            self.report_sender._send_employee_timesheet_report_email()
        self.assertFalse(mocked_send_mail.called)

    def test_send_email_filters_inactive_or_missing_email_recipients(self):
        calendar = self._create_calendar()
        employee = self._create_employee(
            'Employee Filter Recipients', calendar)
        self._create_timesheet(employee, '2026-03-05', 8.0)
        user_group = self.env.ref('base.group_user')
        valid_user = self.env['res.users'].with_context(
            no_reset_password=True
        ).create({
            'email': 'timesheet_valid@example.com',
            'groups_id': [(6, 0, [user_group.id])],
            'login': 'timesheet_valid',
            'name': 'Timesheet Valid',
        })
        inactive_user = self.env['res.users'].with_context(
            no_reset_password=True
        ).create({
            'active': False,
            'email': 'timesheet_inactive@example.com',
            'groups_id': [(6, 0, [user_group.id])],
            'login': 'timesheet_inactive',
            'name': 'Timesheet Inactive',
        })
        no_email_user = self.env['res.users'].with_context(
            no_reset_password=True
        ).create({
            'groups_id': [(6, 0, [user_group.id])],
            'login': 'timesheet_no_email',
            'name': 'Timesheet No Email',
        })
        group = self.env.ref(
            'hr_timesheet_employee_report.group_timesheet_report_recipients')
        group.write({
            'users': [(6, 0, [
                valid_user.id, inactive_user.id, no_email_user.id
            ])],
        })
        with self._freeze_today(), patch(
            'odoo.addons.mail.models.mail_template.'
            'MailTemplate.send_mail',
            return_value=True
        ) as mocked_send_mail:
            self.report_sender._send_employee_timesheet_report_email()
        self.assertEqual(mocked_send_mail.call_count, 1)
        email_values = mocked_send_mail.call_args.kwargs.get('email_values')
        self.assertEqual(
            email_values.get('email_to'),
            valid_user.partner_id.email_formatted)
