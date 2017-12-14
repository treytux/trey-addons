# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp import models, api


class AccountPartnersLedger(models.TransientModel):
    _inherit = 'account.partner.ledger'

    @api.multi
    def pre_print_report(self, data):
        data = super(AccountPartnersLedger, self).pre_print_report(data)
        data['form'].update({'partner_ids': self.env.context['active_ids']})
        return data

    @api.multi
    def _print_report(self, data):
        res = super(AccountPartnersLedger, self)._print_report(data)
        res.update(
            {'report_name': 'account.account_report_partners_ledger_webkit'})
        data = self.pre_print_report(data)
        data.update({'model': 'ir.ui.menu'})
        del data['form']['initial_balance']
        return {
            'type': 'ir.actions.report.xml',
            'report_name': 'account.account_report_partners_ledger_webkit',
            'datas': data}
