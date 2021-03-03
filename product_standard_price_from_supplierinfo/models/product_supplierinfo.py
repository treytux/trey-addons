###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import api, models


class ProductSupplierinfo(models.Model):
    _inherit = 'product.supplierinfo'

    @api.model
    def create(self, vals):
        res = super().create(vals)
        res._compute_standard_price()
        return res

    @api.multi
    def write(self, vals):
        res = super().write(vals)
        if any([f in vals for f in ['sequence', 'price', 'discount']]):
            self._compute_standard_price()
        return res

    def _compute_standard_price(self):
        if self._name != 'product.supplierinfo':
            return
        for info in self:
            if info.product_id:
                info.product_id.standard_price = info.price_get()
            elif len(info.product_tmpl_id.product_variant_ids) == 1:
                sellers = info.product_tmpl_id.seller_ids.sorted('sequence')
                price = sellers[0].price_get()
                info.product_tmpl_id.standard_price = price
                info.product_tmpl_id._set_standard_price()
                variant = info.product_tmpl_id.product_variant_ids
                variant.standard_price = price
                variant._set_standard_price(price)
            elif len(info.product_tmpl_id.product_variant_ids) > 1:
                lines = {}
                sellers = info.product_tmpl_id.seller_ids.sorted('sequence')
                for seller in sellers:
                    item = lines.setdefault(seller.product_id.id, [])
                    item.append(seller)
                info.product_tmpl_id.standard_price = 0.
                for variant in info.product_tmpl_id.product_variant_ids:
                    key = variant.id if variant.id in lines else False
                    price = lines[key][0].price_get()
                    variant.standard_price = price
                    variant._set_standard_price(price)

    def price_get(self):
        self.ensure_one()
        return (
            self.discount
            and (self.price * (1 - self.discount / 100)) or self.price)
