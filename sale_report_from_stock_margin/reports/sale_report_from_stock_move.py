###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import fields, models


class SaleReportFromStockMove(models.Model):
    _inherit = 'sale.report.from_stock_move'

    margin = fields.Float(
        string='Margin (amount)',
    )
    purchase_price = fields.Float(
        string='Purchase price',
    )

    def _select(self):
        select = super()._select()
        operation_type = '''
            (
                CASE
                    WHEN src.usage = 'internal' AND dst.usage = 'customer'
                        THEN 1
                    WHEN src.usage = 'internal' AND dst.usage = 'internal'
                        THEN 0
                    WHEN src.usage = 'customer' AND dst.usage = 'internal'
                        THEN -1
                    ELSE 0
                END
            )
        '''
        operation_total = f'''
            (
                sum(sl.price_reduce * m.product_uom_qty)
                *
                {operation_type}
            )
        '''
        select += [
            '''
                (
                    CASE
                        WHEN sl.purchase_price != 0
                        THEN sl.purchase_price
                        ELSE ip.value_float
                    END
                ) as purchase_price
            ''',
            f'''
                (
                    CASE
                        WHEN sl.purchase_price != 0
                        THEN ({operation_total} - (
                                (sl.purchase_price * m.product_uom_qty)
                                * {operation_type})
                        )
                        ELSE ({operation_total} -
                                (ip.value_float * m.product_uom_qty)
                                * {operation_type})
                    END
                ) as margin
            ''',
        ]
        return select

    def _from(self):
        res = super()._from()
        res += [
            (
                'left join ir_property ip on (ip.name=\'standard_price\' AND '
                'ip.res_id=CONCAT(\'product.product,\',p.id) AND '
                'ip.company_id=m.company_id)'
            ),
        ]
        return res

    def _group_by(self):
        group = super()._group_by()
        group += [
            'sl.margin',
            'sl.purchase_price',
            'ip.value_float',
            'sl.price_subtotal',
        ]
        return group
