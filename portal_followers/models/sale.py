# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp import models, api


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    @api.model
    def create(self, vals):
        env = self.env
        sale_order = super(SaleOrder, self).create(vals)
        if 'partner_id' in vals:
            root_partner_id = sale_order.partner_id.root_partner_id
            order = env['sale.order'].browse(sale_order.id)
            order.write(
                {'message_follower_ids': [(6, 0, list(set(
                    sale_order.message_follower_ids.ids +
                    root_partner_id.message_follower_ids.ids)))]})
        return sale_order

    @api.multi
    def action_button_confirm(self):
        res = super(SaleOrder, self).action_button_confirm()
        if self.partner_id.is_company and self.partner_id.child_ids and \
           self.partner_id.message_follower_ids:
            self.message_unsubscribe([self.partner_id.id])
        return res
