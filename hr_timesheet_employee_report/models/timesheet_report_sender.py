###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
import logging
from datetime import datetime, time, timedelta

from odoo import _, fields, models

_logger = logging.getLogger(__name__)


class TimesheetReportSender(models.AbstractModel):
    _name = 'timesheet.report.sender'
    _description = 'Timesheet Report Sender'

    @staticmethod
    def _get_month_hours_range(month_start, month_end):
        start_dt = datetime.combine(month_start, time.min)
        end_dt = datetime.combine(month_end + timedelta(days=1), time.min)
        return start_dt, end_dt

    @staticmethod
    def _iter_dates(start_date, end_date):
        current_date = start_date
        while current_date <= end_date:
            yield current_date
            current_date += timedelta(days=1)

    def _get_employee_available_and_absence_hours(
            self, employee, cur_month_start, cur_month_end):
        if not employee.resource_calendar_id:
            _logger.warning(
                'Employee %s has no working calendar. Available and '
                'absence hours default to 0.',
                employee.display_name)
            return 0.0, 0.0
        month_start_dt, next_month_start_dt = self._get_month_hours_range(
            cur_month_start, cur_month_end)
        calendar = employee.resource_calendar_id
        working_weekdays = {
            int(attendance.dayofweek)
            for attendance in calendar.attendance_ids
        }
        hours_per_day = calendar.hours_per_day or 8.0
        available_hours = 0.0
        for current_date in self._iter_dates(cur_month_start, cur_month_end):
            if current_date.weekday() in working_weekdays:
                available_hours += hours_per_day
        leaves = self.env['hr.leave'].search([
            ('employee_id', '=', employee.id),
            ('state', '=', 'validate'),
            ('date_from', '<', fields.Datetime.to_string(next_month_start_dt)),
            ('date_to', '>', fields.Datetime.to_string(month_start_dt)),
        ])
        absence_hours = 0.0
        for leave in leaves:
            leave_start = fields.Datetime.to_datetime(leave.date_from).date()
            leave_end = fields.Datetime.to_datetime(leave.date_to).date()
            overlap_start = max(leave_start, cur_month_start)
            overlap_end = min(leave_end, cur_month_end)
            if overlap_start > overlap_end:
                continue
            leave_hours = 0.0
            for current_date in self._iter_dates(overlap_start, overlap_end):
                if current_date.weekday() in working_weekdays:
                    absence_hours += hours_per_day
                    leave_hours += hours_per_day
        return available_hours, absence_hours

    def _get_report_data(self):
        today = fields.Date.today()
        cur_month_start = today.replace(day=1)
        if today.month == 12:
            next_month_start = cur_month_start.replace(
                year=today.year + 1, month=1)
        else:
            next_month_start = cur_month_start.replace(
                month=today.month + 1)
        cur_month_end = next_month_start - timedelta(days=1)
        prev_month_end = cur_month_start - timedelta(days=1)
        prev_month_start = prev_month_end.replace(day=1)
        cur_month_label = cur_month_start.strftime('%Y-%m')
        prev_month_label = prev_month_start.strftime('%Y-%m')
        _logger.info(
            'Generating timesheet report. Current period: '
            '%s (%s to %s). Previous period: %s (%s to %s)',
            cur_month_label,
            fields.Date.to_string(cur_month_start),
            fields.Date.to_string(cur_month_end),
            prev_month_label,
            fields.Date.to_string(prev_month_start),
            fields.Date.to_string(prev_month_end))
        report_lines = {}
        analytic_line = self.env['account.analytic.line']
        prev_month_domain = [
            ('date', '>=', fields.Date.to_string(prev_month_start)),
            ('date', '<=', fields.Date.to_string(prev_month_end)),
            ('employee_id', '!=', False),
        ]
        prev_month_gdata = analytic_line.read_group(
            prev_month_domain,
            fields=['employee_id', 'unit_amount', 'real_time'],
            groupby=['employee_id'])
        for data in prev_month_gdata:
            employee_id = data['employee_id'][0]
            employee_name = data['employee_id'][1]
            if employee_id not in report_lines:
                report_lines[employee_id] = {
                    'employee_name': employee_name,
                    'prev_month_hours': 0.0,
                    'cur_month_hours': 0.0,
                    'prev_month_real_time': 0.0,
                    'cur_month_real_time': 0.0,
                }
            report_lines[employee_id]['prev_month_hours'] = data.get(
                'unit_amount', 0.0)
            report_lines[employee_id]['prev_month_real_time'] = data.get(
                'real_time', report_lines[employee_id]['prev_month_hours'])
        cur_month_domain = [
            ('date', '>=', fields.Date.to_string(cur_month_start)),
            ('date', '<=', fields.Date.to_string(cur_month_end)),
            ('employee_id', '!=', False),
        ]
        cur_month_gdata = analytic_line.read_group(
            cur_month_domain,
            fields=['employee_id', 'unit_amount', 'real_time'],
            groupby=['employee_id'])
        for data in cur_month_gdata:
            employee_id = data['employee_id'][0]
            employee_name = data['employee_id'][1]
            if employee_id not in report_lines:
                report_lines[employee_id] = {
                    'employee_name': employee_name,
                    'prev_month_hours': 0.0,
                    'cur_month_hours': 0.0,
                    'prev_month_real_time': 0.0,
                    'cur_month_real_time': 0.0,
                }
            elif not report_lines[employee_id].get('employee_name'):
                report_lines[employee_id]['employee_name'] = employee_name
            report_lines[employee_id]['cur_month_hours'] = data.get(
                'unit_amount', 0.0)
            report_lines[employee_id]['cur_month_real_time'] = data.get(
                'real_time', report_lines[employee_id]['cur_month_hours'])
        employee_ids = list(report_lines)
        employees = self.env['hr.employee'].browse(employee_ids)
        employees_by_id = {employee.id: employee for employee in employees}
        for employee_id, line_data in report_lines.items():
            prev_month_real_time = line_data.get('prev_month_real_time', 0.0)
            cur_month_real_time = line_data.get('cur_month_real_time', 0.0)
            if prev_month_real_time > 0:
                variation_pct = (
                    (cur_month_real_time - prev_month_real_time)
                    / prev_month_real_time) * 100.0
            else:
                variation_pct = None
            employee = employees_by_id.get(employee_id)
            available_hours, absence_hours = (
                self._get_employee_available_and_absence_hours(
                    employee, cur_month_start, cur_month_end)
                if employee else (0.0, 0.0))
            cur_month_hours = max(
                line_data.get('cur_month_hours', 0.0) - absence_hours,
                0.0)
            line_data['variation_pct'] = variation_pct
            line_data['cur_month_hours'] = cur_month_hours
            line_data['available_hours_month'] = available_hours
            line_data['absence_hours_month'] = absence_hours
            line_data['net_available_hours_month'] = max(
                available_hours - absence_hours, 0.0)
        final_report_lines = sorted(
            list(report_lines.values()),
            key=lambda x: x.get('employee_name', ''))
        return {
            'cur_month_label': cur_month_label,
            'prev_month_label': prev_month_label,
            'report_lines': final_report_lines,
        }

    def _send_employee_timesheet_report_email(self):
        _logger.info(
            'Starting employee timesheet report email dispatch...')
        try:
            context = dict(self._context)
            report_data_ctx = self._get_report_data()
            if not report_data_ctx['report_lines']:
                _logger.info(
                    'No timesheet data found for the period. No email will '
                    'be sent.')
                return
            template = self.env.ref(
                'hr_timesheet_employee_report.'
                'email_template_employee_timesheet_report',
                raise_if_not_found=True)
            recipient_group = self.env.ref(
                'hr_timesheet_employee_report.'
                'group_timesheet_report_recipients',
                raise_if_not_found=False)
            if not recipient_group:
                _logger.warning(_(
                    'Recipient group "group_timesheet_report_recipients" not '
                    'found. Email will not be sent.'))
                return
            users = recipient_group.users
            if users:
                recipient_partners = users.filtered(
                    lambda u: u.active and u.partner_id.email).mapped(
                        'partner_id')
            else:
                recipient_partners = self.env['res.partner']
            if not recipient_partners:
                _logger.info(_(
                    'No active users with email found in group '
                    '"group_timesheet_report_recipients". '
                    'Email will not be sent.'))
                return
            context.update(report_data_ctx)
            sent_count = 0
            for partner in recipient_partners:
                context['lang'] = partner.lang if partner.lang else 'en_US'
                template.with_context(**context).send_mail(
                    partner.id,
                    force_send=True,
                    email_values={'email_to': partner.email_formatted})
                _logger.info(
                    'Timesheet report email sent to: %s',
                    partner.email_formatted)
                sent_count += 1
            if sent_count > 0:
                _logger.info(
                    'Total of %s timesheet report emails sent.', sent_count)
            else:
                _logger.info(_(
                    'No emails were sent (no valid recipients found after '
                    'filtering).'))
        except Exception as error:
            _logger.error(
                'Error generating or sending timesheet report: %s',
                error, exc_info=True)
