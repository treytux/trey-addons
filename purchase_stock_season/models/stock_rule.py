###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import api, models


class StockRule(models.Model):
    _inherit = 'stock.rule'

    @api.multi
    def _prepare_purchase_order(self, product_id, product_qty, product_uom,
                                origin, values, partner):
        res = super()._prepare_purchase_order(
            product_id, product_qty, product_uom, origin, values, partner)
        route_ids = values.get('route_ids', None)
        group_id = values.get('group_id', None)
        if not route_ids or not group_id:
            return res
        if not route_ids.is_season:
            return res
        res.update({
            'sale_order_id': group_id.sale_id.id,
            'is_season': True,
        })
        return res

    @api.multi
    def _make_po_get_domain(self, values, partner):
        domain = super()._make_po_get_domain(values, partner)
        route_ids = values.get('route_ids', False)
        if not route_ids:
            return domain
        if route_ids.is_season:
            group_id = values.get('group_id', None)
            if not group_id or not group_id.sale_id:
                return domain
            domain += (
                ('is_season', '=', True),
                ('sale_order_id', '=', group_id.sale_id.id or None),
            )
        else:
            domain += (
                ('is_season', '=', False),
            )
        return domain
