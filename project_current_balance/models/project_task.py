###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import fields, models


class ProjectTask(models.Model):
    _inherit = 'project.task'

    current_balance = fields.Float(
        related='project_id.current_balance',
        string='Current Balance',
        readonly=True,
    )
