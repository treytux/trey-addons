################################################################################
# For copyright and license notices, see __manifest__.py file in root directory
################################################################################
from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    reservation_picking_ids = fields.Many2many(
        comodel_name='stock.picking',
        relation='sale_order_reserve2picking_rel',
        column1='sale_reserve_id',
        column2='picking_id',
        copy=False,
    )
    customer_reservation = fields.Boolean(
        string='Customer reservation',
        copy=False,
    )
    reservation_count = fields.Integer(
        string='Reservation picking count',
        compute='_compute_reservation_count',
    )

    @api.depends('reservation_picking_ids')
    def _compute_reservation_count(self):
        for order in self:
            order.reservation_count = len(order.reservation_picking_ids)

    def action_reserve_products_sale(self):
        self.ensure_one()
        action = self.env.ref(
            'sale_order_reserve_products.action_sale_products_reserve')
        action = action.read()[0]
        return action

    def action_cancel_reserve_products(self):
        picking = self.reservation_picking_ids.filtered(
            lambda p: p.customer_reservation and p.state == 'assigned')
        if not picking:
            raise ValidationError(
                _('No reservation picking to cancel'))
        picking.do_unreserve()
        if picking.state == 'assigned':
            raise ValidationError(
                _('The cancellation of the reservation picking %s '
                    'was not completed successfully') % picking.name)
        picking.action_cancel()
        if picking.state != 'cancel':
            raise ValidationError(
                _('The reservation picking %s could not be canceled') % (
                    picking.name))
        self.customer_reservation = False

    @api.multi
    def action_cancel(self):
        for sale in self:
            picking = sale.reservation_picking_ids.filtered(
                lambda p: p.customer_reservation and p.state == 'assigned')
            if not picking:
                continue
            picking.do_unreserve()
            if picking.state == 'assigned':
                raise ValidationError(
                    _('The cancellation of the reservation picking %s '
                        'was not completed successfully') % picking.name)
            picking.action_cancel()
            if picking.state != 'cancel':
                raise ValidationError(
                    _('The reservation picking %s could not be canceled') % (
                        picking.name))
            sale.customer_reservation = False
        return super().action_cancel()

    @api.multi
    def action_confirm(self):
        res = super().action_confirm()
        if res is not True:
            return res
        quant_obj = self.env['stock.quant']
        for sale in self:
            vals = []
            reservation_picking = sale.reservation_picking_ids.filtered(
                lambda p: p.customer_reservation and p.state == 'assigned')
            if not reservation_picking:
                continue
            for line in reservation_picking.move_line_ids:
                item = {
                    'product_id': line.product_id,
                    'lot_id': line.lot_id,
                }
                vals.append(item)
            reservation_picking.do_unreserve()
            reservation_picking.action_cancel()
            picking = sale.picking_ids.sorted(key='id', reverse=True)[0]
            if picking.state in ['draft', 'waiting']:
                picking.action_confirm()
                if picking.state != 'confirmed':
                    raise ValidationError(_('Could not confirm the picking'))
            if picking.state == 'assigned':
                picking.do_unreserve()
                if picking.state != 'confirmed':
                    raise ValidationError(
                        _('Could not cancel the automatic reservation '
                            'of picking from the sale order'))
            for move in picking.move_lines:
                for item in vals:
                    if item['product_id'] == move.product_id:
                        qty_available = quant_obj._get_available_quantity(
                            move.product_id, move.location_id, item['lot_id'])
                        move._update_reserved_quantity(
                            1, qty_available, move.location_id,
                            lot_id=item['lot_id'], strict=False)
            picking.action_assign()
            sale.customer_reservation = False
        return res

    def action_view_reserve_pickings(self):
        form_view = self.env.ref('stock.view_picking_form')
        tree_view = self.env.ref('stock.vpicktree')
        search_view = self.env.ref('stock.view_picking_internal_search')
        action_vals = {
            'name': _('Stock pickings'),
            'res_model': 'stock.picking',
            'type': 'ir.actions.act_window',
            'views': [(tree_view.id, 'tree'), (form_view.id, 'form')],
            'view_mode': 'tree, form',
            'search_view_id': search_view.id,
            'view_type': 'form',
            'domain': [('id', 'in', self.reservation_picking_ids.ids)],
        }
        if len(self.reservation_picking_ids) == 1:
            del action_vals['views']
            action_vals.update({
                'view_mode': 'form',
                'res_id': self.reservation_picking_ids[0].id,
            })
        return action_vals
