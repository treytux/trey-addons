###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import fields, models


class ProjectTask(models.Model):
    _inherit = 'project.task'

    analytic_unit_balance = fields.Float(
        related='project_id.analytic_account_id.unit_balance',
        string='Analytic unit balance',
    )
