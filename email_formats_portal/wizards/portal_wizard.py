# -*- coding: utf-8 -*-
# License, author and contributors information in:
# __openerp__.py file at the root folder of this module.
from openerp.osv import osv
from openerp.tools.translate import _
from openerp import models, api
import logging
_log = logging.getLogger(__name__)


class wizard_user(models.TransientModel):
    _inherit = 'portal.wizard.user'

    @api.model
    def _render_template(self, this_user, template_name, data):
        return self.env.ref(template_name) and self.env.ref(
            template_name).render(template_name, data) or ''

    @api.model
    def _get_portal_wizard_data(self, wizard_user, this_user, user):
        env = self.env
        res_partner = env['res.partner']
        portal_url = res_partner.with_context(
            signup_force_type_in_url='')._get_signup_url_for_action(
            [user.partner_id.id])
        portal_url = (
            portal_url[user.partner_id.id] if user.partner_id.id in portal_url
            else '')
        res_partner.signup_prepare([user.partner_id.id])
        base_url = env['ir.config_parameter'].get_param('web.base.url')
        data = {
            'company': this_user.company_id.name,
            'portal': wizard_user.wizard_id.portal_id.name,
            'welcome_message': wizard_user.wizard_id.welcome_message or "",
            'db': env.cr.dbname,
            'name': user.name,
            'login': user.login,
            'base_url': base_url,
            'signup_url': user.signup_url,
            'portal_url': portal_url,
        }
        return data

    @api.model
    def _send_email(self, wizard_user):
        env = self.env
        if not env.user.email:
            raise osv.except_osv(
                _('Email Required'),
                _('You must have an email address in your User Preferences to'
                  ' send emails.'))
        user = self.sudo()._retrieve_user(wizard_user)
        data = self.with_context(lang=user.lang)._get_portal_wizard_data(
            wizard_user, env.user, user)
        subject = self.with_context(lang=user.lang)._render_template(
            env.user, 'email_formats_portal.wizard_user_subject', data)
        body_html = self.with_context(lang=user.lang)._render_template(
            env.user, 'email_formats_portal.wizard_user_body_html', data)
        mail_mail = self.env['mail.mail']
        mail_values = {
            'email_from': env.user.email,
            'email_to': user.email,
            'subject': subject,
            'body_html': body_html,
            'state': 'outgoing',
            'type': 'email',
        }
        mail_id = mail_mail.create(mail_values)
        return mail_mail.send([mail_id])
