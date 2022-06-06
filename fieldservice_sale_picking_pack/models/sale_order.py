###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import api, models


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    @api.multi
    def copy(self, default=None):
        sale_copy = super().copy(default)
        for line in sale_copy.order_line:
            line.sale_line_fsm_id = None
        return sale_copy

    def _link_pickings_to_fsm(self):
        super()._link_pickings_to_fsm()
        for sale in self:
            for move in sale.picking_ids.mapped('move_ids_without_package'):
                if move.sale_line_id.sale_line_fsm_id:
                    line = move.sale_line_id.sale_line_fsm_id
                    fsm_order = self.env['fsm.order'].search([
                        '|',
                        ('sale_line_id', 'in', line.ids),
                        '&',
                        ('sale_id', 'in', line.order_id.ids),
                        ('sale_line_id', '=', False),
                    ])
                    move.fsm_order_id = fsm_order.id
                    move.picking_id.fsm_order_id = fsm_order.id
                else:
                    move.fsm_order_id = None

    def expand_pack(self, product, line):
        self.ensure_one()
        move_data_list = []
        if product.pack_ok:
            for component_line in product.get_pack_lines():
                fsm_orders = self.env['fsm.order'].search([
                    '|',
                    ('sale_line_id', 'in', line.ids),
                    '&',
                    ('sale_id', 'in', line.order_id.ids),
                    ('sale_line_id', '=', False),
                ])
                move_data_list.append({
                    'product_id': component_line.product_id.id,
                    'name': component_line.product_id.name,
                    'product_uom': component_line.product_id.uom_id.id,
                    'product_uom_qty': (
                        component_line.quantity * line.product_uom_qty),
                    'sale_line_id': line.id,
                    'fsm_order_id': fsm_orders and fsm_orders[0].id or None,
                })
        return move_data_list

    def get_stock_move_values(self, line):
        product_tmpl = line.product_id.product_tmpl_id
        product_kit = product_tmpl.product_tmpl_kit_id.product_variant_ids[0]
        return self.expand_pack(product_kit, line)

    def create_pickings(self, sale, move_lines_dict):
        fsm_order = self.env['fsm.order'].browse(
            move_lines_dict[0]['fsm_order_id'])
        sale_warehouse = sale.warehouse_id
        stock_location = sale_warehouse.lot_stock_id
        vehicle_warehouse = fsm_order.warehouse_id
        vehicle_stock_location = vehicle_warehouse.lot_stock_id
        [ml.update({
            'group_id': sale.procurement_group_id.id,
        }) for ml in move_lines_dict]
        return self.env['stock.picking'].create({
            'partner_id': sale.partner_id.id,
            'picking_type_id': sale_warehouse.int_type_id.id,
            'location_id': stock_location.id,
            'location_dest_id': vehicle_stock_location.id,
            'move_lines': [(0, 0, m) for m in move_lines_dict],
            'fsm_order_id': fsm_order.id,
            'origin': sale.name,
        })

    def _action_confirm(self):
        result = super()._action_confirm()
        for sale in self:
            move_lines_list = []
            for line in sale.order_line:
                product_tmpl = line.product_id.product_tmpl_id
                is_create_picking = (
                    product_tmpl.installation_product
                    and product_tmpl.product_tmpl_kit_id
                    and product_tmpl.field_service_tracking != 'no'
                )
                if is_create_picking:
                    move_lines_list.append(self.get_stock_move_values(line))
            for move_line_list in move_lines_list:
                pickings = self.create_pickings(sale, move_line_list)
                sale.picking_ids = [(4, p.id) for p in pickings]
        return result
