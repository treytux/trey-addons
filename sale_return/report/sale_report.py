###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import fields, models


class SaleReport(models.Model):
    _inherit = "sale.report"

    is_return = fields.Boolean(
        string='Is return',
    )

    def _query(self, with_clause='', fields=None, groupby='', from_clause=''):
        if fields is None:
            fields = {}
        fields['is_return'] = ', s.is_return as is_return'
        groupby += ', s.is_return'
        return super()._query(with_clause, fields, groupby, from_clause)
