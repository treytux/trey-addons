###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import fields, models


class ProjectTask(models.Model):
    _inherit = 'project.task'

    is_declined = fields.Boolean(
        string='Declined task',
        related='stage_id.declined_status',
    )
    reason_to_decline = fields.Char(
        string='Reason to decline',
        copy=False,
    )
    allow_decline = fields.Boolean(
        string='Decline allowed',
        related='stage_id.allow_decline',
    )
