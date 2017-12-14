# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp import models, fields


class SaleReport(models.Model):
    _inherit = 'sale.report'
    _auto = False

    product_brand_id = fields.Many2one(
        comodel_name='product.brand',
        string='Brand',
        readonly=True)

    def _select(self):
        select_str = super(SaleReport, self)._select()
        return '%s, t.product_brand_id AS product_brand_id' % select_str

    def _group_by(self):
        group_by_str = super(SaleReport, self)._group_by()
        return '%s, t.product_brand_id' % group_by_str
