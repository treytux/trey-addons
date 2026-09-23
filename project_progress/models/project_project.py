###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import api, fields, models


class ProjectProject(models.Model):
    _inherit = 'project.project'

    progress = fields.Float(
        string='Progress %',
        compute='_compute_progress',
    )

    @api.depends('task_ids.progress')
    def _compute_progress(self):
        for project in self:
            if not project.task_ids:
                project.progress = 0
                continue
            total_progress = sum(project.task_ids.mapped('progress'))
            project.progress = total_progress / len(project.task_ids)
