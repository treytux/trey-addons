# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp import api, fields, models
import datetime


class ResPartner(models.Model):
    _inherit = 'res.partner'

    expiration_date = fields.Date(
        string='Expiration date',
        help="Expiration date of subscription")
    free_date = fields.Date(
        string='Free date',
        help="Date of free subcription")

    @api.model
    def cron_partner_subscriptions_email_reminder(self, days_notify):
        date_compare = (datetime.datetime.now() -
                        datetime.timedelta(days_notify)).strftime("%Y-%m-%d")
        partners = self.env['res.partner'].search([(
            'expiration_date', '=', date_compare)])
        template = self.env['email.template'].search(
            [('name', '=', 'Subscription expiration reminder')], limit=1)
        for partner in partners:
            for user in partner.user_ids:
                template.send_mail(user.id, force_send=True)
        return True
