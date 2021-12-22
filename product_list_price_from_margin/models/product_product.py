###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
import odoo.addons.decimal_precision as dp
from odoo import api, fields, models


class ProductProduct(models.Model):
    _inherit = 'product.product'

    margin = fields.Float(
        string='Margin (%)',
        digits=dp.get_precision('Discount'),
    )

    @api.model
    def create(self, vals):
        if self._context.get('force_margin'):
            vals['margin'] = self._context['force_margin']
        return super().create(vals)

    @api.depends('list_price', 'price_extra', 'standard_price', 'margin',
                 'product_tmpl_id.list_price')
    def _compute_product_lst_price(self):
        super()._compute_product_lst_price()
        for product in self:
            if product.margin >= 100:
                product.margin = 99.99
            margin = product.margin and (product.margin / 100) or 0
            if margin:
                product.lst_price = product.standard_price / (1 - margin)

    def _get_margin(self, lst_price=None):
        self.ensure_one()
        if lst_price is None:
            lst_price = self.lst_price
        if not self.standard_price:
            return 0
        margin = self.standard_price / (lst_price or 0.01)
        return (margin - 1) * -100

    @api.onchange('lst_price')
    def onchange_lst_price(self):
        for product in self:
            product.margin = product._get_margin()

    def _set_product_lst_price(self):
        for product in self:
            if self._context.get('uom'):
                uom = self.env['uom.uom'].browse(self._context['uom'])
                value = uom._compute_price(product.lst_price, product.uom_id)
            else:
                value = product.lst_price
            product.product_tmpl_id.list_price = value
            product.margin = self._get_margin(lst_price=value)

    def price_compute(self, price_type, uom=False, currency=False,
                      company=False):
        if price_type == 'variant_lst_price':
            return {p.id: p.lst_price for p in self}
        return super().price_compute(
            price_type, uom=uom, currency=currency, company=company)
