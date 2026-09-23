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
        index=True,
    )
    team_id = fields.Many2one(
        comodel_name='crm.team',
        string='Sales Team',
        required=True,
        index=True,
    )
    carrier_id = fields.Many2one(
        comodel_name='delivery.carrier',
        string='Carrier',
    )
    market_commission_percent = fields.Float(
        string='Commission market (%)',
    )
    profit = fields.Float(
        compute='_compute_profit',
        string='Profit',
    )
    profit_percent = fields.Float(
        string='Profit (%)',
    )
    sale_price = fields.Float(
        string='Sale Price',
        compute='_compute_sale_price',
    )
    shipping_price = fields.Float(
        string='Shipping Price',
    )
    standard_price = fields.Float(
        related='product_id.standard_price',
    )
    name = fields.Char(
        related='product_id.name',
    )

    @api.depends('standard_price', 'shipping_price', 'profit_percent')
    def _compute_profit(self):
        for team_pricelist in self:
            net_price = (
                (team_pricelist.standard_price + team_pricelist.shipping_price)
                * (1 + (team_pricelist.profit_percent / 100)))
            team_pricelist.profit = (
                net_price - (
                    team_pricelist.standard_price
                    + team_pricelist.shipping_price))

    @api.depends(
        'standard_price', 'shipping_price', 'profit_percent',
        'market_commission_percent')
    def _compute_sale_price(self):
        for team_pricelist in self:
            team_pricelist.sale_price = ((
                (team_pricelist.standard_price + team_pricelist.shipping_price)
                * (1 + (team_pricelist.profit_percent / 100)))
                * (1 + (team_pricelist.market_commission_percent / 100)))
