###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import fields, models


class ProjectProject(models.Model):
    _inherit = 'project.project'

    project_group_id = fields.Many2one(
        string='Project group',
        comodel_name='project.group',
    )
