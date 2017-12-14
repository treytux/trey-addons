# -*- coding: utf-8 -*-
# License, author and contributors information in:
# __openerp__.py file at the root folder of this module.
from openerp import models, fields


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    pos_order_id = fields.Many2one(
        comodel_name='pos.order',
        string='Pos Order',
        readonly=True,
        help="Pos Order relationated.")
    state = fields.Selection([
        ('manage_from_pos', 'Manage from PoS')])
