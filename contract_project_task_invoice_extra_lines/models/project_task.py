###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import fields, models


class ProjectTask(models.Model):
    _inherit = 'project.task'

    project_task_line_extra_ids = fields.One2many(
        string='Project task lines extra',
        comodel_name='project.task.line.extra',
        inverse_name='project_task_id',
        copy=True,
    )
    partner_ids = fields.Many2many(
        comodel_name='res.partner',
        relation='project_task_partner_id_rel',
        column1='task_id',
        column2='partner_id',
        string='Participants',
    )
