# -*- coding: utf-8 -*-
# License, author and contributors information in:
# __openerp__.py file at the root folder of this module.

from openerp import models, fields


class AccountBalanceReport(models.TransientModel):
    _inherit = 'account.balance.report'

    start_page_count = fields.Integer(string='Start page count', default=1)
    show_date = fields.Boolean(string='Show date', default=True)

    def _print_report(self, cr, uid, ids, data, context=None):
        re = super(AccountBalanceReport, self)._print_report(
            cr, uid, ids, data, context=context)
        data = self.read(cr, uid, ids, ['start_page_count', 'show_date'],
                         context=context)[0]
        re['data']['form'].update(data)
        return re
