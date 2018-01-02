# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp import tools, fields, models


class StockValuationProductPrice(models.Model):
    _name = 'stock.valuation.product.price'
    _auto = False
    _order = 'product_id asc'

    quant_id = fields.Many2one(
        comodel_name='stock.quant',
        string='Stock Quant')
    location_id = fields.Many2one(
        comodel_name='stock.location',
        string='Location Source')
    company_id = fields.Many2one(
        comodel_name='res.company',
        string='Company')
    product_id = fields.Many2one(
        comodel_name='product.product',
        string='Product')
    product_categ_id = fields.Many2one(
        comodel_name='product.category',
        string='Product Category')
    quantity = fields.Float(
        string='Product Quantity')
    price_unit = fields.Float(
        string='Quant Price Unit')
    price_unit_product = fields.Float(
        string='Product Price Unit ')
    price_total = fields.Float(
        string='Total')
    date = fields.Datetime(
        string='Operation Date')

    def init(self, cr):
        tools.drop_view_if_exists(cr, 'stock_valuation_product_price')
        cr.execute("""
            CREATE OR REPLACE VIEW stock_valuation_product_price AS (
                SELECT
                    sq.id AS id,
                    sq.id AS quant_id,
                    sq.company_id AS company_id,
                    sq.location_id AS location_id,
                    sq.product_id AS product_id,
                    pt.categ_id AS product_categ_id,
                    CASE
                        WHEN sq.cost != 0
                        THEN (sq.cost*sq.qty)::decimal(16,2)
                        ELSE (ip.value_float*sq.qty)::decimal(16,2)
                    END AS price_total,
                    sq.cost AS price_unit,
                    ip.value_float AS price_unit_product,
                    sq.qty AS quantity,
                    sq.in_date AS date
                FROM stock_quant AS sq
                LEFT JOIN stock_location AS dest_location ON
                    sq.location_id = dest_location.id
                LEFT JOIN product_product AS pp ON
                    sq.product_id = pp.id
                LEFT JOIN product_template AS pt ON
                    pp.product_tmpl_id = pt.id
                LEFT JOIN ir_property AS ip ON (
                    ip.name='standard_price'
                    AND ip.res_id=CONCAT('product.template,',pt.id)
                    AND ip.company_id=sq.company_id)
                WHERE
                    pt.type != 'consu'
                    AND dest_location.usage IN ('internal', 'transit')
            )""")
