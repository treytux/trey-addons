###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import fields, models


class ProjectTask(models.Model):
    _inherit = 'project.task'

    has_pending_invoices = fields.Boolean(
        string='Has Pending Invoices',
        related='project_id.has_pending_invoices',
        help='Indicates if the related project has pending invoices.',
    )
