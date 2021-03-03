# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp import tools, fields, models


class StockValuationProductPrice(models.Model):
    _inherit = 'stock.valuation.product.price'

    season_id = fields.Many2one(
        comodel_name='product.season',
        string='Season',
        readonly=True,
    )

    def init(self, cr):
        tools.drop_view_if_exists(cr, 'stock_valuation_product_price')
        cr.execute('''
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
                    sq.in_date AS date,
                    pt.season_id AS season_id
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
            )
        ''')
