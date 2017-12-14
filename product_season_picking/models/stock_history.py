# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp import models, fields, tools


class StockHistoy(models.Model):
    _inherit = 'stock.history'

    season_id = fields.Many2one(
        comodel_name='product.season',
        string='Season',
        readonly=True)

    def init(self, cr):
        tools.drop_view_if_exists(cr, 'stock_history')
        cr.execute("""
            CREATE OR REPLACE VIEW stock_history AS (
              SELECT MIN(id) as id,
                move_id,
                location_id,
                company_id,
                product_id,
                season_id,
                product_categ_id,
                SUM(quantity) as quantity,
                date,
                COALESCE(SUM(price_unit_on_quant * quantity
                    ) / NULLIF(SUM(quantity), 0), 0) as price_unit_on_quant,
                source
                FROM
                ((SELECT
                    stock_move.id AS id,
                    stock_move.id AS move_id,
                    dest_location.id AS location_id,
                    dest_location.company_id AS company_id,
                    stock_move.product_id AS product_id,
                    product_template.categ_id AS product_categ_id,
                    product_template.season_id AS season_id,
                    quant.qty AS quantity,
                    stock_move.date AS date,
                    quant.cost as price_unit_on_quant,
                    stock_move.origin AS source
                FROM
                    stock_move
                JOIN
                    stock_quant_move_rel on
                        stock_quant_move_rel.move_id = stock_move.id
                JOIN
                    stock_quant as quant on
                        stock_quant_move_rel.quant_id = quant.id
                JOIN
                   stock_location dest_location ON
                        stock_move.location_dest_id = dest_location.id
                JOIN
                    stock_location source_location ON
                        stock_move.location_id = source_location.id
                JOIN
                    product_product ON
                        product_product.id = stock_move.product_id
                JOIN
                    product_template ON
                        product_template.id = product_product.product_tmpl_id
                WHERE quant.qty>0 AND stock_move.state = 'done' AND
                        dest_location.usage in ('internal', 'transit')
                  AND (
                    not (source_location.company_id is null and
                        dest_location.company_id is null) or
                    source_location.company_id != dest_location.company_id or
                    source_location.usage not in ('internal', 'transit'))
                ) UNION ALL
                (SELECT
                    (-1) * stock_move.id AS id,
                    stock_move.id AS move_id,
                    source_location.id AS location_id,
                    source_location.company_id AS company_id,
                    stock_move.product_id AS product_id,
                    product_template.categ_id AS product_categ_id,
                    product_template.season_id AS season_id,
                    - quant.qty AS quantity,
                    stock_move.date AS date,
                    quant.cost as price_unit_on_quant,
                    stock_move.origin AS source
                FROM
                    stock_move
                JOIN
                    stock_quant_move_rel on
                        stock_quant_move_rel.move_id = stock_move.id
                JOIN
                    stock_quant as quant on
                        stock_quant_move_rel.quant_id = quant.id
                JOIN
                    stock_location source_location ON
                        stock_move.location_id = source_location.id
                JOIN
                    stock_location dest_location ON
                        stock_move.location_dest_id = dest_location.id
                JOIN
                    product_product ON
                        product_product.id = stock_move.product_id
                JOIN
                    product_template ON
                        product_template.id = product_product.product_tmpl_id
                WHERE quant.qty>0 AND stock_move.state = 'done' AND
                        source_location.usage in ('internal', 'transit')
                 AND (
                    not (dest_location.company_id is null and
                        source_location.company_id is null) or
                    dest_location.company_id != source_location.company_id or
                    dest_location.usage not in ('internal', 'transit'))
                ))
                AS foo
                GROUP BY move_id, location_id, company_id, product_id,
                        product_categ_id, date, source, season_id
            )""")
