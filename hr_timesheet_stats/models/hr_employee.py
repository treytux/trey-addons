###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
import calendar
from datetime import datetime

from dateutil.relativedelta import relativedelta
from odoo import api, fields, models


class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    hr_timesheet_stats_holidays = fields.Char(
        string='Vacation days',
        help='Contains a string with vacation days separated by commas, '
        'for example "11,9,8,12,10,9,10,9,9,10,9,13"',
    )

    def get_last_month_day(self, date):
        last_month = datetime.today() - relativedelta(months=1)
        return calendar.monthrange(last_month.year, last_month.month)[1]

    def get_employee_analytic_lines(self):
        last_month = datetime.today() - relativedelta(months=1)
        last_month_day = self.get_last_month_day(last_month)
        return self.env['account.analytic.line'].search([
            ('employee_id', '=', self.id),
            ('date', '<=', last_month.replace(day=last_month_day)),
            ('date', '>=', last_month.replace(day=1)),
        ])

    def total_real_hours(self):
        analytic_lines = self.get_employee_analytic_lines()
        return sum([ln.real_time for ln in analytic_lines])

    def total_works(self):
        analytic_lines = self.get_employee_analytic_lines()
        return len(analytic_lines)

    def total_unit_amount(self):
        analytic_lines = self.get_employee_analytic_lines()
        return sum([ln.unit_amount for ln in analytic_lines])

    def get_month_holidays_days(self):
        last_month = datetime.today() - relativedelta(months=1)
        holidays = 0
        if self.hr_timesheet_stats_holidays:
            holidays = int(
                self.hr_timesheet_stats_holidays.split(',')[
                    last_month.month - 1])
        return holidays

    def get_month_stats_days(self):
        last_month = datetime.today() - relativedelta(months=1)
        return calendar.mdays[last_month.month]

    def get_month_working_days(self):
        return self.get_month_stats_days() - self.get_month_holidays_days()

    def get_productivity(self, hours):
        productive_hours = (
            self.resource_calendar_id.daily_productive_hours
            and self.resource_calendar_id.daily_productive_hours or 0)
        return (
            100 / (self.get_month_working_days() * productive_hours)
            * hours)

    @api.multi
    def send_mail(self):
        template = self.env.ref(
            'hr_timesheet_stats.email_template_hr_timesheet_stats')
        for employee in self.search([]):
            template.send_mail(employee.id)
