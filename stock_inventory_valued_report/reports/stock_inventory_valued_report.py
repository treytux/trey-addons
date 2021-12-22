###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import api, fields, models, tools


class StockInventoryValuedReport(models.Model):
    _name = 'stock.inventory_valued.report'
    _description = 'Stock inventory valued report'
    _auto = False
    _rec_name = 'date'
    _order = 'date asc'

    company_id = fields.Many2one(
        comodel_name='res.company',
        string='Company',
        readonly=True,
    )
    date = fields.Date(
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
    value = fields.Float(
        string='Value',
        readonly=True,
    )
    remaining_value = fields.Float(
        string='Remaining value',
        readonly=True,
    )
    remaining_qty = fields.Float(
        string='Remaining qty',
        readonly=True,
    )
    partner_id = fields.Many2one(
        comodel_name='res.partner',
        string='Partner',
        readonly=True,
    )
    is_customer = fields.Integer(
        string='Is customer',
    )
    is_supplier = fields.Integer(
        string='Is supplier',
    )
    picking_id = fields.Many2one(
        comodel_name='stock.picking',
        string='Picking',
        readonly=True,
    )

    def _select(self):
        return [
            'm.id as id',
            'm.company_id as company_id',
            'm.date as date',
            'm.product_id as product_id',
            't.categ_id as categ_id',
            'm.location_id as location_id',
            'm.location_dest_id as location_dest_id',
            '''
            (m.product_uom_qty / u.factor * u2.factor) * (
                CASE
                    WHEN src.usage = 'internal' AND dst.usage = 'supplier'
                        THEN -1
                    WHEN src.usage = 'supplier' AND dst.usage = 'internal'
                        THEN 1
                    WHEN src.usage = 'internal' AND dst.usage = 'internal'
                        THEN 0
                    WHEN src.usage = 'internal' AND dst.usage = 'customer'
                        THEN -1
                    WHEN src.usage = 'customer' AND dst.usage = 'internal'
                        THEN 1
                    ELSE 0
                END
            ) as product_uom_qty
            ''',
            '''
            (m.value / (
                CASE
                    WHEN (m.product_uom_qty / u.factor * u2.factor) = 0 THEN 1
                    ELSE (m.product_uom_qty / u.factor * u2.factor)
                END
            )) as price_unit
            ''',
            'm.value as value',
            'm.remaining_value as remaining_value',
            'm.remaining_qty as remaining_qty',
            'm.product_uom as product_uom',
            'm.state as state',
            'm.picking_id as picking_id',
            'pick.partner_id as partner_id',
            'CASE WHEN partner.customer = TRUE THEN 1 END AS is_customer',
            'CASE WHEN partner.supplier = TRUE THEN 1 END AS is_supplier',
        ]

    def _from(self):
        return [
            'stock_move m',
            'left join stock_location src on (src.id=m.location_id)',
            'left join stock_location dst on (dst.id=m.location_dest_id)',
            'left join product_product p on (m.product_id=p.id)',
            'left join product_template t on (p.product_tmpl_id=t.id)',
            'left join uom_uom u on (u.id=m.product_uom)',
            'left join uom_uom u2 on (u2.id=t.uom_id)',
            'left join stock_picking pick on (pick.id=m.picking_id)',
            'left join res_partner partner on (partner.id=pick.partner_id)',
        ]

    def _where(self):
        return [
            'm.product_id IS NOT NULL'
        ]

    def _group_by(self):
        return [
            'm.id',
            'm.company_id',
            'm.date',
            'm.product_id',
            't.categ_id',
            'm.location_id',
            'm.location_dest_id',
            'm.product_uom_qty',
            'u.factor',
            'u2.factor',
            'm.price_unit',
            'm.value',
            'm.remaining_value',
            'm.remaining_qty',
            'm.product_uom',
            'm.state',
            'm.picking_id',
            'pick.partner_id',
            'partner.customer',
            'partner.supplier',
            'dst.usage',
            'src.usage',
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
