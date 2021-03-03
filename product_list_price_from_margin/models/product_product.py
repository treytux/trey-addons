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

    @api.depends('list_price', 'price_extra', 'standard_price', 'margin')
    def _compute_product_lst_price(self):
        super()._compute_product_lst_price()
        for product in self:
            if product.margin >= 100:
                product.margin = 99.99
            margin = product.margin and (product.margin / 100) or 0
            product.lst_price = product.standard_price / (1 - margin)

    @api.onchange('lst_price')
    def onchange_lst_price(self):
        for product in self:
            if not product.standard_price:
                product.margin = 0
                return
            margin = product.standard_price / (product.lst_price or 0.01)
            product.margin = (margin - 1) * -100
