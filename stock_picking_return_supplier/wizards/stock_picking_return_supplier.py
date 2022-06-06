###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class StockPickingReturnSupplier(models.TransientModel):
    _name = 'stock.picking.return.supplier'
    _description = 'Wizard to create stock picking return supplier'

    @api.model
    def _get_domain_partner_id(self):
        return [('supplier', '=', True)]

    partner_id = fields.Many2one(
        comodel_name='res.partner',
        string='Supplier',
        domain=_get_domain_partner_id,
    )
    location_id = fields.Many2one(
        comodel_name='stock.location',
        string='Location',
    )
    filter_by_date = fields.Boolean(
        string='Filter by date',
    )
    date = fields.Date(
        string='Date',
        default=fields.Date.today(),
    )
    location_dest_id = fields.Many2one(
        comodel_name='stock.location',
        string='Destination location'
    )
    picking_type = fields.Many2one(
        comodel_name='stock.picking.type',
        string='Operation type',
    )
    line_ids = fields.One2many(
        comodel_name='stock.picking.return.supplier.line',
        inverse_name='wizard_id',
        string='Lines',
    )
    confirm_line_ids = fields.One2many(
        comodel_name='stock.picking.return.supplier.line.confirm',
        inverse_name='wizard_id',
        string='Confirm lines',
    )

    def add_stock_move_lines_to_confirm_lines_resume(
            self, lines, order, line_ref):
        for line in lines:
            qty_available_01 = 0
            qty_available_02 = 0
            moves_in = order.picking_ids.filtered(
                lambda p: p.location_dest_id == self.location_id and (
                    p.location_id != self.location_id))
            lines_moves_in = moves_in.mapped('move_line_ids').filtered(
                lambda l: l.product_id == line.product_id)
            qty_available_01 = sum([line.qty_done for line in lines_moves_in])
            moves_out = order.picking_ids.filtered(
                lambda p: p.location_id == self.location_id and (
                    p.location_dest_id != self.location_id))
            lines_moves_out = moves_out.mapped('move_line_ids').filtered(
                lambda l: l.product_id == line.product_id)
            qty_available_02 = sum([line.qty_done for line in lines_moves_out])
            wizard_line = (
                self.env['stock.picking.return.supplier.line'].browse(
                    line_ref))
            self.env['stock.picking.return.supplier.line.confirm'].create({
                'wizard_id': self.id,
                'picking_id': line.picking_id.id,
                'product_id': line.product_id.id,
                'wizard_line': wizard_line.id,
                'qty_available': qty_available_01 - qty_available_02,
                'move_id': line.move_id.id,
                'line_ref': line_ref,
            })

    def add_stock_moves_to_confirm_lines(self, lines, line_ref):
        for line in lines:
            qty_available_01 = 0
            qty_available_02 = 0
            if line.purchase_line_id:
                moves_in = line.purchase_line_id.order_id.picking_ids.filtered(
                    lambda p: p.location_dest_id == self.location_id and (
                        p.location_id != self.location_id))
                lines_moves_in = moves_in.mapped('move_line_ids').filtered(
                    lambda l: l.product_id == line.product_id)
                qty_available_01 = sum(
                    [line.qty_done for line in lines_moves_in])
                moves_out = (
                    line.purchase_line_id.order_id.picking_ids.filtered(
                        lambda p: p.location_id == self.location_id and (
                            p.location_dest_id != self.location_id)))
                lines_moves_out = moves_out.mapped('move_line_ids').filtered(
                    lambda l: l.product_id == line.product_id)
                qty_available_02 = sum(
                    [line.qty_done for line in lines_moves_out])
            elif line.sale_id:
                moves_in = line.sale_line_id.order_id.picking_ids.filtered(
                    lambda p: p.location_dest_id == self.location_id and (
                        p.location_id != self.location_id))
                lines_moves_in = moves_in.mapped('move_line_ids').filtered(
                    lambda l: l.product_id == line.product_id)
                qty_available_01 = sum(
                    [line.qty_done for line in lines_moves_in])
                moves_out = line.sale_line_id.order_id.picking_ids.filtered(
                    lambda p: p.location_id == self.location_id and (
                        p.location_dest_id != self.location_id))
                lines_moves_out = moves_out.mapped('move_line_ids').filtered(
                    lambda l: l.product_id == line.product_id)
                qty_available_02 = sum(
                    [line.qty_done for line in lines_moves_out])
            wizard_line = (
                self.env['stock.picking.return.supplier.line'].browse(
                    line_ref))
            self.env['stock.picking.return.supplier.line.confirm'].create({
                'wizard_id': self.id,
                'picking_id': line.picking_id.id,
                'product_id': line.product_id.id,
                'move_id': line.id,
                'line_ref': line_ref,
                'wizard_line': wizard_line.id,
                'qty_available': qty_available_01 - qty_available_02,
            })

    def check_picking_quantities(self):
        for line in self.confirm_line_ids.filtered(
                lambda l: l.qty_request > 0):
            default_code = line.product_id.default_code
            if line.qty_request > line.qty_available:
                raise ValidationError(
                    _('The selected quantity for product [%s] exceeds '
                      'the quantity available' % default_code))

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

    def button_delete_lines(self):
        for line in self.line_ids:
            line.unlink()
        for line in self.confirm_line_ids:
            line.unlink()
        return self._reopen_view()

    def button_accept(self):
        self.ensure_one()
        self.check_picking_quantities()
        picking = self.env['stock.picking'].create({
            'partner_id': self.partner_id.id,
            'picking_type_id': self.picking_type.id,
            'location_id': self.location_id.id,
            'location_dest_id': self.location_dest_id.id,
        })
        for line in self.confirm_line_ids.filtered(
                lambda l: l.qty_request > 0):
            move_line = picking.move_lines.create({
                'name': line.product_id.name,
                'picking_id': picking.id,
                'product_id': line.product_id.id,
                'product_uom': line.product_id.uom_id.id,
                'product_uom_qty': line.qty_request,
                'location_id': self.location_id.id,
                'location_dest_id': self.location_dest_id.id,
                'origin_returned_move_id': line.move_id.id,
                'to_refund': True,
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

    def get_pickings_domain(self):
        return [
            ('state', '=', 'done'),
            ('location_dest_id', '=', self.location_id.id),
            ('partner_id', '=', self.partner_id.id),
        ]

    def button_assign(self):
        for line in self.confirm_line_ids:
            line.unlink()
        stock_picking_obj = self.env['stock.picking']
        domain = self.get_pickings_domain()
        if self.filter_by_date:
            domain.append(('date_done', '>=', self.date))
        pickings = stock_picking_obj.search(domain)
        for line in self.line_ids:
            if line.purchase_id:
                purchase_pickings = pickings.filtered(
                    lambda p: p.purchase_id == line.purchase_id)
                lines = purchase_pickings.mapped('move_line_ids').filtered(
                    lambda l: l.product_id == line.product_id)
                self.add_stock_move_lines_to_confirm_lines_resume(
                    lines, line.purchase_id, line.id)
                continue
            if line.sale_id:
                sale_pickings = pickings.filtered(
                    lambda p: p.sale_id == line.sale_id)
                lines = sale_pickings.mapped('move_line_ids').filtered(
                    lambda l: l.product_id == line.product_id)
                self.add_stock_move_lines_to_confirm_lines_resume(
                    lines, line.sale_id, line.id)
                continue
            lines = pickings.mapped('move_lines').filtered(
                lambda m: m.product_id == line.product_id and (
                    m.sale_line_id.order_id.partner_id == line.partner_id))
            self.add_stock_moves_to_confirm_lines(lines, line.id)
        return self._reopen_view()


class StockPickingReturnSupplierLine(models.TransientModel):
    _name = 'stock.picking.return.supplier.line'
    _description = 'Wizard lines'

    wizard_id = fields.Many2one(
        comodel_name='stock.picking.return.supplier',
        string='Wizard'
    )
    product_id = fields.Many2one(
        comodel_name='product.product',
        string='Product',
    )
    partner_id = fields.Many2one(
        comodel_name='res.partner',
        string='Partner',
    )
    sale_id = fields.Many2one(
        comodel_name='sale.order',
        string='Sale',
    )
    purchase_id = fields.Many2one(
        comodel_name='purchase.order',
        string='Purchase',
    )


class StockPickingReturnSupplierLineConfirm(models.TransientModel):
    _name = 'stock.picking.return.supplier.line.confirm'
    _description = 'Wizard confirm lines'

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
    qty_request = fields.Integer(
        string='Quantity request',
    )
    qty_available = fields.Integer(
        string='Quantity available',
    )
    move_id = fields.Many2one(
        comodel_name='stock.move',
        string='Stock move',
    )
    wizard_line = fields.Many2one(
        comodel_name='stock.picking.return.supplier.line',
    )
    line_ref = fields.Integer(
        string='Line reference',
    )
