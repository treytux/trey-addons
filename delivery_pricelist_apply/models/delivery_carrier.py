###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import _, models


class DeliveryCarrier(models.Model):
    _inherit = 'delivery.carrier'

    def rate_shipment(self, order):
        res = super().rate_shipment(order)
        is_shipping_free = (
            res.get('warning_message')
            and _('The shipping is free') in res.get('warning_message')
            and res.get('price') == 0.0)
        if is_shipping_free:
            return res
        res['price'] = self.product_id.with_context(
            pricelist=order.pricelist_id.id, uom=self.product_id.uom_id.id
        ).price
        return res
