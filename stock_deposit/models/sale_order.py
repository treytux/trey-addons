###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    is_sale_deposit = fields.Boolean(
        string='Is sale deposit?',
        help='If this field is marked, when confirming the sale order, an '
             'internal stock picking will be generated from the customer\'s '
             'deposit to \'Customers\'.',
    )
    is_inventory_deposit = fields.Boolean(
        string='Is inventory deposit?',
        help='If this field is marked, when confirming the sale order, two '
             'internal stock pickings will be generated: one from the '
             'customer\'s deposit to \'Customers\' and the other from '
             '\'Customers\' to \'Inventory adjustments\'.',
    )

    @api.constrains('is_sale_deposit', 'is_inventory_deposit')
    def _check_boolean_type(self):
        for sale in self:
            if sale.is_sale_deposit and sale.is_inventory_deposit:
                raise ValidationError(_(
                    'The sale order cannot have the options \'Is sale '
                    'deposit?\' and \'Is inventroy?\' checked simultaneously.'
                ))

    @api.constrains('is_sale_deposit', 'is_inventory_deposit')
    def _check_is_deposit(self):
        for sale in self:
            if not sale.is_sale_deposit and not sale.is_inventory_deposit:
                continue
            option_name = self.get_option_name(sale)
            shipping_parent_location = (
                sale.partner_shipping_id.property_stock_customer.location_id)
            wh_deposit_parent_location = sale.warehouse_id.deposit_parent_id
            if shipping_parent_location != wh_deposit_parent_location:
                raise ValidationError(_(
                    'The shipping address does not belong to a deposit of '
                    'the warehouse. The \'%s\' option is not allowed in '
                    'this case.') % option_name)

    def action_confirm(self):
        for sale in self:
            if not sale.is_sale_deposit and not sale.is_inventory_deposit:
                continue
            option_name = self.get_option_name(sale)
            shipping_parent_location = (
                sale.partner_shipping_id.property_stock_customer.location_id)
            wh_deposit_parent_location = sale.warehouse_id.deposit_parent_id
            if shipping_parent_location != wh_deposit_parent_location:
                raise ValidationError(_(
                    'The shipping address does not belong to a deposit of '
                    'the warehouse. The \'%s\' option is not allowed in '
                    'this case.') % option_name)
        return super().action_confirm()

    def _action_confirm(self):
        res = super(SaleOrder, self)._action_confirm()
        for sale in self:
            if not sale.is_sale_deposit and not sale.is_inventory_deposit:
                continue
            option_name = self.get_option_name(sale)
            pickings = sale.picking_ids.filtered(
                lambda p: p.state in ['confirmed', 'assigned'])
            qty_negative_lines = [
                ln for ln in sale.order_line if ln.product_uom_qty < 0]
            if not pickings and qty_negative_lines:
                inventory_location = self.env.ref('stock.location_inventory')
                customer_location = self.env.ref(
                    'stock.stock_location_customers')
                pickings = self.create_picking(
                    sale, inventory_location, customer_location,
                    force_abs_qty=True)
            elif not pickings and not qty_negative_lines:
                raise UserError(_(
                    'No stock picking has been generated, check it.'))
            if len(pickings) > 1:
                raise UserError(_(
                    'When the \'%s\' option is checked, there should only '
                    'be one stock picking generated.') % option_name)
            pickings = self.modify_picking(sale, pickings)
            self.transfer_pickings(pickings)
        return res

    def get_option_name(self, sale):
        return (
            sale.is_sale_deposit and sale._fields['is_sale_deposit'].string
            or sale.is_inventory_deposit
            and sale._fields['is_inventory_deposit'].string or '')

    def transfer_pickings(self, pickings):
        for picking in pickings:
            picking.action_confirm()
            for move in picking.move_lines:
                for move_line in move.move_line_ids:
                    move_line.write({
                        'location_id': move.location_id.id,
                        'location_dest_id': move.location_dest_id.id,
                    })
            picking.action_assign()
            for move in picking.move_lines:
                move.quantity_done = move.product_uom_qty
            picking.action_done()

    def create_picking(
            self, sale, location_src, location_dst, force_abs_qty=False):
        move_lines = []
        for line in sale.order_line:
            qty = (
                force_abs_qty and abs(line.product_uom_qty)
                or line.product_uom_qty)
            move_lines.append({
                'product_id': line.product_id.id,
                'name': line.product_id.name,
                'product_uom': line.product_id.uom_id.id,
                'product_uom_qty': qty,
                'sale_line_id': line.id,
            })
        return self.env['stock.picking'].create({
            'partner_id': sale.partner_id.id,
            'picking_type_id': sale.warehouse_id.int_type_id.id,
            'location_id': location_src.id,
            'location_dest_id': location_dst.id,
            'move_lines': [(0, 0, m) for m in move_lines],
        })

    def modify_picking(self, sale, picking):
        customer_location = self.env.ref('stock.stock_location_customers')
        inventory_location = self.env.ref('stock.location_inventory')
        shipping_location = sale.partner_shipping_id.property_stock_customer
        picking_type = sale.warehouse_id.int_type_id
        pickings = []
        pickings.append(picking)
        if sale.is_sale_deposit:
            location_src = shipping_location
            location_dst = customer_location
            self.assign_locations(
                picking, picking_type, location_src, location_dst)
        elif sale.is_inventory_deposit:
            qty_negative_lines = [
                ln for ln in sale.order_line if ln.product_uom_qty < 0]
            if not qty_negative_lines:
                location_src1 = shipping_location
                location_dst1 = customer_location
            else:
                location_src1 = inventory_location
                location_dst1 = customer_location
            self.assign_locations(
                picking, picking_type, location_src1, location_dst1)
            if not qty_negative_lines:
                picking_data = {
                    'location_id': customer_location.id,
                    'location_dest_id': inventory_location.id,
                }
            else:
                picking_data = {
                    'location_id': customer_location.id,
                    'location_dest_id': shipping_location.id,
                }
            picking2 = picking.copy(picking_data)
            pickings.append(picking2)
            if not qty_negative_lines:
                location_src = customer_location
                location_dst = inventory_location
            else:
                location_src = customer_location
                location_dst = shipping_location
            self.assign_locations(
                picking2, picking_type, location_src, location_dst)
        return pickings

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
