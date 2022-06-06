###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import fields, models


class ProjectProject(models.Model):
    _inherit = 'project.project'

    parent_id = fields.Many2one(
        comodel_name='project.project',
        string='Project parent',
    )
