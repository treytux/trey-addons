# -*- coding: utf-8 -*-
# License, author and contributors information in:
# __openerp__.py file at the root folder of this module.

from openerp import models, api
import logging

_log = logging.getLogger(__name__)


class WarningMessaging(models.Model):
    _inherit = 'warning.messaging'

    @api.one
    def do_send_msg(self, objs, action):
        if self.model_id.name == 'sale.order':
            for order in objs:
                partner_ids = [order.user_id and order.user_id.partner_id and
                               order.user_id.partner_id.id] or []

                order.with_context(mail_post_autofollow=False).message_post(
                    body=self.body, partner_ids=partner_ids)
            return True
        else:
            return super(WarningMessaging, self).do_send_msg(objs, action)
