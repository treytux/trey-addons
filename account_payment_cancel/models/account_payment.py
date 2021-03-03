###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import api, models


class AccountPayment(models.Model):
    _inherit = 'account.payment'

    @api.multi
    def cancel(self):
        res = super().cancel()
        for rec in self:
            rec.move_name = ''
        return res
