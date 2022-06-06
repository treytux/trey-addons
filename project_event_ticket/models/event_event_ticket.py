###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import fields, models


class EventTicket(models.Model):
    _inherit = 'event.event.ticket'

    project_id = fields.Many2one(
        comodel_name='project.project',
        string='Project',
    )
