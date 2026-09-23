###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import models


class AccountAnalyticLine(models.Model):
    _inherit = 'account.analytic.line'

    def _timesheet_postprocess_values(self, values):
        lines = super()._timesheet_postprocess_values(values)
        for line in self:
            if not line.move_line_id:
                continue
            if 'amount' in lines[line.id]:
                del lines[line.id]['amount']
        return lines
