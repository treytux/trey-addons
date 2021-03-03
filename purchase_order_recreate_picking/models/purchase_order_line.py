###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import _, api, models
from odoo.exceptions import UserError


class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'

    @api.multi
    def _prepare_recreate_stock_moves(self, picking):
        def _update_template(template):
            quant_uom = self.product_id.uom_id
            get_param = self.env['ir.config_parameter'].sudo().get_param
            if get_param('stock.propagate_uom') != '1':
                product_qty = self.product_uom._compute_quantity(
                    qty, quant_uom, rounding_method='HALF-UP')
                template['product_uom'] = quant_uom.id
                template['product_uom_qty'] = product_qty
            else:
                template['product_uom_qty'] = (
                    self.product_uom._compute_quantity(
                        qty, self.product_uom, rounding_method='HALF-UP'))
            return template

        self.ensure_one()
        if self.product_id.type not in ['product', 'consu']:
            return []
        res = []
        qty_in = 0.0
        qty_out = 0.0
        price_unit = self._get_stock_move_price_unit()
        for move in self.move_ids.filtered(lambda x: x.state != 'cancel'):
            if move.location_id.usage == 'supplier':
                qty_in += move.product_uom._compute_quantity(
                    move.product_uom_qty, self.product_uom,
                    rounding_method='HALF-UP')
            elif move.location_dest_id.usage == 'supplier':
                qty_out += move.product_uom._compute_quantity(
                    move.product_uom_qty, self.product_uom,
                    rounding_method='HALF-UP')
        warehouse = self.order_id.picking_type_id.warehouse_id
        template = {
            'name': (self.name or '')[:2000],
            'product_id': self.product_id.id,
            'product_uom': self.product_uom.id,
            'date': self.order_id.date_order,
            'date_expected': self.date_planned,
            'location_id': self.order_id.partner_id.property_stock_supplier.id,
            'location_dest_id': self.order_id._get_destination_location(),
            'picking_id': picking.id,
            'partner_id': self.order_id.dest_address_id.id,
            'move_dest_ids': [(4, x) for x in self.move_dest_ids.ids],
            'state': 'draft',
            'purchase_line_id': self.id,
            'company_id': self.order_id.company_id.id,
            'price_unit': price_unit,
            'picking_type_id': self.order_id.picking_type_id.id,
            'group_id': self.order_id.group_id.id,
            'origin': self.order_id.name,
            'route_ids': (
                warehouse and [(6, 0, [x.id for x in warehouse.route_ids])]
                or []),
            'warehouse_id': warehouse.id,
        }
        if self.qty_received < 0:
            raise UserError(_(
                'The stock picking cannot be recreated because there is more '
                'quantity returned than received.'))

        diff_qty = self.product_qty - self.qty_received
        if diff_qty == 0:
            return res
        qty = diff_qty
        template = _update_template(template)
        res.append(template)
        return res

    @api.multi
    def _prepare_stock_moves(self, picking):
        if self._context.get('recreate_picking'):
            return self._prepare_recreate_stock_moves(picking)
        return super()._prepare_stock_moves(picking)
