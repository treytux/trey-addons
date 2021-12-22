###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import models


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    def _compute_available_carrier(self):
        super()._compute_available_carrier()
        carriers = self.env['delivery.carrier'].search([])
        for order in self:
            available_carriers = carriers.filtered(
                lambda d: not d.not_available_from or (
                    d.not_available_from and (
                        order.amount_total <= d.limit_amount)))
            order.available_carrier_ids = (
                available_carriers.available_carriers(
                    order.partner_shipping_id) if order.partner_shipping_id
                else available_carriers)
