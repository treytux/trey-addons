# -*- coding: utf-8 -*-
# License, author and contributors information in:
# __openerp__.py file at the root folder of this module.
from openerp import models, api


class MailMail(models.Model):
    _inherit = 'mail.mail'

    @api.model
    def _get_partner_access_link(self, mail, partner=None):
        super(MailMail, self)._get_partner_access_link(
            mail=mail, partner=partner)
        return ''
