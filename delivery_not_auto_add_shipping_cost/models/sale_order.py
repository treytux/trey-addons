###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import models


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    def action_confirm(self):
        res = super().action_confirm()
        self.invoice_shipping_on_delivery = bool(
            self.carrier_id and self.carrier_id.auto_shipping_cost)
        return res
