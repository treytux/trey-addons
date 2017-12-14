# -*- coding: utf-8 -*-
# License, author and contributors information in:
# __openerp__.py file at the root folder of this module.
from openerp import models, api


class MailNotification(models.Model):
    _inherit = 'mail.notification'

    @api.model
    def get_signature_footer(self, user_id, res_model=None, res_id=None,
                             user_signature=True):
        res = super(MailNotification, self).get_signature_footer(
            user_id=user_id, res_model=res_model, res_id=res_id,
            user_signature=user_signature)
        res = ""
        return res
