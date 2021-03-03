###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import api, models


class ProductProduct(models.Model):
    _inherit = 'product.product'

    @api.multi
    def _select_seller(self, partner_id=False, quantity=0.0, date=None,
                       uom_id=False, params=False):
        self.ensure_one()
        supplierinfo = super()._select_seller(
            partner_id=partner_id, quantity=quantity, date=date,
            uom_id=uom_id, params=params)
        if not supplierinfo or not partner_id or not quantity:
            return supplierinfo
        pricelist = supplierinfo.name.supplier_pricelist_id.with_context(
            ref_price=supplierinfo.ref_price)
        if not pricelist:
            return supplierinfo
        product = (
            supplierinfo.product_id
            or supplierinfo.product_tmpl_id.product_variant_id)
        price, rule_id = pricelist.get_product_price_rule(
            product, quantity, partner_id)
        supplierinfo.with_context(no_update_ref_price=True).price = price
        return supplierinfo.with_context(force_price=price)
