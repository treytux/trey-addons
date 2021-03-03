###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
import odoo.addons.decimal_precision as dp
from odoo import api, fields, models


class ProductProduct(models.Model):
    _inherit = 'product.product'

    margin_limit = fields.Float(
        string='Margin limit (%)',
        digits=dp.get_precision('Discount'),
    )
    margin_price_limit = fields.Float(
        string='Sales price min',
        compute='_compute_margin_price_limit',
        digits=dp.get_precision('Product Price'),
    )

    @api.depends('margin_limit', 'standard_price')
    def _compute_margin_price_limit(self):
        for product in self:
            if product.margin_limit >= 100:
                product.margin_limit = 99.99
            margin = product.margin_limit and (product.margin_limit / 100) or 0
            product.margin_price_limit = product.standard_price / (1 - margin)
