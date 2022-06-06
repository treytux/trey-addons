###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import api, models


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    @api.multi
    @api.onchange('partner_shipping_id', 'partner_id', 'company_id')
    def onchange_partner_shipping_id(self):
        res = super().onchange_partner_shipping_id()
        if not self.partner_shipping_id:
            return res
        default_carrier = self.partner_shipping_id.default_carrier_id
        parent_default_carrier = (
            self.partner_shipping_id.parent_id.default_carrier_id)
        self.carrier_id = default_carrier.id if default_carrier else (
            parent_default_carrier.id if parent_default_carrier else None)
        return res
