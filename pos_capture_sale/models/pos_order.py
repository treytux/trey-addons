# -*- coding: utf-8 -*-
# License, author and contributors information in:
# __openerp__.py file at the root folder of this module.

from openerp import models, fields


class PosOrder(models.Model):
    _inherit = 'pos.order'

    sale_order_id = fields.Many2one(
        comodel_name='sale.order',
        string='Sale Order',
        readonly=True,
        help="Sale Order relationated."
    )
