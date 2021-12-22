###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import fields, models


class ProjectTask(models.Model):
    _inherit = 'project.task'

    is_template = fields.Boolean(
        string='Is template',
        copy=False,
    )

    def get_copy_task_values(self):
        return {
            'name': self.name,
            'partner_id': False,
        }

    def create_task_from_template(self):
        new_task = self.copy(self.get_copy_task_values())
        return {
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'project.task',
            'target': 'current',
            'res_id': new_task.id,
            'type': 'ir.actions.act_window',
        }
