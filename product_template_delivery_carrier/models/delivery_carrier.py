###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import models


class DeliveryCarrier(models.Model):
    _inherit = 'delivery.carrier'

    def available_carriers(self, partner):
        res = super().available_carriers(partner)
        order_id = self.env.context.get('active_id') if self.env.context.get(
            'active_model') == 'sale.order' else False
        if not order_id:
            return res
        order = self.env['sale.order'].browse(order_id)
        products = order.order_line.filtered(
            lambda line: line.product_id and not line.is_delivery).mapped('product_id')
        if not products:
            return res
        common_carriers = None
        for product in products:
            product_carriers = product.carrier_ids
            if not product_carriers:
                common_carriers = None
                break
            if common_carriers is None:
                common_carriers = product_carriers
            else:
                common_carriers = common_carriers & product_carriers
            if not common_carriers:
                break
        if common_carriers:
            return res.filtered(lambda r: r in common_carriers)
        else:
            return self.env['delivery.carrier']
