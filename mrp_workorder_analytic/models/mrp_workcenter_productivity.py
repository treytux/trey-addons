###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import api, fields, models


class MrpWorkcenterProductivity(models.Model):
    _inherit = 'mrp.workcenter.productivity'

    analytic_line_id = fields.Many2one(
        'account.analytic.line',
        string='Analytic Line',
        copy=False)

    @api.model
    def _compute_duration_units(self, duration):
        units, decimals = divmod(duration, 1)
        return round((units / 60) + (decimals / 100.0), 2)

    @api.model
    def _compute_employee(self):
        return self.env['hr.employee'].search([
            ('user_id', '=', self.user_id.id)], limit=1)

    @api.model
    def _compute_price(self, employee=None):
        price = 0
        if employee:
            price = employee.timesheet_cost
        return price

    @api.multi
    def _prepare_analytic_values(self):
        self.ensure_one()
        duration = self._compute_duration_units(self.duration)
        employee = self._compute_employee()
        price = self._compute_price(employee)
        values = {
            'name': f'{self.description}',
            'account_id': self.workorder_id.production_id.analytic_account_id.id,
            'unit_amount': duration,
            'amount': price * duration * -1,
            'product_uom_id': self.workorder_id.production_id.product_uom_id.id,
            'date': self.date_end,
            'productivity_id': self.id,
            'company_id': self.env.user.company_id.id,
            'user_id': self.user_id.id,
        }
        if employee:
            values['employee_id'] = employee.id
            values['department_id'] = employee.department_id.id
        return values

    @api.multi
    def _create_analytic_line(self):
        self.ensure_one()
        Line = self.env['account.analytic.line']
        line = Line.create(self._prepare_analytic_values())
        self.analytic_line_id = line.id
        return line
