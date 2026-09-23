###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import fields, models


class ProjectTaskType(models.Model):
    _inherit = 'project.task.type'

    project_type_ids = fields.Many2many(
        comodel_name='project.type',
        relation='proyect_task_type_project_type_rel',
        column1='project_task_type',
        column2='proyect_type',
        string='Project types',
    )
