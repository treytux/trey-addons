###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import api, fields, models, tools


class StockRotationReport(models.Model):
    _name = 'stock.rotation.report'
    _description = 'Product stock rotation report'
    _auto = False
    _order = 'date_day asc'

    date_day = fields.Date(
        string='Operation Date',
        readonly=True,
    )
    company_id = fields.Many2one(
        comodel_name='res.company',
        string='Company',
        readonly=True,
    )
    warehouse_id = fields.Many2one(
        comodel_name='stock.warehouse',
        string='Warehouse',
        readonly=True,
    )
    product_id = fields.Many2one(
        comodel_name='product.product',
        string='Product',
        readonly=True,
    )
    product_mrp = fields.Boolean(
        string='Product MRP',
        readonly=True,
    )
    category_id = fields.Many2one(
        comodel_name='product.category',
        string='Product Category',
        readonly=True,
    )
    year = fields.Integer(
        string='Year',
        readonly=True,
    )
    month = fields.Integer(
        string='Month',
        readonly=True,
    )
    qty_stock_init = fields.Float(
        string='Stock init',
        group_operator='sum',
        readonly=True,
    )
    qty_stock_end = fields.Float(
        string='Stock end',
        group_operator='sum',
        readonly=True,
    )
    qty_move = fields.Float(
        string='Move Quantity',
        group_operator='sum',
        readonly=True,
    )
    qty_purchase = fields.Float(
        string='Purchase Quantity',
        group_operator='sum',
        readonly=True,
    )
    qty_sale = fields.Float(
        string='Sale Quantity',
        group_operator='sum',
        readonly=True,
    )
    qty_inventory = fields.Float(
        string='Inventory Quantity',
        group_operator='sum',
        readonly=True,
    )
    qty_production = fields.Float(
        string='Production Quantity',
        group_operator='sum',
        readonly=True,
    )
    standard_price = fields.Float(
        string='AVG Price Unit',
        group_operator='avg',
        readonly=True,
    )
    rate_qty = fields.Float(
        string='Rate qty',
        group_operator='avg',
        readonly=True,
    )
    rate_price = fields.Float(
        string='Rate price',
        group_operator='avg',
        readonly=True,
    )
    rate_percentage = fields.Float(
        string='Rate %',
        group_operator='avg',
    )
    rate_qty_week = fields.Float(
        string='Rate quantity week',
        group_operator='avg',
        readonly=True,
    )
    rate_price_week = fields.Float(
        string='Rate price week',
        group_operator='avg',
        readonly=True,
    )
    rate_percentage_week = fields.Float(
        string='Rate % week',
        group_operator='avg',
        readonly=True,
    )
    rate_qty_month = fields.Float(
        string='Rate quantity month',
        group_operator='avg',
        readonly=True,
    )
    rate_price_month = fields.Float(
        string='Rate price monthr',
        group_operator='avg',
        readonly=True,
    )
    rate_percentage_month = fields.Float(
        string='Rate % month',
        group_operator='avg',
        readonly=True,
    )
    rate_qty_year = fields.Float(
        string='Rate quantity year',
        group_operator='avg',
        readonly=True,
    )
    rate_price_year = fields.Float(
        string='Rate price year',
        group_operator='avg',
        readonly=True,
    )
    rate_percentage_year = fields.Float(
        string='Rate % year',
        group_operator='avg',
        readonly=True,
    )

    def _select(self):
        select_str = '''
            SELECT
                sr.id AS id,
                sr.date_day,
                sr.company_id,
                sr.warehouse_id,
                sr.category_id,
                sr.product_id,
                sr.product_mrp,
                sr.year,
                sr.month,
                sr.week,
                sr.day,
                SUM(sr.qty_stock_init) AS qty_stock_init,
                SUM(sr.qty_stock_end) as qty_stock_end,
                SUM(sr.qty_move) AS qty_move,
                SUM(sr.qty_purchase) AS qty_purchase,
                SUM(sr.qty_sale) AS qty_sale,
                SUM(sr.qty_inventory) AS qty_inventory,
                SUM(sr.qty_production) AS qty_production,
                AVG(sr.standard_price) AS standard_price,
                AVG(sr.rate_qty) AS rate_qty,
                AVG(sr.rate_price) AS rate_price,
                AVG(sr.rate_percentage) AS rate_percentage,
                AVG(sr.rate_qty_week) AS rate_qty_week,
                AVG(sr.rate_price_week) AS rate_price_week,
                AVG(sr.rate_percentage_week) AS rate_percentage_week,
                AVG(sr.rate_qty_month) AS rate_qty_month,
                AVG(sr.rate_price_month) AS rate_price_month,
                AVG(sr.rate_percentage_month) AS rate_percentage_month,
                AVG(sr.rate_qty_year) AS rate_qty_year,
                AVG(sr.rate_price_year) AS rate_price_year,
                AVG(sr.rate_percentage_year) AS rate_percentage_year
        '''
        return select_str

    def _from(self):
        from_str = '''
            FROM
                product_product_stock_rotation AS sr
                LEFT JOIN product_product AS pp ON
                    sr.product_id = pp.id
                LEFT JOIN product_template AS pt ON
                    pp.product_tmpl_id = pt.id
        '''
        return from_str

    def _group_by(self):
        group_by_str = '''
            GROUP BY
                sr.id,
                sr.date_day,
                sr.company_id,
                sr.warehouse_id,
                sr.category_id,
                sr.product_id,
                sr.product_mrp,
                sr.year,
                sr.month,
                sr.week,
                sr.day
        '''
        return group_by_str

    @api.model_cr
    def init(self):
        tools.drop_view_if_exists(self._cr, self._table)
        self._cr.execute('CREATE or REPLACE VIEW %s as (%s %s %s)' % (
            self._table, self._select(), self._from(), self._group_by()
        ))
