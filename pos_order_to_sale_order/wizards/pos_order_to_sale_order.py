###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import _, fields, models
from odoo.exceptions import UserError


class PosOrderToSaleOrder(models.TransientModel):
    _name = 'pos_order_to_sale_order'
    _description = 'Create a sale order from a pos order'

    name = fields.Char(
        string='Empty',
    )
    line_ids = fields.One2many(
        comodel_name='pos_order_to_sale_order.line',
        inverse_name='wizard_id',
        string='Lines',
        readonly=True,
    )
    sale_order_ids = fields.Many2many(
        comodel_name='sale.order',
        relation='pos_order_to_sale_order2sale_rel',
        column1='pos_order_to_sale_order_id',
        column2='sale_id',
    )

    def add_error(self, msg, pos_order):
        self.line_ids.create({
            'wizard_id': self.id,
            'name': msg,
            'pos_order_id': pos_order.id,
        })

    def create_sale_order(self, pos_order):
        partner = pos_order.partner_id
        sale = self.env['sale.order'].create({
            'origin': pos_order.name,
            'partner_id': partner.id,
            'partner_invoice_id': partner.id,
            'partner_shipping_id': partner.id,
            'pricelist_id': (
                partner.property_product_pricelist
                and partner.property_product_pricelist.id
                or self.env.ref('product.list0').id),
            'picking_policy': 'direct',
        })
        sale.onchange_partner_id()
        for pos_order_line in pos_order.lines:
            vline = self.env['sale.order.line'].new({
                'order_id': sale.id,
                'name': pos_order_line.product_id.name,
                'product_id': pos_order_line.product_id.id,
                'product_uom_qty': pos_order_line.qty,
                'product_uom': pos_order_line.product_id.uom_id.id,
                'price_unit': pos_order_line.price_unit,
                'discount': pos_order_line.discount,
                'tax_id': [(6, 0, pos_order_line.tax_ids.ids)],
            })
            vline.product_id_change()
            vline.update({
                'price_unit': pos_order_line.price_unit,
                'discount': pos_order_line.discount,
            })
            self.env['sale.order.line'].create(
                vline._convert_to_write(vline._cache))
        self.link_sale_order_line2stock_moves(sale, pos_order.picking_id)
        lines_without_moves = sale.order_line.filtered(
            lambda ln: not ln.move_ids and ln.product_id.type != 'service')
        if lines_without_moves:
            self.add_error(
                'Moves without linked to sale order line.', pos_order)
            sale.unlink()
            return False
        sale.write({
            'picking_ids': [(4, pos_order.picking_id.id)],
            'partner_shipping_id': (
                pos_order.picking_id.partner_id
                and pos_order.picking_id.partner_id.id
                or sale.partner_id.id),
        })
        sale.action_confirm()
        pos_order.sale_id = sale.id
        return sale

    def link_sale_order_line2stock_moves(self, sale, picking):
        for order_line in sale.order_line:
            moves_rel = picking.move_lines.filtered(
                lambda m: m.product_id == order_line.product_id
                and m.product_uom_qty == order_line.product_uom_qty
                and not m.sale_line_id.exists()
            )
            if not moves_rel:
                moves_rel = picking.move_lines.filtered(
                    lambda m: m.product_id == order_line.product_id
                    and m.product_uom_qty == -1 * order_line.product_uom_qty
                    and not m.sale_line_id.exists()
                )
            move_rel = moves_rel and moves_rel[0] or None
            order_line.move_ids = [(4, move_rel.id)]

    def action_accept(self):
        pos_orders = self.env['pos.order'].browse(
            self.env.context.get('active_ids', []))
        for pos_order in pos_orders:
            if not pos_order.partner_id:
                self.add_error(_(
                    'The pos order must have a partner assigned.'), pos_order)
                continue
            if pos_order.sale_id:
                self.add_error(_('The pos has a sale order.'), pos_order)
                continue
            if pos_order.invoice_id:
                self.add_error(_(
                    'The pos order is already invoiced. It cannot be invoiced '
                    'again.'), pos_order)
                continue
            if not pos_order.picking_id:
                self.add_error(_(
                    'The pos order has not an associated stock picking.'),
                    pos_order)
                continue
            if pos_order.picking_id.invoice_ids:
                self.add_error(_(
                    'The picking of pos order is already invoiced. It cannot '
                    'be invoiced again.'), pos_order)
                continue
            sale = self.create_sale_order(pos_order)
            if not sale:
                continue
            self.sale_order_ids = [(4, sale.id)]
        view = self.env.ref(
            'pos_order_to_sale_order.pos_order_to_sale_order_wizard_done')
        return {
            'type': 'ir.actions.act_window',
            'res_model': self._name,
            'view_type': 'form',
            'view_mode': 'form',
            'views': [(view.id, 'form')],
            'target': 'new',
            'res_id': self.id,
        }

    def action_show_sale_orders(self):
        if not self.sale_order_ids:
            raise UserError(_('No sales order has been generated.'))
        form_view = self.env.ref('sale.view_order_form')
        tree_view = self.env.ref('sale.view_order_tree')
        search_view = self.env.ref('sale.view_sales_order_filter')
        return {
            'name': _('Sale orders'),
            'res_model': 'sale.order',
            'type': 'ir.actions.act_window',
            'views': [(tree_view.id, 'tree'), (form_view.id, 'form')],
            'view_mode': 'tree,form',
            'search_view_id': search_view.id,
            'view_type': 'form',
            'domain': [('id', 'in', self.sale_order_ids.ids)],
        }


class PosOrderToSaleOrderLine(models.TransientModel):
    _name = 'pos_order_to_sale_order.line'
    _description = 'Lines'

    name = fields.Char(
        string='Message',
    )
    wizard_id = fields.Many2one(
        comodel_name='pos_order_to_sale_order',
        string='Wizard',
    )
    pos_order_id = fields.Many2one(
        comodel_name='pos.order',
        string='Pos order',
    )
