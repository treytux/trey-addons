# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp import models, fields


class AccountInvoiceReport(models.Model):
    _inherit = 'account.invoice.report'
    _auto = False

    product_brand_id = fields.Many2one(
        comodel_name='product.brand',
        string='Brand',
        readonly=True)

    def _select(self):
        select_str = super(AccountInvoiceReport, self)._select()
        return '%s %s' % (select_str, ', sub.product_brand_id')

    def _sub_select(self):
        select_str = super(AccountInvoiceReport, self)._sub_select()
        return '%s %s' % (
            select_str, ', pt.product_brand_id AS product_brand_id')

    def _group_by(self):
        group_by_str = super(AccountInvoiceReport, self)._group_by()
        return '%s %s' % (group_by_str, ', pt.product_brand_id')
