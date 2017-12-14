# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp import tools, fields, models


class StockRotationReport(models.Model):
    _name = 'stock.rotation.report'
    _auto = False
    _order = 'date asc'

    date = fields.Datetime(
        string='Operation Date')
    product_id = fields.Many2one(
        comodel_name='product.product',
        string='Product')
    product_categ_id = fields.Many2one(
        comodel_name='product.category',
        string='Product Category')
    location_id = fields.Many2one(
        comodel_name='stock.location',
        string='Location Source')
    location_dest_id = fields.Many2one(
        comodel_name='stock.location',
        string='Location Destination')
    location_general_id = fields.Many2one(
        comodel_name='stock.location',
        string='Location')
    warehouse_id = fields.Many2one(
        comodel_name='stock.warehouse',
        string='Warehouse')
    company_id = fields.Many2one(
        comodel_name='res.company',
        string='Company')
    quantity = fields.Float(
        string='Product Quantity')

    def init(self, cr):
        tools.drop_view_if_exists(cr, 'stock_rotation_report')
        cr.execute("""
            CREATE OR REPLACE VIEW stock_rotation_report AS (
                SELECT
                    MIN(id) AS id,
                    date,
                    product_id,
                    product_categ_id,
                    location_id,
                    location_dest_id,
                    warehouse_id,
                    company_id,
                    SUM(quantity) AS quantity,
                    location_general_id
                FROM((
                    SELECT
                        sm.id AS id,
                        sm.date AS date,
                        pp.id AS product_id,
                        pt.categ_id AS product_categ_id,
                        sm.location_id AS location_id,
                        sm.location_dest_id AS location_dest_id,
                        sm.warehouse_id AS warehouse_id,
                        sm.company_id AS company_id,
                        sm.product_uom_qty AS quantity,
                        sm.location_dest_id AS location_general_id
                    FROM stock_move AS sm
                        LEFT JOIN product_product AS pp ON
                            sm.product_id = pp.id
                        LEFT JOIN product_template AS pt ON
                            pp.product_tmpl_id = pt.id
                        LEFT JOIN stock_location AS src_loc ON
                            sm.location_id = src_loc.id
                        LEFT JOIN stock_location AS dst_loc ON
                            sm.location_dest_id = dst_loc.id
                    WHERE
                        pt.type != 'consu' AND
                        sm.state = 'done' AND
                        dst_loc.usage in (
                            'customer', 'production', 'inventory') AND
                        (src_loc.company_id IS NULL OR
                         dst_loc.company_id IS NULL OR
                         src_loc.company_id = dst_loc.company_id)
                    GROUP BY
                        sm.id,
                        sm.date,
                        pp.id,
                        pt.categ_id,
                        sm.location_id,
                        sm.location_dest_id,
                        sm.warehouse_id,
                        sm.company_id)
                UNION ALL(
                    SELECT
                        (-1) * sm.id AS id,
                        sm.date AS date,
                        pp.id AS product_id,
                        pt.categ_id AS product_categ_id,
                        sm.location_id AS location_id,
                        sm.location_dest_id AS location_dest_id,
                        sm.warehouse_id AS warehouse_id,
                        sm.company_id AS company_id,
                        (-1) * sm.product_uom_qty AS quantity,
                        sm.location_id AS location_general_id
                    FROM stock_move AS sm
                        LEFT JOIN product_product AS pp ON
                            sm.product_id = pp.id
                        LEFT JOIN product_template AS pt ON
                            pp.product_tmpl_id = pt.id
                        LEFT JOIN stock_location AS src_loc ON
                            sm.location_id = src_loc.id
                        LEFT JOIN stock_location AS dst_loc ON
                            sm.location_dest_id = dst_loc.id
                    WHERE
                        pt.type != 'consu' AND
                        sm.state = 'done' AND
                        src_loc.usage in (
                            'customer', 'production', 'inventory') AND
                        (src_loc.company_id IS NULL OR
                         dst_loc.company_id IS NULL OR
                         src_loc.company_id = dst_loc.company_id)
                    GROUP BY
                        sm.id,
                        sm.date,
                        pp.id,
                        pt.categ_id,
                        sm.location_id,
                        sm.location_dest_id,
                        sm.warehouse_id,
                        sm.company_id)
                ) AS foo
                GROUP BY
                    date,
                    product_id,
                    product_categ_id,
                    location_id,
                    location_dest_id,
                    warehouse_id,
                    company_id,
                    location_general_id

            )""")
