###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import api, fields, models


class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    task_id = fields.Many2one(
        comodel_name='project.task',
        string='Task',
    )

    @api.multi
    def _prepare_analytic_line(self):
        res = super()._prepare_analytic_line()
        res[0]['task_id'] = self.task_id.id
        return res
