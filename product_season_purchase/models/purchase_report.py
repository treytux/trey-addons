# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp import models, fields


class PurchaseReport(models.Model):
    _inherit = 'purchase.report'
    _auto = False

    season_id = fields.Many2one(
        comodel_name='product.season',
        string='Season',
        readonly=True,
    )

    def _select(self):
        select_str = super(PurchaseReport, self)._select()
        return '%s %s' % (
            select_str,
            ''',
            t.season_id AS season_id
            ''')

    def _group_by(self):
        group_by_str = super(PurchaseReport, self)._group_by()
        return '%s %s' % (group_by_str, ', t.season_id')
