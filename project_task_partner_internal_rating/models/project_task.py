###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import fields, models


class ProjectTask(models.Model):
    _inherit = 'project.task'

    partner_rating = fields.Selection(
        string='Partner rating',
        related='partner_id.commercial_partner_id.evaluation',
    )
