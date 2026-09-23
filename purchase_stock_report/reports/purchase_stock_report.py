# -*- coding: utf-8 -*-
###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from openerp import tools, models, fields


class PurchaseStockReport(models.Model):
    _name = 'purchase.stock.report'
    _description = 'Purchase stock report'
    _auto = False

    date_order = fields.Datetime(
        string='Date order',
        help='Date on which this document has been created',
        readonly=True,
    )
    state = fields.Selection(
        [
            ('draft', 'Draft PO'),
            ('sent', 'RFQ'),
            ('bid', 'Bid Received'),
            ('confirmed', 'Waiting Approval'),
            ('approved', 'Purchase Confirmed'),
            ('except_picking', 'Shipping Exception'),
            ('except_invoice', 'Invoice Exception'),
            ('done', 'Done'),
            ('cancel', 'Cancelled'),
        ],
        string='Purchase state',
        readonly=True,
    )
    product_id = fields.Many2one(
        string='Product',
        comodel_name='product.product',
        readonly=True,
    )
    company_id = fields.Many2one(
        string='Company',
        comodel_name='res.company',
        readonly=True,
    )
    purchase_id = fields.Many2one(
        string='Purchase order',
        comodel_name='purchase.order',
    )
    picking_id = fields.Many2one(
        comodel_name='stock.picking',
        string='Stock picking',
        readonly=True,
    )
    partner_id = fields.Many2one(
        comodel_name='res.partner',
        string='Partner',
        readonly=True,
    )
    qty_ordered = fields.Float(
        string='Qty ordered',
        readonly=True,
    )
    qty_move = fields.Float(
        string='Qty move',
        readonly=True,
    )
    qty_received = fields.Float(
        string='Qty received',
        readonly=True,
    )
    price_unit = fields.Float(
        string='Price unit',
        readonly=True,
    )
    discount = fields.Float(
        string='Discount (%)',
        readonly=True,
    )
    price_subtotal_ordered = fields.Float(
        string='Price subtotal ordered',
        readonly=True,
    )
    price_subtotal_received = fields.Float(
        string='Price subtotal received',
        readonly=True,
    )
    date_expected = fields.Datetime(
        string='Date expected',
        readonly=True,
    )
    date_done = fields.Datetime(
        string='Date done',
        readonly=True,
    )
    state_move = fields.Selection(
        [
            ('draft', 'New'),
            ('cancel', 'Cancelled'),
            ('waiting', 'Waiting Another Move'),
            ('confirmed', 'Waiting Availability'),
            ('assigned', 'Available'),
            ('done', 'Done'),
        ],
        string='Status move',
        readonly=True,
    )
    _order = 'date_order desc'

    def init(self, cr):
        tools.sql.drop_view_if_exists(cr, 'purchase_stock_report')
        cr.execute('''
            CREATE or REPLACE view purchase_stock_report AS (
                {select}
                {from_join}
                {where}
                {group_by}
            );
        '''.format(select=self._select(),
                   from_join=self._from_join(),
                   where=self._where(),
                   group_by=self._group_by(),
                   ))

    def _select(self):
        return '''
            SELECT
                MIN(id) AS id,
                purchase_id,
                date_order,
                picking_id,
                qty_ordered,
                qty_move,
                qty_received,
                price_unit,
                discount,
                price_subtotal_ordered,
                price_subtotal_received,
                date_expected,
                date_done,
                state,
                product_id,
                partner_id,
                state_move,
                company_id
        '''

    def _from_join(self):
        return '''
            FROM ((
                SELECT
                    move.id AS id,
                    l.order_id AS purchase_id,
                    po.date_order AS date_order,
                    move.picking_id AS picking_id,
                    l.product_qty AS qty_ordered,
                    move.product_uom_qty AS qty_move,
                    CASE WHEN move.state = 'done'
                        THEN move.product_uom_qty
                        ELSE 0
                        END AS qty_received,
                    l.price_unit AS price_unit,
                    l.discount AS discount,
                    l.price_unit * l.product_qty * (
                        1 - (l.discount / 100)) AS price_subtotal_ordered,
                    CASE WHEN move.state = 'done'
                        THEN l.price_unit * move.product_uom_qty * (
                            1 - (l.discount / 100))
                        ELSE 0
                        END AS price_subtotal_received,
                    move.date_expected AS date_expected,
                    CASE WHEN move.state = 'done'
                        THEN move.date
                        ELSE null
                        END AS date_done,
                    po.state AS state,
                    l.product_id AS product_id,
                    po.partner_id AS partner_id,
                    move.state AS state_move,
                    move.company_id AS company_id
                FROM stock_move move
                LEFT JOIN stock_location loc ON (move.location_id=loc.id)
                LEFT JOIN purchase_order_line l ON (move.purchase_line_id=l.id)
                LEFT JOIN purchase_order po ON (l.order_id=po.id)
                WHERE loc.usage = 'supplier'
                )
                UNION ALL(
                SELECT
                    -move.id AS id,
                    l.order_id AS purchase_id,
                    po.date_order AS date_order,
                    move.picking_id AS picking_id,
                    l.product_qty AS qty_ordered,
                    -move.product_uom_qty AS qty_move,
                    CASE WHEN move.state = 'done'
                        THEN -move.product_uom_qty
                        ELSE 0
                        END AS qty_received,
                    l.price_unit AS price_unit,
                    l.discount AS discount,
                    l.price_unit * l.product_qty * (
                        1 - (l.discount / 100)) AS price_subtotal_ordered,
                    CASE WHEN move.state = 'done'
                        THEN l.price_unit * -1 * move.product_uom_qty * (
                            1 - (l.discount / 100))
                        ELSE 0
                        END AS price_subtotal_received,
                    move.date_expected AS date_expected,
                    CASE WHEN move.state = 'done'
                        THEN move.date
                        ELSE null
                        END AS date_done,
                    po.state AS state,
                    l.product_id AS product_id,
                    po.partner_id AS partner_id,
                    move.state AS state_move,
                    move.company_id AS company_id
                FROM stock_move move
                    LEFT JOIN stock_location loc_dst ON (
                        move.location_dest_id=loc_dst.id)
                    LEFT JOIN purchase_order_line l ON (
                        move.purchase_line_id=l.id)
                    LEFT JOIN purchase_order po ON (l.order_id=po.id)
                WHERE loc_dst.usage = 'supplier'
                )
            ) AS foo
        '''

    def _where(self):
        return ''

    def _group_by(self):
        return '''
            GROUP BY
                purchase_id,
                picking_id,
                date_order,
                picking_id,
                qty_ordered,
                qty_move,
                qty_received,
                price_unit,
                discount,
                price_subtotal_ordered,
                price_subtotal_received,
                date_expected,
                date_done,
                state,
                product_id,
                partner_id,
                state_move,
                company_id
        '''
