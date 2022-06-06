###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import models


class StockWarehouse(models.Model):
    _inherit = 'stock.warehouse'

    def _create_or_update_global_routes_rules(self):
        res = super()._create_or_update_global_routes_rules()
        module = self.env['ir.module.module'].search([
            ('name', '=', 'stock_mts_mto_rule'),
        ])
        if module.state != 'installed':
            return res
        if (self.mto_mts_management and self.mts_mto_rule_id
                and self.mts_mto_rule_id.action == 'split_procurement'):
            mts_mto_route = self.env.ref('stock_mts_mto_rule.route_mto_mts')
            rule = self.env['stock.rule'].search([
                ('location_id', '=', self.lot_stock_id.id),
                ('route_id', '=', mts_mto_route.id),
                ('action', '=', 'buy'),
            ], limit=1)
            if not rule:
                self.env['stock.rule'].create({
                    'sequence': 20,
                    'location_id': self.lot_stock_id.id,
                    'picking_type_id': self.in_type_id.id,
                    'warehouse_id': self.id,
                    'propagate': True,
                    'procure_method': 'make_to_stock',
                    'route_sequence': 5.0,
                    'name': 'MTS+MTO Buy',
                    'route_id': mts_mto_route.id,
                    'action': 'buy',
                })
        return res
