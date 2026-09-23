###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from datetime import date

from odoo import fields, models


class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    annual_hourly_cost_ids = fields.One2many(
        comodel_name='hr.employee.annual.hourly.cost',
        inverse_name='employee_id',
        string='Hourly cost periods',
    )

    def get_period_hourly_cost(self, line_date):
        self.ensure_one()
        employee = self.sudo()
        if not line_date:
            return employee.hourly_cost or 0.0
        line_date = fields.Date.to_date(line_date)
        today = fields.Date.today()
        period_costs = (
            self.env['hr.employee.annual.hourly.cost'].sudo().search([
                ('employee_id', '=', employee.id),
                ('date_start', '<=', line_date),
            ],
                order='date_start desc, id desc')
        )
        for period_cost in period_costs:
            period_end = period_cost.date_end or today
            if period_end >= line_date:
                return period_cost.hourly_cost
        next_period_cost = (
            self.env['hr.employee.annual.hourly.cost'].sudo().search([
                ('employee_id', '=', employee.id),
                ('date_start', '>', line_date),
            ],
                order='date_start asc',
                limit=1)
        )
        if next_period_cost:
            return next_period_cost.hourly_cost
        return employee.hourly_cost or 0.0

    def get_annual_hourly_cost(self, year):
        self.ensure_one()
        if not year:
            return self.get_period_hourly_cost(False)
        january_first = date(year, 1, 1)
        return self.get_period_hourly_cost(january_first)
