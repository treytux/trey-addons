###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import fields, models


class ProjectTaskType(models.Model):
    _inherit = 'project.task.type'

    allow_voting = fields.Boolean(
        string='Allow voting',
    )
