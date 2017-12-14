# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp.osv import osv
from openerp import tools


class report_account_analytic_line_to_invoice(osv.osv):
    _inherit = "report.account.analytic.line.to.invoice"

    def init(self, cr):
        tools.drop_view_if_exists(
            cr, 'report_account_analytic_line_to_invoice')
        cr.execute("""
            CREATE OR REPLACE VIEW report_account_analytic_line_to_invoice AS (
                SELECT
                    DISTINCT(to_char(l.date,'MM')) as month,
                    to_char(l.date, 'YYYY') as name,
                    MIN(l.id) AS id,
                    l.product_id,
                    l.account_id,
                    SUM(l.amount) AS amount,
                    SUM(l.unit_amount*ip.value_float) AS sale_price,
                    SUM(l.unit_amount) AS unit_amount,
                    l.product_uom_id
                FROM
                    account_analytic_line l
                left join
                    product_product p on (l.product_id=p.id)
                left join
                    product_template t on (p.product_tmpl_id=t.id)
                left join
                ir_property ip on (
                ip.company_id=l.company_id AND res_id='product.template,
                ' || t.id)

                WHERE
                    (invoice_id IS NULL) and (to_invoice IS NOT NULL)
                GROUP BY
                    to_char(l.date, 'YYYY'), to_char(l.date,'MM'),
                    product_id, product_uom_id, account_id
            )
        """)
