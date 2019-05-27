# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp.addons.account_financial_report_webkit.report.partner_balance \
    import PartnerBalanceWebkit
from openerp.report.interface import report_int


class PartnerBalanceWebKitFix(PartnerBalanceWebkit):

    def _get_initial_balance_mode(self, start_period):

        super(PartnerBalanceWebKitFix, self)._get_initial_balance_mode(
            start_period)
        return 'opening_balance'


rep = report_int._reports[
    'report.account.account_report_partner_balance_webkit']
rep.parser = PartnerBalanceWebKitFix
