###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import fields, models


class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    task_id = fields.Many2one(
        comodel_name='project.task',
        string='Task',
    )

    def _prepare_analytic_lines(self):
        self.ensure_one()
        res = super()._prepare_analytic_lines()
        if len(res) == 1:
            res[0]['task_id'] = self.task_id.id
        return res
