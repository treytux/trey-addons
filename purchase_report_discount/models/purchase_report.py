# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp import models, fields


class PurchaseReport(models.Model):
    _inherit = 'purchase.report'
    _auto = False

    discount = fields.Float(
        string='Discount',
        readonly=True)
    price_discounted = fields.Float(
        string='Discounted Price',
        readonly=True)
    line_id = fields.Integer(
        string='Line Id')

    def _select(self):
        select_str = super(PurchaseReport, self)._select()
        return '%s %s' % (
            select_str,
            ''',
            l.discount AS discount,
            (sum(l.price_unit / cr.rate * l.product_qty) *
                (1 - l.discount / 100))::decimal(16,2) AS price_discounted,
            l.id AS line_id
            ''')

    def _group_by(self):
        group_by_str = super(PurchaseReport, self)._group_by()
        return '%s %s' % (group_by_str, ', l.discount, l.id')
