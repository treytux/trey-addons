###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import fields, models
from odoo.addons import decimal_precision as dp


class SaleReport(models.Model):
    _inherit = 'sale.report'

    standard_price = fields.Float(
        string='Cost',
        digits=dp.get_precision('Product Price'),
    )

    def _query(self, with_clause='', fields=None, groupby='', from_clause=''):
        if fields is None:
            fields = {}
        fields['standard_price'] = ', l.standard_price'
        groupby += ', l.standard_price'
        return super()._query(
            with_clause=with_clause, fields=fields, groupby=groupby,
            from_clause=from_clause)
