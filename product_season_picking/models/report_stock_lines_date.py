# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp import models, fields, tools


class ReportStockLinesDate(models.Model):
    _inherit = 'report.stock.lines.date'
    _auto = False

    season_id = fields.Many2one(
        comodel_name='product.season',
        string='Season')

    def init(self, cr):
        tools.sql.drop_view_if_exists(cr, 'report_stock_lines_date')
        cr.execute("""
            create or replace view report_stock_lines_date as (
                select
                    p.id as id,
                    p.id as product_id,
                    max(s.date) as date,
                    max(m.date) as move_date,
                    p.active as active,
                    pt.season_id as season_id
                from product_product p
                left join product_template as pt on p.product_tmpl_id=pt.id
                left join (
                    stock_inventory_line l
                    inner join stock_inventory s on (
                        l.inventory_id=s.id and s.state = 'done')
                            ) on (p.id=l.product_id)
                left join stock_move m on (m.product_id=p.id and
                    m.state = 'done')
                group by p.id, pt.season_id

            )""")
