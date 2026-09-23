# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp import fields, models


class AccountInvoiceReport(models.Model):
    _inherit = 'account.invoice.report'
    _auto = False

    product_supplierinfo = fields.Char(
        string='Product supplierinfo',
        readonly=True,
    )

    def _select(self):
        select_str = super(AccountInvoiceReport, self)._select()
        return '%s %s' % (select_str, ', sub.product_supplierinfo')

    def _sub_select(self):
        select_str = super(AccountInvoiceReport, self)._sub_select()
        return '%s %s' % (
            select_str, ', ail.name AS product_supplierinfo')

    def _group_by(self):
        group_by_str = super(AccountInvoiceReport, self)._group_by()
        return '%s %s' % (group_by_str, ', ail.name')
