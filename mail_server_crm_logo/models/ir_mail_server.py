##############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
##############################################################################
from odoo import models


class IrMailServer(models.Model):
    _inherit = 'ir.mail_server'

    def _get_message_team(self, message):
        message_id = message.get('Message-Id')
        if not message_id:
            return False
        mail_message = self.env['mail.message'].sudo().search([
            ('message_id', '=', message_id),
        ], limit=1)
        if mail_message.model not in [
                'sale.order', 'stock.picking', 'account.move']:
            return False
        record = self.env[mail_message.model].sudo().browse(mail_message.res_id)
        if not record.exists():
            return False
        if mail_message.model == 'stock.picking':
            return record.sale_id.team_id if record.sale_id else False
        return record.team_id

    def _replace_html_parts_logo(self, message, team):
        for part in message.walk():
            if part.get_content_maintype() == 'multipart':
                continue
            if part.get_content_type() != 'text/html' or part.get_filename():
                continue
            payload = part.get_payload(decode=True)
            if not payload:
                continue
            charset = part.get_content_charset() or 'utf-8'
            body_html = payload.decode(charset, errors='replace')
            new_body_html = team._replace_email_logo(body_html)
            if new_body_html != body_html:
                part.set_content(
                    new_body_html, subtype=part.get_content_subtype() or 'html',
                    charset=charset)

    def _prepare_email_message(self, message, smtp_session):
        team = self._get_message_team(message)
        if team:
            self._replace_html_parts_logo(message, team)
        return super()._prepare_email_message(message, smtp_session)
