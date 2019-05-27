# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
import urllib
from openerp import models, api


class MailMail(models.Model):
    _inherit = ['mail.mail']

    @api.model
    def send_get_mail_body(self, mail, partner=None):
        body = super(MailMail, self).send_get_mail_body(mail, partner=partner)
        params = {
            'db': self.env.cr.dbname,
            'res_id': mail.res_id,
            'email': mail.email_to,
            'token': self.env['mail.mass_mailing'].hash_create(
                mail.mailing_id.id,
                mail.res_id,
                mail.email_to),
        }
        url = '/mail/mailing/%s/unsubscribe?%s' % (
            mail.mailing_id.id, urllib.urlencode(params))
        return body.replace('/UNSUBSCRIBE_URL', url)
