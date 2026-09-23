###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import api, models


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    @api.onchange('partner_id', 'company_id')
    def onchange_partner_id(self):
        res = super().onchange_partner_id()
        if not self.partner_id:
            return res
        else:
            if self.partner_id.property_account_position_purchase_id:
                self.fiscal_position_id = (
                    self.partner_id.property_account_position_purchase_id.id)
            return res
