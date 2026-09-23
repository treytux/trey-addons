###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import api, fields, models


class ProjectTask(models.Model):
    _inherit = 'project.task'

    planned_remaining_hours = fields.Float(
        string='Remaining hours planned',
        compute='_compute_planned_remaining_hours',
        readonly=True,
        store=True,
    )

    @api.depends('remaining_hours')
    def _compute_planned_remaining_hours(self):
        for task in self:
            task.planned_remaining_hours = max(0, task.remaining_hours)
