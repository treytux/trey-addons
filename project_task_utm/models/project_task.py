###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import fields, models


class ProjectTask(models.Model):
    _inherit = 'project.task'

    utm_campaign_id = fields.Many2one(
        comodel_name='utm.campaign',
        string='Campaign',
    )
    utm_medium_id = fields.Many2one(
        comodel_name='utm.medium',
        string='Medium',
    )
    utm_source_id = fields.Many2one(
        comodel_name='utm.source',
        string='Source',
    )
