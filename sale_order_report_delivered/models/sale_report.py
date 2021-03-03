###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import fields, models


class SaleReport(models.Model):
    _inherit = 'sale.report'

    price_delivered = fields.Float(
        string='Untaxed total delivered',
        readonly=True,
    )

    def _query(self, with_clause='', fields=None, groupby='', from_clause=''):
        if fields is None:
            fields = {}
        fields['price_delivered'] = '''
            , SUM(
                l.price_unit * (l.qty_delivered / u.factor * u2.factor)
                - (
                    l.price_unit * l.qty_delivered * l.discount / 100.0
                    / CASE COALESCE(s.currency_rate, 0)
                    WHEN 0 THEN 1.0 ELSE s.currency_rate END
                )
            ) as price_delivered
        '''
        return super(). _query(
            with_clause=with_clause,
            fields=fields,
            groupby=groupby,
            from_clause=from_clause)
