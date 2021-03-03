###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import api, models


class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'

    @api.multi
    def pricelist_get(self):
        self.ensure_one()
        return self.order_id.partner_id.supplier_pricelist_id

    @api.onchange('product_id')
    def onchange_product_id_multiple_discount(self):
        self = self.with_context(ref_price=self.price_unit)
        super(PurchaseOrderLine, self).onchange_product_id_multiple_discount()

    @api.model
    def _apply_value_from_seller(self, seller):
        super()._apply_value_from_seller(seller)
        if not seller:
            return
        self.onchange_product_id_multiple_discount()
