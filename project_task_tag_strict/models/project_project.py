###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import api, models


class ProjectProject(models.Model):
    _inherit = 'project.project'

    @api.onchange('tag_ids')
    def check_task_tags(self):
        if isinstance(self.id, models.NewId):
            project_id = self._origin.id
        elif isinstance(self.id, (int,)):
            project_id = self.id
        tasks = self.env['project.task'].search([
            ('project_id', '=', project_id),
        ])
        for task in tasks:
            tag_list = []
            for tag in task.tag_ids:
                if tag.id not in self.tag_ids.ids:
                    tag_list.append(tag)
            task.write({'tag_ids': [(3, tag.id) for tag in tag_list]})
