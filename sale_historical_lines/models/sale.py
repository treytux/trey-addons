# -*- coding: utf-8 -*-
# License, author and contributors information in:
# __openerp__.py file at the root folder of this module.
from openerp import models, api, fields


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    date_order = fields.Datetime(
        string='Date',
        related='order_id.date_order')
    historical_line_ids = fields.Many2many(
        comodel_name='sale.order.line',
        relation='sale_order_line_historical_rel',
        column1='line_id',
        column2='historical_id',
        compute='_compute_historical_lines',
        store=False,
        readonly=True)

    @api.one
    @api.depends('product_id')
    def _compute_historical_lines(self):
        if self.order_id.partner_id and self.product_id:
            domain = [
                ('order_partner_id', '=', self.order_id.partner_id.id),
                ('product_id', '=', self.product_id.id)]
            if self.order_id.id:
                domain.append(('order_id', '!=', self.order_id.id))
            self.historical_line_ids = [l.id for l in self.search(domain)]
