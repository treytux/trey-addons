###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import api, models


class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    @api.onchange('partner_id', 'company_id')
    def _onchange_partner_id(self):
        res = super()._onchange_partner_id()
        if not self.partner_id:
            return res
        else:
            apply_fiscal_position_purchase = (
                self.type in ('in_invoice', 'in_refund')
                and self.partner_id.property_account_position_purchase_id)
            if apply_fiscal_position_purchase:
                self.fiscal_position_id = (
                    self.partner_id.property_account_position_purchase_id.id)
            return res
