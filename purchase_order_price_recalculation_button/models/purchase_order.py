###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import models


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    def button_recalculate_purchase_prices(self):
        return self._recalculate_prices()
