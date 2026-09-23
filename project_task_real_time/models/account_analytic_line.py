###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import api, fields, models


class AccountAnalyticLine(models.Model):
    _inherit = 'account.analytic.line'

    real_time = fields.Float(
        string='Real time',
    )

    @api.onchange('unit_amount')
    def _onchange_partner_id(self):
        if not self.real_time:
            self.real_time = self.unit_amount
