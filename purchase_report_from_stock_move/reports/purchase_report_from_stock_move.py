###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import api, fields, models, tools


class PurchaseReportFromStockMove(models.Model):
    _name = 'purchase.report.from_stock_move'
    _description = 'Purchase report from stock move'
    _auto = False
    _rec_name = 'date'
    _order = 'date asc'

    company_id = fields.Many2one(
        comodel_name='res.company',
        string='Company',
        readonly=True,
    )
    date = fields.Datetime(
        string='Date',
        readonly=True,
    )
    product_id = fields.Many2one(
        comodel_name='product.product',
        string='Product',
        readonly=True,
    )
    categ_id = fields.Many2one(
        comodel_name='product.category',
        string='Product Category',
        readonly=True,
    )
    product_uom_qty = fields.Float(
        string='Quantity',
        readonly=True,
    )
    product_uom = fields.Many2one(
        comodel_name='uom.uom',
        string='Unit of Measure',
        readonly=True,
    )
    location_id = fields.Many2one(
        comodel_name='stock.location',
        string='Source Location',
        readonly=True,
    )
    location_dest_id = fields.Many2one(
        comodel_name='stock.location',
        string='Destination Location',
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
    price_unit = fields.Float(
        string='Price Unit',
        readonly=True,
    )
    move_total = fields.Float(
        string='Price Move',
        readonly=True,
    )
    operation_total = fields.Float(
        string='Price Operation',
        readonly=True,
    )
    order_id = fields.Many2one(
        comodel_name='purchase.order',
        string='Purchase order',
        readonly=True,
    )
    partner_id = fields.Many2one(
        comodel_name='res.partner',
        string='Partner',
        readonly=True,
    )
    picking_type_id = fields.Many2one(
        comodel_name='stock.picking.type',
        string='Operation type',
        readonly=True,
    )
    state_id = fields.Many2one(
        comodel_name='res.country.state',
        string='Partner State',
        readonly=True,
    )
    picking_id = fields.Many2one(
        comodel_name='stock.picking',
        string='Picking',
        readonly=True,
    )

    def _select(self):
        return [
            'min(m.id) as id',
            'm.company_id as company_id',
            'm.date as date',
            'm.product_id as product_id',
            't.categ_id as categ_id',
            'sum(m.product_uom_qty / u.factor * u2.factor) as product_uom_qty',
            'm.product_uom as product_uom',
            'm.location_id as location_id',
            'm.location_dest_id as location_dest_id',
            'm.state as state',
            'pol.price_unit as price_unit',
            'sum(pol.price_unit * m.product_uom_qty) as move_total',
            ('''
                sum(pol.price_unit * m.product_uom_qty)
                *
                (CASE
                    WHEN src.usage = 'internal' AND dst.usage = 'supplier'
                        THEN -1
                    WHEN src.usage = 'internal' AND dst.usage = 'internal'
                        THEN 0
                    WHEN src.usage = 'supplier' AND dst.usage = 'internal'
                        THEN 1
                    ELSE 0
                END) as operation_total
            '''),
            'po.id as order_id',
            'po.picking_type_id as picking_type_id',
            'po.partner_id as partner_id',
            'partner.state_id as state_id',
            'm.picking_id as picking_id',
        ]

    def _from(self):
        return [
            'stock_move m',
            'left join stock_location src on (src.id=m.location_id)',
            'left join stock_location dst on (dst.id=m.location_dest_id)',
            'left join product_product p on (m.product_id=p.id)',
            'left join product_template t on (p.product_tmpl_id=t.id)',
            'left join uom_uom u on (u.id=m.product_uom)',
            'left join uom_uom u2 on (u2.id=m.product_uom)',
            'left join purchase_order_line pol on (pol.id=m.purchase_line_id)',
            'left join purchase_order po on (po.id=pol.order_id)',
            'left join res_partner partner on (partner.id=pol.partner_id)',
        ]

    def _where(self):
        return [
            'm.purchase_line_id IS NOT NULL',
            'AND m.product_id IS NOT NULL'
        ]

    def _group_by(self):
        return [
            'm.id',
            'm.company_id',
            'm.date',
            'm.product_id',
            't.categ_id',
            'm.product_uom_qty',
            'm.product_uom',
            'm.location_id',
            'm.location_dest_id',
            'm.state',
            'pol.price_unit',
            'po.id',
            'po.picking_type_id',
            'po.partner_id',
            'partner.state_id',
            'src.usage',
            'dst.usage',
            'm.picking_id',
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
