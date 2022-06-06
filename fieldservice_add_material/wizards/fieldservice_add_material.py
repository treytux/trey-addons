###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import _, api, fields, models
from odoo.exceptions import UserError


class FieldserviceAddMaterial(models.TransientModel):
    _name = 'fieldservice.add_material'
    _description = 'Wizard add material'

    name = fields.Char(
        string='Empty',
    )
    line_ids = fields.One2many(
        comodel_name='fieldservice.add_material.line',
        inverse_name='wizard_id',
        string='Lines',
    )

    @api.model
    def default_get(self, fields):
        res = super().default_get(fields)
        if not self.env.context.get('active_id'):
            raise UserError(_(
                'This wizard must be launched from fieldservice order record.'))
        fsm_order = self.env['fsm.order'].browse(self.env.context['active_id'])
        stock_moves = fsm_order.mapped('move_internal_ids').filtered(
            lambda m: m.state != 'cancel')
        if fsm_order.base_stock_already_delivered or not stock_moves:
            return res
        lines = self.env['fieldservice.add_material.line']
        for move in stock_moves:
            lines |= lines.create({
                'move_id': move.id,
                'product_id': move.product_id.id,
                'quantity_available': move.product_uom_qty,
                'product_uom_id': move.product_id.uom_id.id,
            })
        res.update({
            'line_ids': [(6, 0, lines.ids)],
        })
        return res

    def get_location_src_id(self, fsm_order):
        return fsm_order.warehouse_id.lot_stock_id.id

    def get_location_dest_id(self, fsm_order):
        return self.env.ref('stock.stock_location_customers').id

    def create_sale(self, fsm_order, lines_invoiced):
        sale_original = fsm_order.sale_line_id.order_id or fsm_order.sale_id
        sale = self.env['sale.order'].create({
            'partner_id': fsm_order.sale_id.partner_id.id,
            'warehouse_id': fsm_order.warehouse_id.id,
            'fsm_location_id': sale_original.fsm_location_id.id,
            'order_line': [
                (0, 0, data) for k, data in lines_invoiced.items()
            ],
        })
        sale.action_confirm()
        for move in sale.picking_ids.mapped('move_lines'):
            move.quantity_done = move.product_uom_qty
        sale.picking_ids.action_done()
        sale.message_post_with_view(
            'mail.message_origin_link',
            values={'self': sale, 'origin': fsm_order},
            subtype_id=self.env.ref('mail.mt_note').id)
        fsm_order_msg = _(
            '''This fieldservice order has created sale: <a href=
               # data-oe-model=sale.order data-oe-id=%d>%s</a>
            ''') % (sale.id, sale.name)
        fsm_order.message_post(body=fsm_order_msg)
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
            'domain': [('id', 'in', sale.ids)],
        }

    def create_picking(self, fsm_order, lines_not_invoiced):
        picking_type_out = self.env.ref('stock.picking_type_out')
        picking = self.env['stock.picking'].create({
            'picking_type_id': picking_type_out.id,
            'partner_id': fsm_order.sale_id.partner_id.id,
            'location_id': self.get_location_src_id(fsm_order),
            'location_dest_id': self.get_location_dest_id(fsm_order),
            'origin': fsm_order.name,
            'fsm_order_id': fsm_order.id,
            'move_lines': [
                (0, 0, data) for k, data in lines_not_invoiced.items()
            ]
        })
        for move in picking.mapped('move_lines'):
            move.quantity_done = move.product_uom_qty
        picking.action_done()
        picking.message_post_with_view(
            'mail.message_origin_link',
            values={'self': picking, 'origin': fsm_order},
            subtype_id=self.env.ref('mail.mt_note').id)
        fsm_order_msg = _(
            '''This fieldservice order has created picking: <a href=
               # data-oe-model=stock.picking data-oe-id=%d>%s</a>
            ''') % (picking.id, picking.name)
        fsm_order.message_post(body=fsm_order_msg)
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
            'domain': [('id', 'in', picking.ids)],
        }

    def button_accept(self):
        self.ensure_one()
        fsm_order = self.env['fsm.order'].browse(
            self.env.context.get('active_id', []))
        lines_invoiced = {}
        lines_not_invoiced = {}
        rounding_method = self._context.get('rounding_method', 'UP')
        if self.line_ids.filtered(lambda l: l.product_qty < 0):
            raise UserError(_('The amounts must be positive.'))
        if len(self.line_ids) != len(self.line_ids.mapped('product_id')):
            raise UserError(_('There are duplicated products in wizard lines!'))
        fsm_order_msg = _('Products delivered to customer location:<br>')
        lines_with_qty = self.line_ids.filtered(lambda l: l.product_qty > 0)
        if not lines_with_qty:
            return
        for line in lines_with_qty:
            fsm_order_msg += '&nbsp;&nbsp;<b>%s : %s</b><br>' % (
                line.product_id.name, line.product_qty)
            move_out = fsm_order.move_ids.filtered(
                lambda m: m.state not in ['done', 'cancel']
                and m.product_id == line.product_id)
            if move_out:
                move_out.reserved_availability += line.product_qty
                move_out.quantity_done += line.product_qty
                picking_out = move_out.picking_id
                picking_msg = _(
                    '''This picking has been updated from fieldservice order:
                       <a href=# data-oe-model=fsm.order data-oe-id=%d>%s</a>
                    ''') % (fsm_order.id, fsm_order.name)
                picking_out.message_post(body=picking_msg)
                if all([
                    move.quantity_done >= move.product_uom_qty
                    for move in picking_out.move_lines
                ]):
                    picking_out.action_done()
                continue
            qty = line.product_uom_id._compute_quantity(
                line.product_qty, line.product_id.uom_id,
                rounding_method=rounding_method)
            if line.is_invoiced:
                lines_invoiced[line.id] = {
                    'product_id': line.product_id.id,
                    'product_uom_qty': qty,
                }
            else:
                lines_not_invoiced[line.id] = {
                    'product_id': line.product_id.id,
                    'name': line.product_id.name,
                    'product_uom': line.product_id.uom_id.id,
                    'product_uom_qty': qty,
                }
        if lines_invoiced:
            self.create_sale(fsm_order, lines_invoiced)
        if lines_not_invoiced:
            self.create_picking(fsm_order, lines_not_invoiced)
        form_view = self.env.ref(
            'fieldservice_add_material.fieldservice_add_material_ok')
        fsm_order.message_post(body=fsm_order_msg)
        fsm_order.base_stock_already_delivered = True
        return {
            'name': _('Add material'),
            'res_model': 'fieldservice.add_material',
            'type': 'ir.actions.act_window',
            'views': [(form_view.id, 'form')],
            'view_mode': 'form',
            'view_type': 'form',
            'target': 'new',
        }


class FieldserviceAddMaterialLine(models.TransientModel):
    _name = 'fieldservice.add_material.line'
    _description = 'Wizard lines'

    name = fields.Char(
        string='Empty',
    )
    wizard_id = fields.Many2one(
        comodel_name='fieldservice.add_material',
        string='Wizard',
        ondelete='cascade',
    )
    product_id = fields.Many2one(
        comodel_name='product.product',
        string='Product',
        domain='[("type", "=", "product")]',
        required=True,
    )
    quantity_available = fields.Float(
        string='Available quantity',
        readonly=True,
    )
    product_qty = fields.Float(
        string='Applied quantity',
    )
    uom_category_id = fields.Many2one(
        related='product_id.uom_id.category_id',
    )
    product_uom_id = fields.Many2one(
        comodel_name='uom.uom',
        string='Unit of measure',
        domain='[("category_id", "=", uom_category_id)]',
        required=True,
    )
    is_invoiced = fields.Boolean(
        string='Is invoiced',
    )
    move_id = fields.Many2one(
        comodel_name='stock.move',
        string='Stock move',
        readonly=True,
    )

    @api.onchange('product_id')
    def onchange_product_id(self):
        fsm_order = self.env['fsm.order'].browse(
            self.env.context.get('active_id', []))
        location_id = self.wizard_id.get_location_src_id(fsm_order)
        for line in self:
            line.product_uom_id = (
                line.product_id and line.product_id.uom_id.id or False)
            line.quantity_available = (
                line.product_id and line.product_id.with_context(
                    location=location_id).qty_available)
