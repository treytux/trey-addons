###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import api, fields, models


class HrEmployeeStateHistory(models.Model):
    _name = 'hr.employee.state.history'
    _description = 'States History'

    start_date = fields.Date(
        string='Start Date',
    )
    end_date = fields.Date(
        string='End Date',
    )
    duration = fields.Integer(
        compute='_compute_duration',
        string='Duration (days)',
        store=True,
    )
    state = fields.Selection(
        selection=[
            ('applicant', 'Applicant'),
            ('employment', 'Employment'),
            ('discarded', 'Discarded'),
            ('inactive', 'Inactive'),
        ],
        string='State',
        default='applicant',
        copy=False,
        required=True,
    )
    employee_id = fields.Many2one(
        comodel_name='hr.employee',
    )

    @api.depends('end_date')
    def _compute_duration(self):
        for state_history in self:
            if state_history.end_date and state_history.start_date:
                state_history.duration = (
                    state_history.end_date - state_history.start_date).days
