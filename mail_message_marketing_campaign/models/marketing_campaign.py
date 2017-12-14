# -*- coding: utf-8 -*-
# License, author and contributors information in:
# __openerp__.py file at the root folder of this module.
from openerp import models, fields, api, _, exceptions
import logging
_log = logging.getLogger(__name__)


class MarketingCampaign(models.Model):
    _name = 'marketing.campaign'
    _inherit = ['marketing.campaign', 'mail.thread', 'ir.needaction_mixin']

    state = fields.Selection(
        track_visibility='onchange')

    @api.model
    def get_email_from(self):
        email_froms = self.env['ir.mail_server'].search(
            [('active', '=', True)])
        if not email_froms.exists():
            raise exceptions.Warning(_(
                'Not exist any mail server in active state, the email can not '
                'be send.'))
        return email_froms[0].smtp_user

    @api.multi
    def send_email(self, email_to, subject, body_html, attachment_ids=None):
        email_from = self.get_email_from()
        mail_values = {
            'email_from': email_from,
            'email_to': email_to,
            'subject': subject,
            'body_html': body_html,
            'state': 'outgoing',
            'type': 'email'}
        if attachment_ids is not None and len(attachment_ids) > 0:
            mail_values['attachment_ids'] = [
                (0, 0, a) for a in attachment_ids]
        mail = self.env['mail.mail'].create(mail_values)
        mail.send()
        return True
