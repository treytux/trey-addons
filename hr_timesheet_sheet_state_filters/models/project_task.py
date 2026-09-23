###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import api, fields, models


class ProjectTask(models.Model):
    _inherit = 'project.task'

    effective_hours_pending = fields.Float(
        string='Hours effective pending',
        compute='_compute_effective_hours_by_state',
        store=True,
    )
    effective_hours_approve = fields.Float(
        string='Hours effective approve',
        compute='_compute_effective_hours_by_state',
        store=True,
    )

    @api.depends('timesheet_ids.unit_amount', 'timesheet_ids.sheet_id.state')
    def _compute_effective_hours_by_state(self):
        for task in self:
            approve_lines = task.timesheet_ids.filtered(
                lambda ln: ln.sheet_id and ln.sheet_id.state == 'done')
            task.effective_hours_approve = sum(
                approve_lines.mapped('unit_amount'))
            task.effective_hours_pending = (
                task.effective_hours - task.effective_hours_approve)
