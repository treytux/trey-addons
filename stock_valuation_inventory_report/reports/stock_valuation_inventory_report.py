# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp import tools, fields, models, api


class StockValuationInventoryReport(models.Model):
    _name = 'stock.valuation.inventory.report'
    _auto = False
    _order = 'product_id asc'

    company_id = fields.Many2one(
        comodel_name='res.company',
        string='Company')
    product_id = fields.Many2one(
        comodel_name='product.product',
        string='Product')
    location_id = fields.Many2one(
        comodel_name='stock.location',
        string='Location destination')
    product_categ_id = fields.Many2one(
        comodel_name='product.category',
        string='Product category')
    qty_available = fields.Float(
        string='Quantity on hand')
    uom_id = fields.Many2one(
        comodel_name='product.uom',
        string='Uom')
    price_cost = fields.Float(
        string='Cost price')
    total_price_cost = fields.Float(
        string='Total cost price')
    uom_po_id = fields.Many2one(
        comodel_name='product.uom',
        string='Purchase uom')

    def init(self, cr):
        tools.drop_view_if_exists(cr, 'stock_valuation_inventory_report')
        cr.execute("""
            CREATE OR REPLACE VIEW stock_valuation_inventory_report AS (
                SELECT
                    MIN(sq.id) AS id,
                    sq.product_id AS product_id,
                    pt.company_id AS company_id,
                    sq.location_id AS location_id,
                    pt.categ_id AS product_categ_id,
                    sum(sq.qty) AS qty_available,
                    pt.uom_id AS uom_id,
                    ip.value_float AS price_cost,
                    sum(sq.qty) / uom.factor * uom_po.factor * ip.value_float
                        AS total_price_cost,
                    pt.uom_po_id AS uom_po_id
                FROM stock_quant AS sq
                LEFT JOIN stock_location AS dest_location ON
                    sq.location_id = dest_location.id
                LEFT JOIN product_product AS pp on sq.product_id = pp.id
                LEFT JOIN product_template AS pt on pp.product_tmpl_id = pt.id
                LEFT JOIN product_uom AS uom on uom.id = pt.uom_id
                LEFT JOIN product_uom AS uom_po on uom_po.id = pt.uom_po_id
                LEFT JOIN ir_property ip ON (
                    ip.name='standard_price' AND
                    ip.res_id=CONCAT('product.template,',pt.id) AND
                    ip.company_id=sq.company_id)
                WHERE
                    pt.type != 'consu'
                    AND dest_location.usage IN ('internal', 'transit')
                GROUP BY
                    product_id, sq.location_id, pt.company_id,
                    product_categ_id, price_cost, pt.uom_id, pt.uom_po_id,
                    uom.factor, uom_po.factor
            )""")

    @api.model
    def search(self, args, offset=0, limit=None, order=None, count=False):
        for i, arg in enumerate(args):
            if 'product_categ_id' in arg:
                args[i] = ['product_categ_id', 'child_of', args[i][2]]
        return super(StockValuationInventoryReport, self).search(
            args, offset=offset, limit=limit, order=order, count=count)

    @api.model
    def read_group(self, domain, fields, groupby, **kwargs):
        if bool([gb for gb in groupby if 'product_categ_id' in gb]):
            for i, dom in enumerate(domain):
                if 'product_categ_id' in dom:
                    domain[i] = ['product_categ_id', 'child_of', domain[i][2]]
        return super(StockValuationInventoryReport, self).read_group(
            domain, fields, groupby, **kwargs)
