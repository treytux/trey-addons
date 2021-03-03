# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp import api, models


class SaleOrderConfirm(models.TransientModel):
    _name = 'sale.order.confirm'
    _description = 'Sale order confirm'

    @api.multi
    def button_accept(self):
        self.ensure_one()
        active_ids = self.env.context.get('active_ids', [])
        orders = self.env['sale.order'].browse(active_ids)
        for order in orders.filtered(lambda o: o.state in ['draft', 'sent']):
            order.action_button_confirm()
        return {'type': 'ir.actions.act_window_close'}
