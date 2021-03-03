###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import fields, models


class SaleReport(models.Model):
    _inherit = 'sale.report'

    agents_name = fields.Char(
        string='Agents',
    )

    def _query(self, with_clause='', fields=None, groupby='', from_clause=''):
        if not fields:
            fields = {}
        fields['agents'] = ', s.agents_name as agents_name'
        groupby += ', s.agents_name'
        return super()._query(with_clause, fields, groupby, from_clause)
