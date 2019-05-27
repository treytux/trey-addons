# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp import models, fields, api


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    date_value = fields.Date(
        string='Value date',
        states={'draft': [('readonly', False)]},
        help='Value date to compute due date on sale order invoice.')

    @api.model
    def _prepare_invoice(self, order, lines):
        vals = super(SaleOrder, self)._prepare_invoice(order, lines)
        if vals and order.date_value:
            vals['date_value'] = order.date_value
        return vals

    @api.multi
    def action_button_confirm(self):
        res = super(SaleOrder, self).action_button_confirm()
        if not self.date_value:
            return res
        for picking in self.picking_ids:
            picking.date_value = self.date_value
        return res
