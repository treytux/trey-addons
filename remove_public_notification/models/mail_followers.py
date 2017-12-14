# -*- coding: utf-8 -*-
# License, author and contributors information in:
# __openerp__.py file at the root folder of this module.
from openerp import models, api


class MailNotification(models.Model):
    _inherit = 'mail.notification'

    @api.multi
    def get_partners_to_email(self, message):
        res = super(MailNotification, self).get_partners_to_email(
            message=message)
        if message.type == 'notification':
            values = []
            user_obj = self.env['res.users']
            partner_ids = self.env['res.partner'].browse(res)
            for partner_id in partner_ids:
                for user in partner_id.user_ids:
                    env_user = self.env(self.env.cr, user.id,
                                        self.env.context)
                    if not user_obj.with_env(env_user).has_group(
                            'base.group_public'):
                        values.append(partner_id.id)
            return list(set(values))
        else:
            return res
