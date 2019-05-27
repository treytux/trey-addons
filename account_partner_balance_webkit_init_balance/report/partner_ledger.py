# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp.addons.account_financial_report_webkit.report.partners_ledger \
    import PartnersLedgerWebkit
from openerp.report.interface import report_int


class PartnersLedgerWebKitFix(PartnersLedgerWebkit):

    def _get_initial_balance_mode(self, start_period):

        super(PartnersLedgerWebKitFix, self)._get_initial_balance_mode(
            start_period)
        return 'opening_balance'


rep = report_int._reports[
    'report.account.account_report_partners_ledger_webkit']
rep.parser = PartnersLedgerWebKitFix
