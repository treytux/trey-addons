# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp import models, fields


class WizLastPricesFromSaleOrderLine(models.TransientModel):
    _name = 'wiz.last.prices.from.sale.order.line'
    _description = 'Last prices from sale order lines and pos lines.'

    name = fields.Char(
        string='Name')
    sale_order_line_ids = fields.Many2many(
        comodel_name='sale.order.line',
        relation='last_price_sale_order_line_rel',
        column1='last_price_id',
        column2='sale_order_line_id',
        readonly=True)
    pos_order_line_ids = fields.Many2many(
        comodel_name='pos.order.line',
        relation='last_price_pos_order_line_rel',
        column1='last_price_id',
        column2='pos_order_line_id',
        readonly=True)
