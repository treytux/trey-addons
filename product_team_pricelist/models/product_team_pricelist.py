###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import api, fields, models


class ProductTeamPricelist(models.Model):
    _name = 'product.team.pricelist'
    _description = 'Product Pricelist for Sales Teams'

    product_id = fields.Many2one(
        comodel_name='product.template',
        string='Product',
        required=True,
    )
    team_id = fields.Many2one(
        comodel_name='crm.team',
        string='Sales Team',
        required=True,
    )
    carrier_id = fields.Many2one(
        comodel_name='delivery.carrier',
        string='Carrier',
    )
    commission = fields.Float(
        string='Commission (%)',
    )
    profit = fields.Float(
        compute='_compute_profit',
        string='Profit',
    )
    sale_price = fields.Float(
        string='Sale Price',
    )
    shipping_price = fields.Float(
        string='Shipping Price',
    )
    standard_price = fields.Float(
        string='Standard Price',
    )

    @api.depends(
        'product_id', 'commission', 'sale_price',
        'shipping_price', 'standard_price')
    def _compute_profit(self):
        for product_id in self:
            product_id.profit = product_id.sale_price - (
                product_id.standard_price + product_id.shipping_price) - (
                product_id.sale_price * (0 + (product_id.commission / 100)))
