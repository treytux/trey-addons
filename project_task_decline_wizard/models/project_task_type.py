###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class ProjectTaskType(models.Model):
    _inherit = 'project.task.type'

    allow_decline = fields.Boolean(
        string='Allow to decline tasks',
    )
    declined_status = fields.Boolean(
        string='Declined status',
        copy=False,
    )

    @api.constrains('declined_status')
    def _check_declined_status(self):
        declined_statuses = self.search([
            ('declined_status', '=', True),
        ])
        if len(declined_statuses) > 1:
            raise ValidationError(_('Only one declined status allowed'))
