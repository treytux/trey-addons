###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import api, fields, models
from odoo.addons import decimal_precision as dp
from odoo.tools import float_is_zero


class ProductProduct(models.Model):
    _inherit = 'product.product'

    cost_category_price = fields.Float(
        string='Cost Category Price',
        digits=dp.get_precision('Product Price'),
    )

    @api.multi
    def price_compute(
            self, price_type, uom=False, currency=False, company=False):
        res = super().price_compute(price_type, uom, currency, company)
        rounding = self.env.user.company_id.currency_id.rounding
        if price_type != 'cost_category_price':
            return res
        if not uom and self._context.get('uom'):
            uom = self.env['uom.uom'].browse(self._context['uom'])
        if not currency and self._context.get('currency'):
            currency = self.env['res.currency'].browse(
                self._context['currency'])
        prices = dict.fromkeys(self.ids, 0.0)
        for product in self:
            prices[product.id] = product.cost_category_price or 0.00
            if float_is_zero(
                    prices[product.id], precision_rounding=rounding) or \
                    product.cost_category_price == \
                    product.product_tmpl_id.cost_category_price:
                product.cost_category_price = self.cost_category_price
            prices[product.id] += product.price_extra
            if self._context.get('no_variant_attributes_price_extra'):
                prices[product.id] += sum(
                    self._context.get('no_variant_attributes_price_extra'))
            if uom:
                prices[product.id] = product.uom_id._compute_price(
                    prices[product.id], uom)
            if currency:
                prices[product.id] = product.currency_id._convert(
                    prices[product.id], currency, product.company_id,
                    fields.Date.today())
        return prices
