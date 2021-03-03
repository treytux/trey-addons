###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import api, models


class ProjectTask(models.Model):
    _inherit = 'project.task'

    @api.onchange('project_id')
    def _onchange_project(self):
        res = super()._onchange_project()
        if self.project_id and self.project_id.main_technical_id:
            self.user_id = self.project_id.main_technical_id
        return res
