###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from datetime import date

from odoo import api, fields, models


class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    state = fields.Selection(
        selection=[
            ('applicant', 'Applicant'),
            ('employment', 'Employment'),
            ('discarded', 'Discarded'),
            ('inactive', 'Inactive'),
        ],
        string='State',
        default='applicant',
        track_visibility='always',
        copy=False,
    )
    states_history = fields.One2many(
        comodel_name='hr.employee.state.history',
        inverse_name='employee_id',
        string='States History',
    )

    @api.model
    def create(self, vals):
        res = super().create(vals)
        self.env['hr.employee.state.history'].create({
            'start_date': date.today(),
            'employee_id': res.id,
            'state': 'applicant',
        })
        return res

    def end_open_states(self, employee):
        employee_state_obj = self.env['hr.employee.state.history']
        last_state = employee_state_obj.search([
            ('employee_id', '=', employee.id),
            ('end_date', '=', False),
        ])
        if last_state:
            last_state.write({
                'end_date': date.today(),
            })

    def set_as_applicant(self):
        employee_state_obj = self.env['hr.employee.state.history']
        for employee in self:
            employee.state = 'applicant'
            self.end_open_states(employee)
            employee_state_obj.create({
                'start_date': date.today(),
                'employee_id': employee.id,
                'state': 'applicant',
            })

    def set_as_employee(self):
        employee_state_obj = self.env['hr.employee.state.history']
        for employee in self:
            employee.state = 'employment'
            self.end_open_states(employee)
            employee_state_obj.create({
                'start_date': date.today(),
                'employee_id': employee.id,
                'state': 'employment',
            })
            if employee.user_id and not employee.user_id.active:
                employee.user_id.active = True

    def set_as_discarded(self):
        employee_state_obj = self.env['hr.employee.state.history']
        for employee in self:
            employee.state = 'discarded'
            self.end_open_states(employee)
            employee_state_obj.create({
                'start_date': date.today(),
                'employee_id': employee.id,
                'state': 'discarded',
            })
            if employee.user_id:
                employee.user_id.active = False

    def set_as_inactive(self):
        employee_state_obj = self.env['hr.employee.state.history']
        for employee in self:
            employee.state = 'inactive'
            self.end_open_states(employee)
            employee_state_obj.create({
                'start_date': date.today(),
                'employee_id': employee.id,
                'state': 'inactive',
            })
            if employee.user_id:
                employee.user_id.active = False
