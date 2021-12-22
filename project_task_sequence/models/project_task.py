###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import fields, models


class ProjectTask(models.Model):
    _inherit = 'project.task'

    task_priority_position = fields.Integer(
        string='Task priority position',
        help='Task position in priority list',
    )
