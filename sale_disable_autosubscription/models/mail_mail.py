# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp import models, api


class MailMail(models.Model):
    _inherit = 'mail.mail'

    @api.model
    def _postprocess_sent_message(self, mail, mail_sent=True):
        if not mail_sent or mail.model != 'sale.order':
            return super(MailMail, self)._postprocess_sent_message(
                mail, mail_sent=True)
        order = self.env['sale.order'].browse(mail.res_id)
        partner = order.partner_id
        if partner in mail.partner_ids:
            order.with_context(
                force_partner_subscribe=True).message_subscribe(partner.ids)
        return super(MailMail, self)._postprocess_sent_message(
            mail, mail_sent=True)
