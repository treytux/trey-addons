##############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
##############################################################################
from odoo import api, models


class MailMessage(models.Model):
    _inherit = 'mail.message'

    @api.model_create_multi
    def create(self, values_list):
        for values in values_list:
            model = values.get('model')
            if model not in ['sale.order', 'stock.picking', 'account.move']:
                continue
            record = self.env[model].browse(values.get('res_id'))
            team = False
            if model == 'stock.picking':
                team = record.sale_id.team_id if record.sale_id else False
            else:
                team = record.team_id
            if not team or not team.mail_domain:
                continue
            email_from = values.get('email_from')
            if email_from:
                context = self.env.context.copy()
                context['force_mail_message_from'] = True
                self.env.context = context
                values['email_from'] = team._replace_email_domain(
                    email_from, team.mail_domain)
            try:
                email_reply_to = self._get_reply_to(values)
                if email_reply_to:
                    values['reply_to'] = team._replace_email_domain(
                        email_reply_to, team.mail_domain)
            except Exception:
                pass
        return super().create(values_list)
