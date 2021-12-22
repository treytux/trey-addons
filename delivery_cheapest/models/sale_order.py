###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import _, api, models
from odoo.exceptions import ValidationError


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    def _get_sale_available_delivery_carrier_domain(self):
        return [
            ('include_cheapest_carrier', '=', True),
            '|',
            ('not_available_from', '=', False),
            '&',
            ('not_available_from', '=', True),
            ('limit_amount', '>=', self.amount_total),
        ]

    def _get_available_delivery_carrier(self, carriers):
        return carriers.available_carriers(
            self.partner_shipping_id) if self.partner_shipping_id else carriers

    def assign_cheapest_delivery_carrier(self):
        carriers = self.env['delivery.carrier'].search(
            self._get_sale_available_delivery_carrier_domain())
        if not carriers:
            raise ValidationError(
                _('No shipping methods found with the check for calculating '
                    'the most economical shipping method activated.'))
        prices_dict = {}
        for carrier in self._get_available_delivery_carrier(carriers):
            res = carrier.rate_shipment(self)
            if res['success']:
                prices_dict.update({
                    carrier.id: res['price'],
                })
        self.carrier_id = prices_dict and (
            min(prices_dict, key=prices_dict.get)) or False
        if self.carrier_id:
            self.get_delivery_price()

    @api.multi
    def action_confirm(self):
        res = super().action_confirm()
        for order in self:
            if not order.picking_ids:
                continue
            for picking in order.picking_ids:
                picking.carrier_price = order.delivery_price
        return res
