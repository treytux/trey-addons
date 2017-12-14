# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp import tools, fields, models


class StockValuationProductPrice(models.Model):
    _name = 'stock.valuation.product.price'
    _auto = False
    _order = 'date asc'

    move_id = fields.Many2one(
        comodel_name='stock.move',
        string='Stock Move',
        required=True)
    location_id = fields.Many2one(
        comodel_name='stock.location',
        string='Location Source',
        required=True)
    company_id = fields.Many2one(
        comodel_name='res.company',
        string='Company')
    product_id = fields.Many2one(
        comodel_name='product.product',
        string='Product',
        required=True)
    product_categ_id = fields.Many2one(
        comodel_name='product.category',
        string='Product Category',
        required=True)
    quantity = fields.Float(
        string='Product Quantity')
    standard_price = fields.Float(
        string='Price',
        readonly=True)
    standard_price_unit = fields.Float(
        string='Unit Price',
        readonly=True)
    date = fields.Datetime(
        string='Operation Date')
    origin = fields.Char(
        string='Origin')

    def init(self, cr):
        tools.drop_view_if_exists(cr, 'stock_valuation_product_price')
        cr.execute("""
            CREATE OR REPLACE VIEW stock_valuation_product_price AS (
                SELECT
                    MIN(id) AS id,
                    move_id,
                    location_id,
                    company_id,
                    product_id,
                    product_categ_id,
                    standard_price_unit,
                    standard_price,
                    SUM(quantity) AS quantity,
                    date,
                    origin
                FROM
                    ((SELECT
                        sq.id AS id,
                        sm.id AS move_id,
                        dest_location.id AS location_id,
                        dest_location.company_id AS company_id,
                        sq.product_id AS product_id,
                        pt.categ_id AS product_categ_id,
                        ip.value_float AS standard_price_unit,
                        SUM(ip.value_float*sq.cost/u.factor*u2.factor
                            )::decimal(16,2) AS standard_price,
                        sq.qty AS quantity,
                        sq.in_date AS date,
                        sm.origin AS origin
                    FROM stock_quant AS sq
                    LEFT JOIN stock_quant_move_rel AS sqm_rel ON
                        sq.id = sqm_rel.quant_id
                    LEFT JOIN stock_move AS sm ON sqm_rel.move_id = sm.id
                    JOIN stock_location AS dest_location ON
                        sm.location_dest_id = dest_location.id
                    JOIN stock_location AS source_location ON
                        sm.location_id = source_location.id
                    LEFT JOIN product_product AS pp ON
                        sq.product_id = pp.id
                    LEFT JOIN product_template AS pt ON
                        pp.product_tmpl_id = pt.id
                    LEFT JOIN ir_property AS ip ON (
                        ip.name='standard_price'
                        AND ip.res_id=CONCAT('product.template,',pt.id)
                        AND ip.company_id=sq.company_id)
                    LEFT JOIN product_uom AS u ON (u.id=sm.product_uom)
                    LEFT JOIN product_uom AS u2 ON (u2.id=pt.uom_id)
                    WHERE pt.type != 'consu' AND
                        sm.state = 'done' AND
                        dest_location.usage IN ('internal', 'transit')
                      AND (
                        NOT (source_location.company_id IS NULL AND
                            dest_location.company_id IS NULL) OR
                        source_location.company_id !=
                                dest_location.company_id OR
                        source_location.usage NOT IN ('internal', 'transit'))
                    GROUP BY sm.id, sq.id, pt.categ_id, pt.type,
                        standard_price_unit, dest_location.id)
                UNION ALL
                    (SELECT
                        (-1) * sq.id AS id,
                        sm.id AS move_id,
                        source_location.id AS location_id,
                        source_location.company_id AS company_id,
                        sq.product_id AS product_id,
                        pt.categ_id AS product_categ_id,
                        ip.value_float AS standard_price_unit,
                        SUM(-1*ip.value_float*sq.cost/u.factor*u2.factor
                            )::decimal(16,2) AS standard_price,
                        (-1) * sq.qty AS quantity,
                        sq.in_date AS date,
                        sm.origin AS origin
                    FROM stock_quant AS sq
                    LEFT JOIN stock_quant_move_rel AS sqm_rel ON
                        sq.id = sqm_rel.quant_id
                    LEFT JOIN stock_move AS sm ON sqm_rel.move_id = sm.id
                    JOIN stock_location AS source_location ON
                        sm.location_id = source_location.id
                    JOIN stock_location AS dest_location ON
                        sm.location_dest_id = dest_location.id
                    JOIN product_product AS pp ON pp.id = sq.product_id
                    JOIN product_template AS pt ON pt.id = pp.product_tmpl_id
                    LEFT JOIN ir_property AS ip ON (
                        ip.name='standard_price' AND
                        ip.res_id=CONCAT('product.template,',pt.id) AND
                        ip.company_id=sq.company_id)
                    LEFT JOIN product_uom AS u ON (u.id=sm.product_uom)
                    LEFT JOIN product_uom AS u2 ON (u2.id=pt.uom_id)
                    WHERE pt.type != 'consu' AND
                        sm.state = 'done' AND
                        source_location.usage in ('internal', 'transit') AND (
                            NOT (dest_location.company_id IS NULL AND
                                source_location.company_id IS NULL) OR
                            dest_location.company_id !=
                                    source_location.company_id
                            OR dest_location.usage NOT IN
                                ('internal', 'transit'))
                    GROUP BY sm.id, sq.id, pt.categ_id, pt.type,
                        standard_price_unit, dest_location.id,
                        source_location.id)
                ) AS foo
                GROUP BY move_id, location_id, company_id, product_id,
                    product_categ_id, standard_price, standard_price_unit,
                    date, origin
            )""")
