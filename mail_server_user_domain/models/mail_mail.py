###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import models
from odoo.tools import email_normalize


class MailMail(models.Model):
    _inherit = 'mail.mail'

    def send(self, auto_commit=False, raise_exception=False):
        mail_server_obj = self.env['ir.mail_server'].sudo()
        config_parameter_obj = self.env['ir.config_parameter']

        def _set_mail_server(mail):
            mail_server = mail_server_obj
            user_not_allowed = False
            if not mail.email_from:
                return mail_server
            email_normalized = email_normalize(mail.email_from)
            server_domain_search = (
                email_normalized and '@' in email_normalized
                and email_normalized.split('@')[1] or False)
            if not server_domain_search:
                return mail_server
            mail_server = mail_server_obj.search([
                ('smtp_user', 'ilike', server_domain_search),
            ], limit=1)
            if not mail_server:
                user_not_allowed = True
                if mail.fetchmail_server_id:
                    mail_server = mail_server_obj.search([
                        ('smtp_user', '=', mail.fetchmail_server_id.user),
                    ], limit=1)
                else:
                    model = mail.model or self.env.context.get('active_model')
                    if not model:
                        return mail_server
                    res_id = (
                        mail.model and mail.res_id
                        or self.env.context.get('active_ids'))
                    record = self.env[model].browse(res_id)
                    if (record.exists() and 'company_id'
                            in record._fields.keys()):
                        company_email = record.company_id.email
                        server_domain_search = (
                            '@' in company_email
                            and company_email.split('@')[1]
                            if company_email else False)
                        mail_server = mail_server_obj.search([
                            ('smtp_user', 'ilike', server_domain_search),
                        ], limit=1)
            if mail_server:
                mail.mail_server_id = mail_server.id
                catchall_alias = config_parameter_obj.get_param(
                    'mail.catchall.alias')
                if catchall_alias:
                    company_catchall_email = '%s@%s' % (
                        catchall_alias, mail_server.smtp_user.split('@')[1])
                    mail.reply_to = company_catchall_email
                    if (user_not_allowed and mail.author_id
                            and mail.author_id.name):
                        mail.email_from = '%s <%s>' % (
                            mail.author_id.name.replace(',', ' '),
                            company_catchall_email)
            return mail_server

        for mail in self:
            _set_mail_server(mail)
        return super().send(
            auto_commit=auto_commit, raise_exception=raise_exception)
