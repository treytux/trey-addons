# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp import models, tools


class PurchaseReport(models.Model):
    _inherit = 'purchase.report'
    _auto = False

    def _select(self):
        select_str = '''
            SELECT
                min(l.id) AS id,
                s.date_order AS date,
                l.state,
                s.date_approve,
                s.minimum_planned_date AS expected_date,
                s.dest_address_id,
                s.pricelist_id,
                s.validator,
                spt.warehouse_id AS picking_type_id,
                s.partner_id AS partner_id,
                s.create_uid AS user_id,
                s.company_id AS company_id,
                l.product_id,
                t.categ_id AS category_id,
                t.uom_id AS product_uom,
                s.location_id AS location_id,
                sum(l.product_qty / u.factor * u2.factor) AS quantity,
                extract(epoch from age(s.date_approve, s.date_order)) / (
                    24 * 60 * 60)::decimal(16, 2) AS delay,
                extract(epoch from age(l.date_planned, s.date_order)) / (
                    24 * 60 * 60)::decimal(16, 2) AS delay_pass,
                count(*) AS nbr,
                sum(l.price_unit / cr.rate * l.product_qty)::decimal(
                    16, 2) AS price_total,
                avg(100.0 * (l.price_unit / cr.rate * l.product_qty) / NULLIF(
                    ip.value_float * l.product_qty / u.factor * u2.factor, 0.0)
                    )::decimal(16, 2) AS negociation,
                sum(
                    ip.value_float * l.product_qty / u.factor * u2.factor
                )::decimal(16, 2) AS price_standard,
                (sum(l.product_qty * l.price_unit / cr.rate) / NULLIF(sum(
                    l.product_qty / u.factor * u2.factor), 0.0))::decimal(
                    16, 2) AS price_average
        '''
        return select_str

    def _from(self):
        from_str = '''
            FROM purchase_order_line l
                JOIN purchase_order s ON (l.order_id=s.id)
                LEFT JOIN product_product p ON (l.product_id=p.id)
                LEFT JOIN product_template t ON (p.product_tmpl_id=t.id)
                LEFT JOIN ir_property ip ON (ip.name='standard_price'
                    AND ip.res_id=CONCAT('product.template,',t.id)
                    AND ip.company_id=s.company_id)
                LEFT JOIN product_uom u ON (u.id=l.product_uom)
                LEFT JOIN product_uom u2 ON (u2.id=t.uom_id)
                LEFT JOIN stock_picking_type spt ON (spt.id=s.picking_type_id)
                JOIN currency_rate cr ON (cr.currency_id = s.currency_id AND
                    cr.date_start <= coalesce(s.date_order, now()) AND (
                    cr.date_end is null or cr.date_end > coalesce(
                        s.date_order, now())))
        '''
        return from_str

    def _group_by(self):
        group_by_str = '''
            GROUP BY
                s.company_id,
                s.create_uid,
                s.partner_id,
                u.factor,
                s.location_id,
                l.price_unit,
                s.date_approve,
                l.date_planned,
                l.product_uom,
                s.minimum_planned_date,
                s.pricelist_id,
                s.validator,
                s.dest_address_id,
                l.product_id,
                t.categ_id,
                s.date_order,
                l.state,
                spt.warehouse_id,
                u.uom_type,
                u.category_id,
                t.uom_id,
                u.id,
                u2.factor
        '''
        return group_by_str

    def init(self, cr):
        tools.drop_view_if_exists(cr, self._table)
        cr.execute('''CREATE or REPLACE VIEW %s AS (
            WITH currency_rate (currency_id, rate, date_start, date_end) AS (
                SELECT r.currency_id, r.rate, r.name AS date_start,
                    (SELECT name FROM res_currency_rate r2
                    WHERE r2.name > r.name AND
                        r2.currency_id = r.currency_id
                     ORDER BY r2.name ASC
                     LIMIT 1) AS date_end
                FROM res_currency_rate r
            )
            %s
            %s
            %s
        )''' % (self._table, self._select(), self._from(), self._group_by()))
