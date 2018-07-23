# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp import models, tools


class ReportStockLinesDate(models.Model):
    _inherit = 'report.stock.lines.date'

    def init(self, cr):
        tools.sql.drop_view_if_exists(cr, 'report_intrastat')
        cr.execute('''
            CREATE OR REPLACE VIEW report_intrastat AS (
                SELECT
                    TO_CHAR(account_period.date_start, 'YYYY') AS name,
                    TO_CHAR(account_period.date_start, 'MM') AS month,
                    MIN(inv_line.id) AS id,
                    intrastat.id AS intrastat_id,
                    upper(inv_country.code) AS code,
                    SUM(CASE WHEN inv_line.price_unit IS NOT NULL
                            THEN inv_line.price_unit * inv_line.quantity - (
                                inv_line.price_unit * inv_line.quantity *
                                inv_line.discount / 100)
                            ELSE 0
                        END) AS value,
                    SUM(
                        CASE WHEN uom.category_id != puom.category_id
                            THEN (pt.weight_net * inv_line.quantity)
                        ELSE (pt.weight_net * inv_line.quantity * uom.factor)
                        END) AS weight,
                    SUM(
                        CASE WHEN uom.category_id != puom.category_id
                            THEN inv_line.quantity
                        ELSE (inv_line.quantity * uom.factor) END
                    ) AS supply_units,
                    inv.currency_id AS currency_id,
                    inv.number AS ref,
                    CASE WHEN inv.type IN ('out_invoice','in_refund')
                        THEN 'export'
                        ELSE 'import'
                        END AS type
                FROM
                    account_invoice inv
                    LEFT JOIN account_invoice_line inv_line ON
                        inv_line.invoice_id=inv.id
                    LEFT JOIN (product_template pt
                        LEFT JOIN product_product pp ON (
                            pp.product_tmpl_id = pt.id))
                        ON (inv_line.product_id = pp.id)
                    LEFT JOIN product_uom uom ON uom.id=inv_line.uos_id
                    LEFT JOIN product_uom puom ON puom.id = pt.uom_id
                    LEFT JOIN report_intrastat_code intrastat ON
                        pt.intrastat_id = intrastat.id
                    LEFT JOIN (res_partner inv_address
                        LEFT JOIN res_country inv_country ON (
                            inv_country.id = inv_address.country_id))
                        ON (inv_address.id = inv.partner_id)
                    LEFT JOIN account_period ON account_period.id=inv.period_id
                WHERE
                    inv.state IN ('open','paid')
                    and inv_line.product_id IS NOT NULL
                    and inv_country.intrastat=true
                GROUP BY
                    TO_CHAR(account_period.date_start, 'YYYY'),
                    TO_CHAR(account_period.date_start, 'MM'),
                    intrastat.id, inv.type, pt.intrastat_id, inv_country.code,
                    inv.number, inv.currency_id
            )''')
