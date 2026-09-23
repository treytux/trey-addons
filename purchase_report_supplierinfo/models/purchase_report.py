# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp import fields, models


class PurchaseReport(models.Model):
    _inherit = 'purchase.report'
    _auto = False

    product_supplierinfo = fields.Char(
        string='Product supplierinfo',
        readonly=True,
    )

    def _select(self):
        select_str = super(PurchaseReport, self)._select()
        return '%s %s' % (select_str, ', l.name AS product_supplierinfo')

    def _group_by(self):
        group_by_str = super(PurchaseReport, self)._group_by()
        return '%s %s' % (group_by_str, ', l.name')
