###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import fields, models


class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    project_task_line_extra_id = fields.Many2one(
        comodel_name='project.task.line.extra',
        string='Project task line extra',
    )
