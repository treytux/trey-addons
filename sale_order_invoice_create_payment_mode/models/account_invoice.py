###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import api, models


class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    @api.onchange('partner_id', 'company_id')
    def _onchange_partner_id(self):
        payment_mode = self.payment_mode_id
        res = super(AccountInvoice, self)._onchange_partner_id()
        if (payment_mode
                and self.env.context.get('active_model') == 'sale.order'):
            self.payment_mode_id = payment_mode.id
        return res
