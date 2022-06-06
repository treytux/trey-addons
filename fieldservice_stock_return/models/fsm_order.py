###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import _, fields, models
from odoo.exceptions import UserError, ValidationError


class FsmOrder(models.Model):
    _inherit = 'fsm.order'

    stock_returned = fields.Boolean(
        string='Stock returned',
        help='FSM stock returned',
        readonly=True,
    )

    def get_location_dest_id(self):
        return self.warehouse_id.lot_stock_id.id

    def create_picking(self, moves):
        self.ensure_one()
        location_id = self.warehouse_id.lot_stock_id.id
        location_dest_id = self.sale_id.warehouse_id.lot_stock_id.id
        picking_moves = self.env['stock.move']
        picking_type_out = self.env.ref('stock.picking_type_out')
        for move in moves:
            moves_out = picking_moves.search([
                ('picking_id', 'in', self.picking_ids.ids),
                ('picking_id.picking_type_id', '=', picking_type_out.id),
                ('product_id', '=', move.product_id.id),
            ])
            qty_left = (
                move.quantity_done - sum(moves_out.mapped('quantity_done')))
            if qty_left <= 0:
                continue
            picking_moves |= picking_moves.create({
                'name': move.product_id.name,
                'product_id': move.product_id.id,
                'product_uom': move.product_uom.id,
                'product_uom_qty': qty_left,
                'quantity_done': qty_left,
                'location_id': location_id,
                'location_dest_id': location_dest_id,
            })
        if not picking_moves:
            raise ValidationError(_('There are not quantities to return.'))
        picking_type_internal = self.env.ref('stock.picking_type_internal')
        picking_return = self.env['stock.picking'].create({
            'picking_type_id': picking_type_internal.id,
            'partner_id': self.sale_id.partner_id.id,
            'location_id': location_id,
            'location_dest_id': location_dest_id,
            'origin': self.name,
            'fsm_order_id': self.id,
            'move_lines': [(6, 0, picking_moves.ids)],
        })
        picking_return.action_done()
        fsm_order_msg = _(
            '''This order has created return stock picking: <a href=#
            data-oe-model=stock.picking data-oe-id=%d>%s</a>
            ''') % (picking_return.id, picking_return.name)
        self.message_post(body=fsm_order_msg)
        picking_msg = _(
            '''This picking has been created from fieldservice order: <a href=
               # data-oe-model=fsm.order data-oe-id=%d>%s</a>
            ''') % (self.id, self.name)
        picking_return.message_post(body=picking_msg)
        self.stock_returned = True
        return picking_return

    def action_return_stock(self):
        for order in self:
            if order.stock_returned:
                raise UserError(_('Fieldservice order stock already returned.'))
            if not order.stage_is_closed:
                raise ValidationError(_(
                    'Fieldservice order must be in done or cancel state.'))
            stock_moves = order.mapped('move_internal_ids').filtered(
                lambda x: x.state == 'done')
            if not stock_moves:
                raise UserError(_('There no are stock moves done.'))
            order.create_picking(stock_moves)
