# -*- coding: utf-8 -*-
# License, author and contributors information in:
# __openerp__.py file at the root folder of this module.
from openerp import models, api


class ProductPricelistItem(models.Model):
    _inherit = 'product.pricelist.item'

    @api.one
    def price_get(self, product_id, qty, partner_id, uom_id):
        '''Inherit the price_get function to calculate the price according to
        the selected unit. This price is obtained from the field 'UoM prices'
        of the product.'''
        res = super(ProductPricelistItem, self).price_get(
            product_id, qty, partner_id, uom_id)
        product_uom_price_obj = self.env['product.uom.price']
        product_obj = self.env['product.product']
        product = product_obj.browse(int(product_id))
        if uom_id and uom_id != product.uom_id.id:
            product_uom_prices = product_uom_price_obj.search([
                ('uom_id', '=', uom_id),
                ('product_tmpl_id', '=', product.product_tmpl_id.id)])
            if product_uom_prices.exists():
                return product_uom_prices[0].price
        return res and res[0] or 0
