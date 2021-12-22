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
        string='Timesheet stats holidays',
        help='Contains a string with vacation days separated by commas, '
        'for example "2,0,1,2,1,1,0,1,0,1,1,2"',
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

    @api.multi
    def send_mail(self):
        template = self.env.ref(
            'hr_timesheet_stats.email_template_hr_timesheet_stats')
        for employee in self.search([]):
            template.send_mail(employee.id)
