###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import fields, models


class ProjectProject(models.Model):
    _inherit = 'project.project'

    unit_balance_display = fields.Selection(
        selection=[
            ('hidden', 'Hide'),
            ('effective', 'Show effective time'),
            ('real', 'Show effective and real time'),
        ],
        string='Project balance',
        default='hidden',
    )
