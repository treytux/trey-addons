###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import api, fields, models


class ProjectTask(models.Model):
    _inherit = 'project.task'

    cost_center_id = fields.Many2one(
        string='Cost center',
        comodel_name='account.analytic.cost_center',
        compute='_compute_cost_center',
        store=True,
        readonly=False,
        tracking=True,
        domain="['|', ('company_id', '=', False), ('company_id', '=', company_id)]"
    )

    @api.depends('project_id')
    def _compute_cost_center(self):
        for task in self.filtered(lambda task: not task.cost_center_id):
            project = (
                task.display_project_id
                if task.parent_id and task.display_project_id
                else task.project_id
            )
            task.cost_center_id = project.cost_center_id
