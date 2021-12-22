###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import fields, models


class CrmTeam(models.Model):
    _inherit = 'crm.team'

    is_market = fields.Boolean(
        string='Is a market',
    )
    market_commission = fields.Float(
        string='Market commission',
    )
    market_carrier_id = fields.Many2one(
        comodel_name='delivery.carrier',
        string='Carrier',
    )

    def _price_carrier_compute(self, product, standard_price=None):
        self.ensure_one()
        standard_price = standard_price or product.standard_price
        if not self.market_carrier_id:
            return standard_price
        sale = self.env['sale.order'].new({
            'company_id': self.env.user.company_id,
            'partner_id': self.env.user.company_id.partner_id.id,
            'order_line': [
                (0, 0, {
                    'product_id': product.id,
                    'product_uom_qty': 1,
                    'price_unit': standard_price,
                }),
            ]
        })
        carrier_price = self.market_carrier_id.rate_shipment(sale)
        return standard_price + carrier_price['price']

    def price_cost_compute(self, product, standard_price=None):
        self.ensure_one()
        standard_price = self._price_carrier_compute(product, standard_price)
        return standard_price * (1 + (self.market_commission / 100))
