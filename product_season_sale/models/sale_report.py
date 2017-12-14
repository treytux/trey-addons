# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp import models, fields


class SaleReport(models.Model):
    _inherit = 'sale.report'
    _auto = False

    season_id = fields.Many2one(
        comodel_name='product.season',
        string='Season',
        readonly=True)

    def _select(self):
        select_str = super(SaleReport, self)._select()
        return '%s, t.season_id' % select_str

    def _group_by(self):
        group_by_str = super(SaleReport, self)._group_by()
        return '%s, t.season_id' % group_by_str
