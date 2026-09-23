###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import fields, models


class SaleReport(models.Model):
    _inherit = 'sale.report'

    season_id = fields.Many2one(
        comodel_name='product.season',
        string='Season in sale line',
    )

    def _query(self, with_clause='', fields=None, groupby='', from_clause=''):
        if not fields:
            fields = {}
        fields['season_id'] = ', l.season_id as season_id'
        groupby += ', l.season_id'
        return super()._query(with_clause, fields, groupby, from_clause)
