# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp import models, api, _, exceptions


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    @api.multi
    def action_picking_create(self):
        picking_id = super(PurchaseOrder, self).action_picking_create()
        if not picking_id:
            return picking_id
        picking = self.env['stock.picking'].browse(picking_id)
        if not picking.picking_type_id.auto_return_picking:
            return picking_id
        if not picking.picking_type_id.return_picking_type_id:
            raise exceptions.Warning(_(
                'You must fill \'Picking type for returns\' field in \'%s\' '
                'picking type!') % picking.picking_type_id.name)
        picking_return = picking.copy({
            'picking_type_id': (
                picking.picking_type_id.return_picking_type_id and
                picking.picking_type_id.return_picking_type_id.id or None),
            'move_lines': None})
        move_obj = self.env['stock.move']
        for move in picking.move_lines:
            data = {
                'picking_id': picking_return.id,
                'picking_type_id': move.picking_type_id.id,
                'warehouse_id': move.warehouse_id.id,
                'purchase_line_id': move.purchase_line_id.id,
                'name': move.name,
                'origin': move.origin,
                'product_id': move.product_id.id,
                'product_uom': move.product_uom.id,
                'product_uom_qty': move.product_uom_qty,
                'product_uos': move.product_uos.id,
                'product_uos_qty': move.product_uos_qty,
                'location_id': move.location_dest_id.id,
                'location_dest_id': move.location_id.id,
                'invoice_state': 'none',
                'move_dest_id': move.id,
                'group_id': move.group_id and move.group_id.id or None}
            move_return = move_obj.create(data)
        for move in picking.move_lines:
            move.state = 'waiting'
        for move_return in picking_return.move_lines:
            move_return.state = 'assigned'
        return picking_id
