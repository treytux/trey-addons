###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import fields, models


class SaleReport(models.Model):
    _inherit = 'sale.report'

    margin_percent = fields.Float(
        string='Margin (%)'
    )

    def _query(self, with_clause='', fields=None, groupby='', from_clause=''):
        if fields is None:
            fields = {}
        fields['margin_percent'] = ', SUM(l.margin_percent) AS margin_percent'
        return super()._query(with_clause, fields, groupby, from_clause)
