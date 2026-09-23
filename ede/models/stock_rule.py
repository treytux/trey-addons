###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import models


class StockRule(models.Model):
    _inherit = 'stock.rule'

    def _prepare_purchase_order(self, company_id, origins, values):
        res = super()._prepare_purchase_order(company_id, origins, values)
        values = values[0]
        group = values.get('group_id', None)
        if (not group or not group.stock_move_ids
                or not group.stock_move_ids.sale_line_id):
            return res
        route = group.stock_move_ids.sale_line_id.route_id
        if not route:
            return res
        if not route.is_ede_company and not route.is_ede_customer:
            return res
        res.update({
            'sale_order_id': group.sale_id.id,
            'is_ede_custom': True,
            'ede_client_order_ref': (
                group.sale_id.client_order_ref or group.sale_id.name),
        })
        if route.is_ede_customer:
            res['customer_shipping_id'] = (
                group.sale_id.partner_shipping_id.id or None)
        return res

    def _make_po_get_domain(self, company_id, values, partner):
        domain = super()._make_po_get_domain(company_id, values, partner)
        group = values.get('group_id', None)
        if (not group or not group.stock_move_ids
                or not group.stock_move_ids.sale_line_id):
            return domain
        route = group.stock_move_ids.sale_line_id.route_id
        if not route:
            return domain
        if route.is_ede_company or route.is_ede_customer:
            group = values.get('group_id', None)
            if not group or not group.sale_id:
                return domain
            domain += (
                ('is_ede_custom', '=', True),
                ('sale_order_id', '=', group.sale_id.id or None),
            )
        else:
            domain += (
                ('is_ede_custom', '=', False),
            )
        return domain
