# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp import models, api, _


class IrCron(models.Model):
    _inherit = "ir.cron"

    @api.model
    def cron_block_when_unpaid(self):
        def _get_user_to_inform_per_company(self):
            company_ids = self.env['res.company'].search([])
            acc_settings_obj = self.env['account.config.settings']
            to_inform = []
            for company in company_ids:
                account_setting_ids = acc_settings_obj.search(
                    [('company_id', '=', company.id)])
                for account_setting in account_setting_ids:
                    if not account_setting.users_to_inform_ids:
                        continue
                    to_inform += [
                        user for user in account_setting.users_to_inform_ids]
            return list(set(to_inform))

        users_to_inform = _get_user_to_inform_per_company(self)
        if not users_to_inform:
            return False
        unpaid_partners = self.env['res.partner'].get_unpaid_partner()
        template = self.env.ref(
            'account_partner_debt_blocking.unpaid_email_cutomize')
        header = '<h1>' + _('Partners blocked') + '</h1><br/>'
        body_with_users = ', <br/> '.join([(p.name) for p in unpaid_partners])
        template.body_html += header + body_with_users
        for user_id in users_to_inform:
            template.email_from = user_id.company_id.email
            template.email_to = user_id.email
            template.subject = _('No payment partners list')
            template.sudo().send_mail(user_id.company_id.id, force_send=True)
        return True
