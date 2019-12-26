# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp import models, api


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    @api.multi
    def action_button_confirm(self):
        pre_followers = self.message_follower_ids
        res = super(SaleOrder, self).action_button_confirm()
        for follower in self.message_follower_ids:
            if follower not in pre_followers:
                self.message_unsubscribe([follower.id])
        return res
