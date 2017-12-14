# -*- coding: utf-8 -*-
# License, author and contributors information in:
# __openerp__.py file at the root folder of this module.
from openerp import models, api, fields
import logging
_log = logging.getLogger(__name__)


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    is_promotion_gift = fields.Boolean(
        string='Is promotion gift',
        readonly=True,
        default=False)


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    @api.one
    def action_button_confirm(self):
        '''Inherit, to confirm the sales order, look for the lines order are
        gift to mark as a gift.'''
        res = super(SaleOrder, self).action_button_confirm()
        order_line_obj = self.env['sale.order.line']
        lines = []
        for line_gift in self.sale_final_gifts:
            order_lines = order_line_obj.search([
                ('order_id', '=', self.id),
                ('product_id', '=', line_gift.product.id),
                ('product_uom_qty', '=', line_gift.quantity),
                ('price_unit', '=', 0)])
            lines.append(order_lines)
        for line in lines:
            line.write({'is_promotion_gift': True})
        return res
