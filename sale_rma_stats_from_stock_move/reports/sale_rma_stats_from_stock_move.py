################################################################################
# For copyright and license notices, see __manifest__.py file in root directory
################################################################################
from odoo import api, fields, models, tools


class SaleRMAReportFromStockMove(models.Model):
    _name = 'sale.rma.stats.from_stock_move'
    _description = 'Sale RMA stats from stock move'
    _auto = False
    _rec_name = 'product_id'

    product_id = fields.Many2one(
        comodel_name='product.product',
        string='Product',
        readonly=True,
    )
    date = fields.Datetime(
        string='Date',
        readonly=True,
    )
    state = fields.Selection(
        selection=[
            ('draft', 'New'),
            ('cancel', 'Cancelled'),
            ('waiting', 'Waiting Another Move'),
            ('confirmed', 'Waiting Availability'),
            ('partially_available', 'Partially Available'),
            ('assigned', 'Available'),
            ('done', 'Done'),
        ],
        string='Status',
        default='draft',
        readonly=True,
    )
    categ_id = fields.Many2one(
        comodel_name='product.category',
        string='Product Category',
        readonly=True,
    )
    sales_count = fields.Float(
        string='Sale quantity',
        readonly=True,
    )
    order_id = fields.Many2one(
        comodel_name='sale.order',
        string='Sale order',
        readonly=True,
    )
    partner_id = fields.Many2one(
        comodel_name='res.partner',
        string='Partner',
        readonly=True,
    )
    returns = fields.Float(
        string='Return quantity',
        readonly=True,
    )
    losts = fields.Float(
        string='Lost quantity',
        readonly=True,
    )
    percentage = fields.Float(
        string='Percentage lost',
        digits=(16, 2),
    )

    def _select(self):
        return [
            'min(m.id) as id',
            'm.product_id as product_id',
            'm.date as date',
            'm.state as state',
            't.categ_id as categ_id',
            's.id as order_id',
            's.partner_id as partner_id',
            ('''
                sum(sl.product_uom_qty)
                *
                (CASE
                    WHEN s.is_return = False
                        THEN 1
                    ELSE 0
                END) as sales_count
            '''),
            ('''
                sum(m.product_uom_qty)
                *
                (CASE
                    WHEN m.is_return = True
                        THEN 1
                    ELSE 0
                END) as returns
            '''),
            ('''
                sum(m.product_uom_qty)
                *
                (CASE
                    WHEN loc_dst.usage = 'inventory' AND m.is_return = True
                        THEN 1
                    ELSE 0
                END) as losts
            '''),
            ('''
                (sum(m.product_uom_qty)
                *
                (CASE
                    WHEN loc_dst.usage = 'inventory' AND m.is_return = True
                    THEN 1
                    ELSE 0
                END))
                /
                p.sales_count * 100 as percentage
            '''),
        ]

    def _from(self):
        return [
            'stock_move as m',
            'left join product_product p on (m.product_id=p.id)',
            'left join product_template t on (p.product_tmpl_id=t.id)',
            'left join sale_order_line as sl on sl.id=m.sale_line_id',
            'left join sale_order s on (s.id=sl.order_id)',
            'left join stock_location as loc_dst on loc_dst.id=m.location_dest_id',
        ]

    def _where(self):
        return [
            'm.sale_line_id IS NOT NULL',
            'AND m.product_id IS NOT NULL',
        ]

    def _group_by(self):
        return [
            'm.id',
            'm.date',
            'm.state',
            'sl.product_uom_qty',
            'm.product_id',
            't.categ_id',
            'm.product_uom_qty',
            'p.id',
            's.id',
            's.partner_id',
            'loc_dst.usage',
        ]

    def _query(self):
        return 'SELECT %s FROM %s WHERE %s GROUP BY %s' % (
            ', '.join(self._select()),
            ' '.join(self._from()),
            ' '.join(self._where()),
            ', '.join(self._group_by()),
        )

    @api.model_cr
    def init(self):
        tools.drop_view_if_exists(self.env.cr, self._table)
        self.env.cr.execute(
            'CREATE or REPLACE VIEW %s as (%s)' % (self._table, self._query()))
