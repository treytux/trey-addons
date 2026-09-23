###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import api, fields, models


class ProjectTask(models.Model):
    _inherit = 'project.task'

    timesheet_blocked = fields.Boolean(
        string='Timesheet registration blocked',
        compute='_compute_timesheet_blocked',
        compute_sudo=True,
        help='Timesheets cannot be added or edited when the task is blocked '
             'or its project blocks timesheet registration.',
    )

    @api.depends(
        'kanban_state', 'project_id.block_timesheet', 'project_id.active',
        'project_id.stage_id.fold')
    def _compute_timesheet_blocked(self):
        for task in self:
            project = task.project_id
            task.timesheet_blocked = bool(
                task.kanban_state == 'blocked' or (project and (
                    project.block_timesheet
                    or not project.active
                    or project.stage_id.fold)))
