# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp import api, fields, models


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    no_shipping_types = ['service']
    requires_shipping = fields.Boolean(
        compute='_requires_shipping',
        string='Requires shipping')

    @api.model
    def _get_no_shipping_types(self):
        return self.no_shipping_types

    @api.one
    def _requires_shipping(self):
        requires_shipping = False
        for line in self.order_line:
            if line.product_id.type not in self._get_no_shipping_types():
                requires_shipping = True
                break
        self.requires_shipping = requires_shipping
