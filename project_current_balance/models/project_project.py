###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import api, fields, models


class ProjectProject(models.Model):
    _inherit = 'project.project'

    extra_balance = fields.Float(
        string='Extra balance',
    )
    extra_balance_date = fields.Date(
        string='Date from apply extra balance',
        default=fields.Date.today,
        required=True,
    )
    current_balance = fields.Float(
        string='Current Balance',
        compute='_compute_current_balance',
        help='Remaining hours available in the current period',
    )

    def _get_balance_timesheets(self, start_date):
        self.ensure_one()
        return self.env['account.analytic.line'].search([
            ('project_id', '=', self.id),
            ('date', '>=', start_date),
        ])

    def _get_base_current_balance(self):
        self.ensure_one()
        start_date = self.extra_balance_date or fields.Date.today()
        hours_logged = sum(
            self._get_balance_timesheets(start_date).mapped('unit_amount'))
        return self.extra_balance - hours_logged

    @api.depends(
        'extra_balance',
        'extra_balance_date',
        'timesheet_ids.date',
        'timesheet_ids.unit_amount',
    )
    def _compute_current_balance(self):
        for project in self:
            project.current_balance = project._get_base_current_balance()
