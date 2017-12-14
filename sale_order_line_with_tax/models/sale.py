# -*- coding: utf-8 -*-
# License, author and contributors information in:
# __openerp__.py file at the root folder of this module.
from openerp import models, fields, api
import logging
_log = logging.getLogger(__name__)


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    price_with_tax = fields.Float(
        string='Price with taxs',
        compute='_compute_price_with_tax')

    @api.one
    @api.depends('product_id', 'product_uom_qty', 'product_uom', 'price_unit',
                 'tax_id', 'discount')
    def _compute_price_with_tax(self):
        taxs = self.tax_id.compute_all(
            (self.price_unit * (1.0 - (self.discount or 0.0) / 100.0)),
            self.product_uom_qty, None, self.order_id.partner_id)
        taxs['total_included']
        self.price_with_tax = taxs['total_included']
