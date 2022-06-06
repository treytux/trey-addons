###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import api, fields, models


class EventEvent(models.Model):
    _inherit = 'event.event'

    picking_ids = fields.One2many(
        comodel_name='stock.picking',
        compute='_compute_pickings',
        string='Pickings',
    )
    picking_count = fields.Integer(
        string='Picking count',
        compute='_compute_pickings',
    )

    @api.depends('product_ids', 'product_ids.stock_move_ids')
    def _compute_pickings(self):
        for event in self:
            pickings = event.product_ids.mapped('stock_move_ids.picking_id')
            event.picking_ids = [(6, 0, pickings.ids)]
            event.picking_count = len(pickings)

    def create_services_and_material(self):
        self.ensure_one()
        super().create_services_and_material()
        location_dst = self.address_id.property_stock_customer
        warehouse = self.env['stock.warehouse'].search(
            [('company_id', '=', self.env.user.company_id.id)], limit=1)
        picking = self.env['stock.picking'].create({
            'partner_id': self.address_id.id,
            'location_id': warehouse.lot_stock_id.id,
            'location_dest_id': location_dst.id,
            'picking_type_id': warehouse.int_type_id.id,
        })
        move_lines = self.env['stock.move'].browse([])
        for line in self.product_ids:
            if line.product_id.type != 'product':
                continue
            move_lines |= move_lines.create({
                'picking_id': picking.id,
                'event_id': self.id,
                'event_product_id': line.id,
                'product_id': line.product_id.id,
                'name': line.product_id.name,
                'product_uom': line.product_id.uom_id.id,
                'product_uom_qty': line.quantity,
                'location_id': warehouse.lot_stock_id.id,
                'location_dest_id': location_dst.id,
            })
        if not move_lines:
            picking.unlink()
            return
        picking.action_confirm()
        picking.action_assign()

    def button_cancel(self):
        super().button_cancel()
        self.ensure_one()
        for picking in self.picking_ids:
            if picking.state in ['cancel', 'done']:
                continue
            picking.action_cancel()

    @api.multi
    def action_view_delivery(self):
        action = self.env.ref('stock.action_picking_tree_all').read()[0]
        pickings = self.mapped('picking_ids')
        if len(pickings) > 1:
            action['domain'] = [('id', 'in', pickings.ids)]
        elif pickings:
            action['views'] = [
                (self.env.ref('stock.view_picking_form').id, 'form')]
            action['res_id'] = pickings.id
        return action
