###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import _, models
from odoo.exceptions import UserError


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    def get_stock_locations(self):
        return_stock_location = self.env['stock.location'].search([
            ('usage', '=', 'return'),
            ('company_id', '=', self.company_id.id)
        ], limit=1)
        if not return_stock_location:
            raise UserError(
                _('Return stock locations not created for this company'))
        return {
            'customer_location': self.env.ref(
                'stock.stock_location_customers'),
            'return_location': return_stock_location,
            'scrap_location': self.env.ref('stock.stock_location_scrapped'),
            'stock_location': self.warehouse_id.lot_stock_id,
        }

    def assign_locations(
            self, picking, picking_type, location_src, location_dst):
        picking.write({
            'picking_type_id': picking_type.id,
            'location_id': location_src.id,
            'location_dest_id': location_dst.id,
        })
        for move in picking.move_lines:
            move.write({
                'location_id': picking.location_id.id,
                'location_dest_id': picking.location_dest_id.id,
            })
            move.move_line_ids.write({
                'location_id': picking.location_id.id,
                'location_dest_id': picking.location_dest_id.id,
            })

    def create_picking(
            self, picking_type_id, location_src, location_dst, ttype):
        self.ensure_one()
        move_lines = []
        ttype_lines = self.order_line.filtered(lambda ol: ol.ttype == ttype)
        for line in ttype_lines:
            move_lines.append({
                'product_id': line.product_id.id,
                'name': line.product_id.name,
                'product_uom': line.product_id.uom_id.id,
                'product_uom_qty': line.product_uom_qty,
                'sale_line_id': line.id,
                'group_id': line.order_id.procurement_group_id.id,
            })
        return self.env['stock.picking'].create({
            'partner_id': self.partner_id.id,
            'picking_type_id': picking_type_id,
            'location_id': location_src.id,
            'location_dest_id': location_dst.id,
            'move_lines': [(0, 0, m) for m in move_lines],
        })

    def chain_moves(self, picking_orig, picking_dest):
        for move_line in picking_dest.move_lines:
            origin_moves = self.env['stock.move'].search([
                ('id', 'in', picking_orig.mapped('move_lines').ids),
                ('product_id', '=', move_line.product_id.id),
            ])
            move_line.write({
                'move_orig_ids': [(6, 0, origin_moves.ids)]
            })

    def manage_pickings_ttype(
            self, picking_type, origin_location, dest_location, ttype):
        self.ensure_one()
        picking = self.picking_ids
        picking2 = self.create_picking(
            picking_type.id, origin_location, dest_location, ttype)
        self.chain_moves(picking, picking2)
        picking2.action_confirm()
        if ttype == 'change':
            locations = self.get_stock_locations()
            picking3 = self.create_picking(
                self.warehouse_id.out_type_id.id, locations['stock_location'],
                locations['customer_location'], ttype)
            picking3.action_confirm()

    def get_ttypes_lines(self):
        self.ensure_one()
        ttypes_lines = {}
        for line in self.order_line:
            if line.ttype not in ttypes_lines:
                ttypes_lines.update({
                    line.ttype : line,
                })
            else:
                ttypes_lines[line.ttype] += line
        return ttypes_lines

    def check_extra_pickings(self):
        self.ensure_one()
        lines_ttypes = self.get_ttypes_lines()
        locations = self.get_stock_locations()
        origin_location = locations['return_location']
        int_type_id = self.warehouse_id.int_type_id
        for lines_ttype in lines_ttypes:
            if lines_ttype == 'draft':
                continue
            if lines_ttype in ['change', 'no_stock']:
                dest_location = locations['scrap_location']
                self.manage_pickings_ttype(
                    int_type_id, origin_location, dest_location, lines_ttype)
            elif lines_ttype == 'repentance':
                dest_location = locations['stock_location']
                self.manage_pickings_ttype(
                    int_type_id, origin_location, dest_location, lines_ttype)
            elif lines_ttype in ['repaired', 'no_default', 'out_warranty']:
                dest_location = locations['customer_location']
                self.manage_pickings_ttype(
                    self.warehouse_id.out_type_id, origin_location,
                    dest_location, lines_ttype)

    def modify_income_picking(self):
        self.ensure_one()
        picking = self.picking_ids
        if picking.state != 'assigned':
            raise UserError(_('Picking are unexpected state, check please'))
        locations = self.get_stock_locations()
        in_type_id = self.warehouse_id.in_type_id
        self.assign_locations(
            picking, in_type_id, locations['customer_location'],
            locations['return_location'])

    def action_confirm(self):
        res = super().action_confirm()
        for sale in self:
            if not sale.is_return:
                continue
            if len(self.picking_ids) != 1:
                raise UserError(
                    _('There are unexpected pickings, check please'))
            sale.modify_income_picking()
            sale.check_extra_pickings()
        return res
