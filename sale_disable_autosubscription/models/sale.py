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

    @api.multi
    def message_subscribe(self, partner_ids=None, subtype_ids=None):
        partner_in_followers = self.partner_id in self.message_follower_ids
        autofollow_key = 'mail_post_autofollow' in self.env.context
        if (not self.env.context.get('fetchmail_cron_running') and
                not autofollow_key or partner_in_followers):
            return super(SaleOrder, self).message_subscribe(
                partner_ids, subtype_ids)
        partners_to_add = self.env.context.get('partners_to_add')
        if not self.env.context.get('force_partner_subscribe'):
            partner_ids = list(set(partner_ids) - set(self.partner_id.ids))
        if partners_to_add:
            partner_ids.extend(partners_to_add)
        return super(SaleOrder, self).message_subscribe(
            partner_ids, subtype_ids)

    @api.multi
    def message_post(self, **kwargs):
        partners_to_add = kwargs.get('partner_ids', False)
        res = super(SaleOrder, self.with_context(
            partners_to_add=partners_to_add)).message_post(**kwargs)
        return res
