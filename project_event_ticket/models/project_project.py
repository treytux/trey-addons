###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import fields, models


class ProjectProject(models.Model):
    _inherit = 'project.project'

    event_ticket_ids = fields.One2many(
        comodel_name='event.event.ticket',
        inverse_name='project_id',
        string='Event Ticket',
        copy=True,
    )
