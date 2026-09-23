###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import api, models


class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    @api.onchange('partner_id', 'company_id')
    def _onchange_partner_id(self):
        date_due = self.date_due
        res = super(AccountInvoice, self)._onchange_partner_id()
        if (date_due and not self.date_due
                and self.env.context.get('active_model') == 'sale.order'):
            self.date_due = date_due
        return res
