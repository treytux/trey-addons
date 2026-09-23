################################################################################
# For copyright and license notices, see __manifest__.py file in root directory
################################################################################
from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class SaleProductReserve(models.TransientModel):
    _name = 'sale.product.reserve'
    _description = 'Wizard to reserve products from sale order'

    def _get_default_picking_type(self):
        user = self.env.user
        picking_types = self.env['stock.picking.type'].search([
            ('code', '=', 'internal'),
            '|',
            ('warehouse_id', '=', False),
            '|',
            ('warehouse_id.company_id', '=', False),
            ('warehouse_id.company_id', 'child_of', [user.company_id.id])
        ])
        if picking_types:
            return picking_types[0]

    sale_id = fields.Many2one(
        comodel_name='sale.order',
        string='Sale',
    )
    location_src_id = fields.Many2one(
        comodel_name='stock.location',
        string='Location origin',
        required=True,
    )
    location_dest_id = fields.Many2one(
        comodel_name='stock.location',
        string='Location destination',
        domain='[("reserve_products_location", "=", True)]',
        required=True,
    )
    picking_type = fields.Many2one(
        comodel_name='stock.picking.type',
        string='Picking type',
        default=_get_default_picking_type,
        required=True,
    )
    line_ids = fields.One2many(
        comodel_name='sale.product.reserve.line',
        inverse_name='wizard_id',
        string='Wizard lines',
    )
    step = fields.Integer(
        string='Step',
    )
    msg_line_ids = fields.One2many(
        comodel_name='sale.product.reserve.line.msg',
        inverse_name='wizard_id',
        string='Wizard lines with messages',
    )

    @api.model
    def default_get(self, fields):
        res = super().default_get(fields)
        if 'line_ids' not in res:
            res['line_ids'] = []
        if 'msg_line_ids' not in res:
            res['msg_line_ids'] = []
        sale = self.env['sale.order'].browse(
            self.env.context.get('active_ids', []))
        lines = self.env['sale.product.reserve.line']
        sale_lines = sale.order_line.filtered(
            lambda sl: sl.product_id.tracking != 'none')
        res['step'] = 1 if sale_lines else 2
        location_src = self.env.user.company_id.location_reserve_default
        res['location_src_id'] = location_src.id
        line_msg_obj = self.env['sale.product.reserve.line.msg']
        lines_msg = self.env['sale.product.reserve.line.msg']
        for line in sale_lines:
            lot_list = []
            quants = self.env['stock.quant'].search([
                '|',
                ('company_id', '=', self.env.user.company_id.id),
                ('company_id', '=', False),
                ('location_id', 'child_of', location_src.id),
                ('product_id', '=', line.product_id.id),
                ('lot_id', '!=', False),
                ('quantity', '>', 0),
            ])
            quants = quants.filtered(
                lambda q: q.location_id.usage == 'internal')
            lots_selected = []
            for quant in quants:
                if quant.quantity - quant.reserved_quantity <= 0:
                    continue
                vals = {}
                vals.update({
                    'lot_id': quant.lot_id,
                    'qty': quant.quantity - quant.reserved_quantity,
                    'location_id': quant.location_id,
                })
                lot_list.append(vals)
                lots_selected.append(quant.lot_id.id)
            for _index in range(int(line.product_uom_qty)):
                line_data = {
                    'wizard_id': self.id,
                    'product_id': line.product_id.id,
                    'lots_selected': [(6, 0, lots_selected)],
                }
                if lot_list:
                    line_data.update({
                        'lot_id': lot_list[0]['lot_id'].id,
                        'location_id': lot_list[0]['location_id'].id,
                    })
                    lot_list[0]['qty'] = lot_list[0]['qty'] - 1
                    if lot_list[0]['qty'] < 1:
                        lot_list.pop(0)
                else:
                    msg = _('Not enough stock of product %s at location %s') % (
                        line.product_id.name, location_src.name)
                    msg_vals = {
                        'wizard_id': self.id,
                        'name': msg,
                    }
                    lines_msg |= line_msg_obj.create(msg_vals)
                lines |= lines.create(line_data)
        res.update({
            'line_ids': [(6, 0, lines.ids)],
            'sale_id': sale.id,
            'msg_line_ids': [(6, 0, lines_msg.ids)],
        })
        location_reserve = self.env['stock.location'].search([
            ('company_id', '=', self.env.user.company_id.id),
            ('active', '=', True),
            ('reserve_products_location', '=', True),
        ], limit=1)
        if location_reserve:
            res.update({
                'location_dest_id': location_reserve.id,
            })
        return res

    def check_product_lots(self):
        for line in self.line_ids:
            if not line.lot_id:
                continue
            if line.lot_id.product_id != line.product_id:
                raise ValidationError(
                    _('The lot %s not belong to product %s') % (
                        line.lot_id.name, line.product_id.name))
            qty_available = self.env['stock.quant']._get_available_quantity(
                line.product_id, line.location_id, line.lot_id)
            if qty_available < 1:
                raise ValidationError(
                    _('There is no stock of lot %s in location %s.') % (
                        line.lot_id.name, self.location_src_id.name))
        return True

    def button_create_internal_picking_reserve(self):
        self.check_product_lots()
        picking = self.env['stock.picking'].create({
            'partner_id': self.sale_id.partner_id.id,
            'picking_type_id': self.picking_type.id,
            'location_id': self.location_src_id.id,
            'location_dest_id': self.location_dest_id.id,
            'customer_reservation': True,
            'sale_reservation': self.sale_id.id,
        })
        msg = _('Picking to reserve products from sales order %s') % (
            self.sale_id.name)
        picking.message_post(body=msg)
        move_obj = self.env['stock.move']
        sale_lines = self.sale_id.order_line.filtered(
            lambda sl: sl.product_id.tracking != 'none')
        for line in sale_lines:
            lines_lot = self.line_ids.filtered(
                lambda ln: ln.product_id == line.product_id and ln.lot_id)
            if not lines_lot:
                continue
            move_obj.create({
                'name': line.product_id.name,
                'origin': line.product_id.default_code,
                'product_id': line.product_id.id,
                'product_uom': line.product_id.uom_id.id,
                'product_uom_qty': len(lines_lot),
                'picking_id': picking.id,
                'location_id': self.location_src_id.id,
                'location_dest_id': self.location_dest_id.id,
            })
        picking.action_confirm()
        for move in picking.move_lines:
            lines = self.line_ids.filtered(
                lambda ln: ln.product_id == move.product_id and ln.lot_id)
            for line in lines:
                qty_available = self.env['stock.quant']._get_available_quantity(
                    line.product_id, line.location_id, line.lot_id)
                move._update_reserved_quantity(
                    1, qty_available, line.location_id,
                    lot_id=line.lot_id, strict=False)
        picking.action_assign()
        self.sale_id.write({
            'reservation_picking_ids': [(4, picking.id)],
            'customer_reservation': True,
        })
        if picking.state != 'assigned':
            raise ValidationError(
                _('The new internal picking could not be reserved'))
        return picking


class SaleProductReserveLine(models.TransientModel):
    _name = 'sale.product.reserve.line'
    _description = 'Wizard lines'

    wizard_id = fields.Many2one(
        comodel_name='sale.product.reserve',
        string='Wizard',
    )
    product_id = fields.Many2one(
        comodel_name='product.product',
        string='Product',
        required=True,
    )
    lot_id = fields.Many2one(
        comodel_name='stock.production.lot',
        string='Lot',
        domain='[("product_id", "=", product_id), ("id", "in", lots_selected)]',
    )
    location_id = fields.Many2one(
        comodel_name='stock.location',
        string='Location',
    )
    lots_selected = fields.Many2many(
        comodel_name='stock.production.lot',
        relation='stock_production_lot2sale_reserve_line_rel',
        column1='lot_id',
        column2='wizard_line_id',
        string='Lots allowed',
    )

    @api.onchange('lot_id')
    def onchange_lot_id(self):
        quants = self.env['stock.quant'].search([
            '|',
            ('company_id', '=', self.env.user.company_id.id),
            ('company_id', '=', False),
            ('location_id', 'child_of', self.wizard_id.location_src_id.id),
            ('lot_id', '=', self.lot_id.id),
            ('quantity', '>', 0),
        ])
        quants = quants.filtered(lambda q: q.location_id.usage == 'internal')
        if quants:
            self.location_id = quants[0].location_id.id


class SaleProductReserveLineMsg(models.TransientModel):
    _name = 'sale.product.reserve.line.msg'
    _description = 'Wizard lines with messages'

    wizard_id = fields.Many2one(
        comodel_name='sale.product.reserve',
        string='Wizard',
    )
    name = fields.Char(
        string='Message',
    )
