###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import models


class MailMail(models.Model):
    _inherit = 'mail.mail'

    def send(self, auto_commit=False, raise_exception=False):
        mail_server_obj = self.env['ir.mail_server'].sudo()
        config_parameter_obj = self.env['ir.config_parameter']
        for mail in self:
            mail_server = False
            user_not_allowed = False
            server_domain_search = (
                mail.author_id.email and '@' in mail.author_id.email
                and mail.author_id.email.split('@')[1] or False)
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
                        continue
                    res_id = (mail.model and mail.res_id
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
                    if mail.message_type == 'notification' or user_not_allowed:
                        mail.email_from = '%s <%s>' % (
                            mail.author_id
                            and mail.author_id.name.replace(',', ' ') or '',
                            company_catchall_email)
            return super(
                MailMail,
                self.with_context(force_server_id=mail_server.id)).send(
                    auto_commit=auto_commit, raise_exception=raise_exception)
