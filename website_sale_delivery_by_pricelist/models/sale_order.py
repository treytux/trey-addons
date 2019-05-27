###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import models


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    def _get_delivery_methods(self):
        return super()._get_delivery_methods().filtered(
            lambda c: c.pricelist_id == self.pricelist_id)
