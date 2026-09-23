###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class StockPickingReturnSupplier(models.TransientModel):
    _name = 'stock.picking.return.supplier'
    _description = 'Wizard to create stock picking return supplier'

    @api.model
    def _get_supplier_domain(self):
        return [('supplier', '=', True)]

    def _get_default_picking_type(self):
        picking_types = self.env['stock.picking.type'].search([
            ('code', '=', 'outgoing'),
        ])
        picking_types.filtered(
            lambda t: t.warehouse_id.company_id == self.env.user.company_id)
        if picking_types:
            return picking_types[0]

    partner_id = fields.Many2one(
        comodel_name='res.partner',
        string='Supplier',
        required=True,
        domain=_get_supplier_domain,
    )
    location_id = fields.Many2one(
        comodel_name='stock.location',
        string='Location',
        required=True,
    )
    picking_type = fields.Many2one(
        comodel_name='stock.picking.type',
        string='Picking type',
        required=True,
        default=_get_default_picking_type,
    )
    confirm_line_ids = fields.One2many(
        comodel_name='stock.picking.return.supplier.line',
        inverse_name='wizard_id',
        string='Confirm lines',
    )
    qty_inventory = fields.Integer(
        string='Quantity of products in stock',
    )
    qty_return = fields.Integer(
        string='Quantity of products to be returned',
    )

    def check_barcode(self, barcode, supplier_code):
        index = barcode.find('.')
        if index != 1 and barcode[index:] == supplier_code:
            return True
        else:
            return False

    def search_purchase_order(self, line):
        if line.move_id.purchase_line_id:
            return line.move_id.purchase_line_id.order_id
        if line.move_id.picking_id.purchase_id:
            return line.move_id.picking_id.purchase_id
        if line.move_id.sale_line_id:
            purchases = self.env['sale.order'].get_purchase_order_ids(
                line.move_id.sale_line_id.order_id)
            if len(purchases) == 1:
                purchase = self.env['purchase.order'].browse(purchases[0])
                return purchase
        if line.move_id.picking_id.sale_id:
            purchases = self.env['sale.order'].get_purchase_order_ids(
                line.move_id.picking_id.sale_id)
            if len(purchases) == 1:
                purchase = self.env['purchase.order'].browse(purchases[0])
                return purchase
        if line.move_id.picking_id.origin:
            sales_ref = line.move_id.picking_id.origin.split(', ')
            if len(sales_ref) == 1:
                sales = self.env['sale.order'].search([
                    ('name', '=', sales_ref[0]),
                ], limit=1)
                if sales:
                    purchases = self.env['sale.order'].get_purchase_order_ids(
                        sales)
                    if len(purchases) == 1:
                        purchase = self.env['purchase.order'].browse(
                            purchases[0])
                        return purchase
        if line.move_id.picking_id.partner_id:
            sales = self.env['sale.order'].search([
                ('partner_id', '=', line.move_id.picking_id.partner_id.id),
            ], limit=1)
            if sales:
                purchases = self.env['sale.order'].get_purchase_order_ids(
                    sales)
                if len(purchases) == 1:
                    purchase = self.env['purchase.order'].browse(purchases[0])
                    return purchase
        return False

    def button_get_products_location(self):
        line_obj = self.env['stock.picking.return.supplier.line']
        quants = self.env['stock.quant'].search([
            ('location_id', 'child_of', self.location_id.id),
        ])
        if len(self.partner_id.category_id) == 0:
            raise ValidationError(_('Supplier has no code label'))
        supplier_code = self.partner_id.category_id[0].name
        for quant in quants:
            if quant.quantity <= 0:
                continue
            barcode = quant.product_id.barcode
            condition = (
                quant.product_id.default_code
                and quant.product_id.default_code.startswith(supplier_code)
                or self.check_barcode(barcode, supplier_code))
            if condition:
                lines = self.env['stock.move.line'].search([
                    ('state', '=', 'done'),
                    ('product_id', '=', quant.product_id.id),
                ])
                lines_in = lines.filtered(
                    lambda ln: ln.location_id != self.location_id and (
                        ln.location_dest_id == self.location_id))
                lines_out = lines.filtered(
                    lambda ln: ln.location_dest_id != self.location_id and (
                        ln.location_id == self.location_id))
                qty_in = sum([line.qty_done for line in lines_in])
                qty_out = sum([line.qty_done for line in lines_out])
                qty_available = quant.quantity
                lines_find_list = []
                for line in lines_in.sorted(key='date', reverse=True):
                    vals = {}
                    if qty_available == 0:
                        continue
                    lines_find = lines_out.filtered(
                        lambda ln: ln.id not in lines_find_list and (
                            ln.picking_id.sale_id == line.picking_id.sale_id))
                    qty_done = 0
                    for line_find in lines_find:
                        qty_done += line_find.qty_done
                        lines_find_list.append(line_find.id)
                    if lines_find and qty_done == line.qty_done:
                        continue
                    if lines_find and qty_done < line.qty_done:
                        vals.update({
                            'wizard_id': self.id,
                            'product_id': line.product_id.id,
                            'qty': line.qty_done - qty_done,
                            'move_id': line.move_id.id,
                            'picking_id': line.move_id.picking_id.id,
                        })
                        purchase = self.search_purchase_order(line)
                        if purchase:
                            vals.update({
                                'purchase_id': purchase.id,
                            })
                        line_obj.create(vals)
                        continue
                    if not lines_find and qty_in > qty_out:
                        if (qty_available - line.qty_done) < 0:
                            vals.update({
                                'wizard_id': self.id,
                                'product_id': line.product_id.id,
                                'qty': qty_available,
                                'move_id': line.move_id.id,
                                'picking_id': line.move_id.picking_id.id,
                            })
                            purchase = self.search_purchase_order(line)
                            if purchase:
                                vals.update({
                                    'purchase_id': purchase.id,
                                })
                            line_obj.create(vals)
                            qty_available -= qty_available
                            continue
                        vals.update({
                            'wizard_id': self.id,
                            'product_id': line.product_id.id,
                            'qty': line.qty_done,
                            'move_id': line.move_id.id,
                            'picking_id': line.move_id.picking_id.id,
                        })
                        purchase = self.search_purchase_order(line)
                        if purchase:
                            vals.update({
                                'purchase_id': purchase.id,
                            })
                        line_obj.create(vals)
                        qty_available -= line.qty_done
                        continue
        self.qty_return = sum([line.qty for line in self.confirm_line_ids])
        self.qty_inventory = sum([
            quant.quantity for quant in quants
            if quant.product_id.default_code
            and quant.product_id.default_code.startswith(supplier_code)
            and quant.quantity >= 0])
        return self._reopen_view()

    def _reopen_view(self):
        return {
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'view_type': 'form',
            'res_id': self.ids[0],
            'res_model': self._name,
            'target': 'new',
            'context': {'wizard_id': self.id},
        }

    def button_accept(self):
        supplier_location = self.env.ref('stock.stock_location_suppliers')
        picking = self.env['stock.picking'].create({
            'partner_id': self.partner_id.id,
            'location_id': self.location_id.id,
            'location_dest_id': supplier_location.id,
            'picking_type_id': self.picking_type.id,
            'is_return_supplier': True,
        })
        for line in self.confirm_line_ids:
            move_line = picking.move_lines.create({
                'name': line.product_id.name,
                'picking_id': picking.id,
                'product_id': line.product_id.id,
                'product_uom': line.product_id.uom_id.id,
                'product_uom_qty': line.qty,
                'location_id': self.location_id.id,
                'location_dest_id': supplier_location.id,
                'origin_returned_move_id': line.move_id.id,
                'to_refund': True,
                'note': line.purchase_id and line.purchase_id.name or '',
            })
            if line.move_id.purchase_line_id:
                move_line.purchase_line_id = line.move_id.purchase_line_id.id
        form_view = self.env.ref('stock.view_picking_form')
        tree_view = self.env.ref('stock.vpicktree')
        search_view = self.env.ref('stock.view_picking_internal_search')
        return {
            'name': _('Stock pickings'),
            'res_model': 'stock.picking',
            'type': 'ir.actions.act_window',
            'views': [(tree_view.id, 'tree'), (form_view.id, 'form')],
            'view_mode': 'tree,form',
            'search_view_id': search_view.id,
            'view_type': 'form',
            'res_id': picking.id,
            'domain': [('id', 'in', picking.ids)],
        }

    def button_delete_lines(self):
        self.qty_return = 0
        self.qty_inventory = 0
        for line in self.confirm_line_ids:
            line.unlink()
        return self._reopen_view()


class StockPickingReturnSupplierLine(models.TransientModel):
    _name = 'stock.picking.return.supplier.line'
    _description = 'Wizard lines'

    wizard_id = fields.Many2one(
        comodel_name='stock.picking.return.supplier',
        string='Wizard',
    )
    picking_id = fields.Many2one(
        comodel_name='stock.picking',
        string='Picking',
    )
    product_id = fields.Many2one(
        comodel_name='product.product',
        string='Product',
    )
    qty = fields.Integer(
        string='Quantity',
    )
    move_id = fields.Many2one(
        comodel_name='stock.move',
        string='Stock move',
    )
    purchase_id = fields.Many2one(
        comodel_name='purchase.order',
        string='Purchase order',
    )
