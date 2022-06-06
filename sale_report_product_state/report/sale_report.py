###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import fields, models


class SaleReport(models.Model):
    _inherit = 'sale.report'

    product_state = fields.Char(
        string='Product State',
    )

    def _query(self, with_clause='', fields=None, groupby='', from_clause=''):
        fields = fields or {}
        fields['product_state'] = ', l.product_state AS product_state'
        groupby += ', l.product_state'
        return super()._query(with_clause, fields, groupby, from_clause)
