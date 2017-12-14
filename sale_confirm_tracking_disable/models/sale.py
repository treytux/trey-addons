# -*- coding: utf-8 -*-
# License, author and contributors information in:
# __openerp__.py file at the root folder of this module.
from openerp import models, api


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    @api.one
    def write(self, vals):
        user_obj = self.pool.get("res.users")
        for follower in self.message_follower_ids:
            for user in follower.user_ids:
                if user_obj.has_group(self.env.cr, user.id,
                                      'base.group_public'):
                    return super(
                        SaleOrder, self.with_context(
                            mail_notrack=True)).write(vals)
        return super(SaleOrder, self).write(vals)
