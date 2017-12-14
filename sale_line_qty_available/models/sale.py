# -*- coding: utf-8 -*-
# License, author and contributors information in:
# __openerp__.py file at the root folder of this module.
from openerp import models, fields


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    product_qty_available = fields.Float(
        string='Quantity On Hand',
        related='product_id.qty_available',
        readonly=True)
