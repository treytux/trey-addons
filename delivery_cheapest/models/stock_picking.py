###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import _, models
from odoo.exceptions import ValidationError


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    def _get_stock_available_delivery_carrier_domain(self):
        return [
            ('include_cheapest_carrier', '=', True),
            '|',
            ('not_available_from', '=', False),
            '&',
            ('not_available_from', '=', True),
            ('limit_amount', '>=', self.sale_id.amount_total),
        ]

    def assign_cheapest_delivery_carrier(self):
        carriers = self.env['delivery.carrier'].search(
            self._get_stock_available_delivery_carrier_domain())
        if not carriers:
            raise ValidationError(
                _('No shipping methods found with the check for calculating '
                    'the most economical shipping method activated.'))
        prices_dict = {}
        for carrier in self.sale_id._get_available_delivery_carrier(carriers):
            res = carrier.rate_shipment(self.sale_id)
            if res['success']:
                prices_dict.update({
                    carrier.id: res['price'],
                })
        self.carrier_id = prices_dict and (
            min(prices_dict, key=prices_dict.get)) or False
        res = self.carrier_id.rate_shipment(self.sale_id) if (
            self.carrier_id) else False
        self.carrier_price = res['price'] if res and res['success'] else 0.0
