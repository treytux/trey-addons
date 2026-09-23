###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import api, fields, models


class AccountAnalyticLine(models.Model):
    _inherit = 'account.analytic.line'

    cost_center_id = fields.Many2one(
        compute='_compute_cost_center',
        store=True,
        readonly=False,
    )

    @api.depends('project_id')
    def _compute_cost_center(self):
        account_lines = self.filtered(
            lambda line: not line.cost_center_id and line.task_id)
        for line in account_lines:
            line.cost_center_id = line.task_id.cost_center_id
