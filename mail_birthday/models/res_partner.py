###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import fields, models


class ResPartner(models.Model):
    _inherit = 'res.partner'

    def send_birthday_mail_alert(self):
        now = fields.Datetime.now().strftime('-%m-%d')
        template = self.env.ref('mail_birthday.birth_notification')
        partners = self.search([
            ('birthdate_date', '=like', '____%s' % now),
        ])
        for partner in partners:
            template.with_context(
                lang=partner.lang).send_mail(partner.id)
