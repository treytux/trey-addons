###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import api, fields, models


class ProjectTask(models.Model):
    _inherit = 'project.task'

    pending_estimated_time = fields.Float(
        string='Pending estimated time',
        compute='_compute_pending_estimated_time',
    )

    @api.depends('activity_ids.pending_estimated_time')
    def _compute_pending_estimated_time(self):
        for task in self:
            task.pending_estimated_time = sum(
                task.activity_ids.mapped('pending_estimated_time'))
