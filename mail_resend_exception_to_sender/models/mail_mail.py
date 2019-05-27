# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp import models, api, fields
from openerp.tools.translate import _
import logging
_log = logging.getLogger(__name__)


class MailMail(models.Model):
    _inherit = 'mail.mail'

    is_resend_exception = fields.Boolean(
        string='Is resend exception?',
        readonly=True,
        help="This field is marked when a forwarding mail is sent by "
             "exception. This will prevent you from sending more than one "
             "notice per failed email. \nFurther, to avoid sending exception "
             "mails from an exception mail, we also mark them as forwarded "
             "only to be forwarded once.")

    @api.model
    def cron_resend_exception_to_sender(self):
        mail_exceptions = self.env['mail.mail'].search([
            ('state', '=', 'exception'), ('is_resend_exception', '=', False)])
        for mail_exception in mail_exceptions:
            company = self.env.user.company_id
            if company.exception_sender_options == 'none':
                return False
            if company.exception_sender_options == 'email_from':
                email_to = mail_exception.email_from
            elif company.exception_sender_options == 'user_except_sender':
                email_to = ', '.join([
                    user.partner_id.email
                    for user in company.user_except_sender_ids
                    if user.partner_id.email != ''])
            elif company.exception_sender_options == 'both':
                email_to = ', '.join([
                    mail_exception.email_from,
                    ', '.join([
                        user.partner_id.email
                        for user in company.user_except_sender_ids
                        if user.partner_id.email != ''])])
            if email_to == '':
                _log.error(_(
                    'There is no recipient to send the email exception notice '
                    'mail with id = %s. It may be due to missing data in the '
                    'configuration or that the mail that failed has no sender '
                    'defined.') % mail_exception.id)
                return False
            delivery_to = (
                mail_exception.email_to or (
                    mail_exception.recipient_ids and
                    (','.join([
                        partner.email
                        for partner in mail_exception.recipient_ids]))) or '')
            body = _(
                'Failed mail delivery to \'%s\'.\nOriginal message:\n'
                '- Subject: %s\n- Body: %s') % (
                delivery_to, mail_exception.subject,
                mail_exception.body_html or mail_exception.body)
            new_mail = self.env['mail.mail'].create({
                'subject': _('Forward exception: %s') % mail_exception.subject,
                'email_from': self.env.user.partner_id.email,
                'email_to': email_to,
                'body_html': body,
                'type': 'email',
                'attachment_ids': [(6, 0, mail_exception.attachment_ids.ids)],
                'is_resend_exception': True})
            new_mail.send()
            mail_exception.write({'is_resend_exception': True})
