# -*- coding: utf-8 -*-
# License, author and contributors information in:
# __openerp__.py file at the root folder of this module.
from openerp import models, fields


class SaleReport(models.Model):
    _inherit = 'sale.report'
    _auto = False

    is_promotion_gift = fields.Boolean(
        string='Is promotion gift',
        readonly=True)

    def _select(self):
        select_str = super(SaleReport, self)._select()
        return '%s %s' % (
            select_str,
            ', l.is_promotion_gift')

    def _group_by(self):
        group_by_str = super(SaleReport, self)._group_by()
        return '%s ,l.is_promotion_gift' % group_by_str
