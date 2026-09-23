###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import _, api, models
from odoo.exceptions import ValidationError


class AccountAnalyticLine(models.Model):
    _inherit = 'account.analytic.line'

    @api.constrains('task_id', 'unit_amount', 'date')
    def _check_timesheet_not_blocked(self):
        for line in self:
            task = line.task_id
            if task and task.timesheet_blocked:
                raise ValidationError(_(
                    'You cannot register or modify timesheets on task '
                    '"%s": it is blocked or its project blocks timesheet '
                    'registration.') % task.display_name)
