###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import _, fields, models


class StockWarehouse(models.Model):
    _inherit = 'stock.warehouse'

    mts_mtd_management = fields.Boolean(
        string='Use MTS+MTD rules',
        help='If this new route is selected on product form view, a '
             'dropshipping purchase order will be created only if the virtual '
             'stock is less than 0 else, the product will be taken from '
             'stocks.',
    )
    mts_mtd_rule_id = fields.Many2one(
        comodel_name='stock.rule',
        string='MTS+MTD rule',
    )

    def _get_all_routes(self):
        routes = super()._get_all_routes()
        routes |= self.mapped('mts_mtd_rule_id.route_id')
        return routes

    def _update_name_and_code(self, new_name=False, new_code=False):
        res = super()._update_name_and_code(new_name, new_code)
        if not new_name:
            return res
        for warehouse in self.filtered('mts_mtd_rule_id'):
            warehouse.mts_mtd_rule_id.write({
                'name': warehouse.mts_mtd_rule_id.name.replace(
                    warehouse.name, new_name, 1),
            })
        return res

    def _get_route_name(self, route_type):
        if route_type == 'mts_mtd':
            return _('MTS+MTD')
        return super()._get_route_name(route_type)

    def _get_global_route_rules_values(self):
        rule = self.get_rules_dict()[self.id][self.delivery_steps]
        rule = [r for r in rule if r.from_loc == self.lot_stock_id][0]
        location_id = rule.from_loc
        location_dest_id = rule.dest_loc
        picking_type_id = rule.picking_type
        res = super()._get_global_route_rules_values()
        route_name = _('Make to stock + Make to dropshipping')
        route = self.env['stock.location.route'].search([
            ('name', 'like', route_name),
        ], limit=1)
        res.update({
            'mts_mtd_rule_id': {
                'depends': ['delivery_steps', 'mts_mtd_management'],
                'create_values': {
                    'action': 'pull',
                    'procure_method': 'make_to_order',
                    'company_id': self.company_id.id,
                    'auto': 'manual',
                    'propagate': True,
                    'route_id': route.id,
                },
                'update_values': {
                    'active': self.mts_mtd_management,
                    'name': self._format_rulename(
                        location_id, location_dest_id, 'MTS+MTD'),
                    'location_id': location_dest_id.id,
                    'location_src_id': location_id.id,
                    'picking_type_id': picking_type_id.id,
                }
            },
        })
        return res

    def _create_or_update_global_routes_rules(self):
        res = super()._create_or_update_global_routes_rules()
        is_mts_mtd = (
            self.mts_mtd_management and self.mts_mtd_rule_id
            and self.mts_mtd_rule_id.action != 'split_procurement_mts_mtd')
        if is_mts_mtd:
            rule = self.env['stock.rule'].search([
                ('location_id', '=', self.mts_mtd_rule_id.location_id.id),
                ('location_src_id', '=',
                 self.mts_mtd_rule_id.location_src_id.id),
                ('route_id', '=', self.delivery_route_id.id),
            ], limit=1)
            self.mts_mtd_rule_id.write({
                'action': 'split_procurement_mts_mtd',
                'mts_rule_id': rule.id,
                'mtd_rule_id': self.env.ref(
                    'stock_dropshipping.stock_rule_drop_shipping').id,
            })
        return res
