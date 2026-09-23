###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import fields, models


class ProjectProject(models.Model):
    _inherit = 'project.project'

    financial = fields.Boolean(
        related='budget_id.financial',
    )
    include_subtasks = fields.Boolean(
        related='budget_id.include_subtasks',
    )
