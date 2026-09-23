###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import api, models


class ProjectProject(models.Model):
    _inherit = 'project.project'

    @api.onchange('type_id')
    def _onchange_type_id(self):
        domain = [('case_default', '=', True)]
        if self.type_id:
            domain += [('project_type_ids', 'in', [self.type_id.id])]
        else:
            domain += [('project_type_ids', '=', False)]
        default_stages = self.env['project.task.type'].search(domain)
        self.type_ids = [(6, 0, default_stages.ids)]
