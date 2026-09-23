###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import fields, models


class ProjectProject(models.Model):
    _inherit = 'project.project'

    block_picking = fields.Boolean(
        string='Block pickings',
        help='If enabled, stock moves cannot be added or edited on pickings '
             'linked to a task of this project.',
    )
