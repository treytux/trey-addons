###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import _, api, fields, models
from odoo.exceptions import UserError


class FsmOrder(models.Model):
    _inherit = 'fsm.order'

    warehouse_id = fields.Many2one(
        track_visibility='onchange',
    )
    sale_id = fields.Many2one(
        copy=False,
    )
    sale_line_id = fields.Many2one(
        copy=False,
    )

    def update_picking_location(self, pickings):
        def _get_state_name(picking):
            return dict(self.env['stock.picking']._fields[
                'state'].selection).get(picking.state)

        def _create_internal_move(sale, move, picking):
            return self.env['stock.move'].create({
                'picking_id': picking.id,
                'fsm_order_id': self.id,
                'product_id': move_out.product_id.id,
                'location_id': location_src.id,
                'location_dest_id': location_dest.id,
                'name': move_out.product_id.name,
                'procure_method': 'make_to_stock',
                'product_uom_qty': move_out.product_uom_qty,
                'product_uom': move_out.product_id.uom_id.id,
                'group_id': sale.procurement_group_id.id,
            })

        self.ensure_one()
        pickings = pickings.filtered(
            lambda p: p.picking_type_code in ['outgoing', 'internal'])
        internal_pickings = pickings.filtered(
            lambda p: p.picking_type_code == 'internal')
        sale = self.sale_id
        for picking in pickings:
            is_not_change = (
                any([m.state not in ['draft', 'confirmed']
                    for p in pickings for m in p.move_lines]))
            if is_not_change:
                raise UserError(_(
                    'Picking %s is in \'%s\' state but, if you want change '
                    'the warehouse, it must be in \'Draft\' or \'Waiting\' '
                    'state.' % (picking.name, _get_state_name(picking))))
            if picking.picking_type_code == 'outgoing':
                picking.location_id = self.warehouse_id.lot_stock_id.id
                if self.sale_id.warehouse_id == self.warehouse_id:
                    continue
                location_src = self.sale_id.warehouse_id.lot_stock_id
                location_dest = self.warehouse_id.lot_stock_id
                if internal_pickings:
                    is_create_move = (
                        any([m for p in internal_pickings
                            for m in p.move_lines if not m.sale_line_id]))
                    if is_create_move:
                        continue
                    for move_out in picking.move_lines:
                        _create_internal_move(
                            sale, move_out, internal_pickings[0])
                        internal_picking = internal_pickings[0]
                        internal_picking.fsm_order_id = (
                            internal_picking.move_lines[0]
                            and internal_picking.move_lines[0].fsm_order_id
                            and internal_picking.move_lines[0].fsm_order_id.id)
                else:
                    internal_picking = self.env['stock.picking'].create({
                        'picking_type_id': (
                            self.env.ref('stock.picking_type_internal').id),
                        'fsm_order_id': self.id,
                        'move_type': 'direct',
                        'location_id': location_src.id,
                        'location_dest_id': location_dest.id,
                        'origin': sale.name,
                    })
                    for move_out in picking.move_lines:
                        _create_internal_move(sale, move_out, internal_picking)
                        internal_picking.fsm_order_id = (
                            internal_picking.move_lines[0]
                            and internal_picking.move_lines[0].fsm_order_id
                            and internal_picking.move_lines[0].fsm_order_id.id)
            elif picking.picking_type_code == 'internal':
                picking.location_dest_id = self.warehouse_id.lot_stock_id.id
                picking.action_confirm()

    @api.multi
    def write(self, vals):
        res = super().write(vals)
        if 'warehouse_id' in vals:
            for fsm in self:
                pickings = self.env['stock.picking']
                pickings |= (
                    fsm.move_ids.mapped('picking_id')
                    + fsm.move_internal_ids.mapped('picking_id'))
                fsm.update_picking_location(pickings)
        return res
