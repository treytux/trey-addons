###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import _, api, exceptions, fields, models
from odoo.exceptions import UserError


class StockDeposit(models.TransientModel):
    _name = 'stock.deposit'
    _description = 'Move stock a deposit location'

    name = fields.Char(
        string='Empty',
    )
    line_ids = fields.One2many(
        comodel_name='stock.deposit.line',
        inverse_name='deposit_id',
        string='Deposit',
    )
    ttype = fields.Selection(
        selection=[
            ('sale', 'Sale'),
        ],
        string='Type',
        default='sale',
        required=True,
    )
    partner_id = fields.Many2one(
        comodel_name='res.partner',
        string='Partner',
        required=True,
        help="Partner's shipping address",
        domain="[('type', '=', 'delivery')]",
    )
    location_id = fields.Many2one(
        comodel_name='stock.location',
        string='Location',
        required=True,
    )
    warehouse_id = fields.Many2one(
        comodel_name='stock.warehouse',
        string='Warehouse',
        required=True,
    )
    price_option = fields.Selection(
        selection=[
            ('real_fifo', 'Price from quotation (FIFO)'),
            ('last_price', 'Last price'),
        ],
        string='Price option',
        required=True,
        default='real_fifo',
        help='Indicates how to calculate the price:\n'
        '\t- "Price from quotation (FIFO)": the price is obtained from the '
        'sales line and, if there is no associated sales line, the sales '
        'price of the product form is assigned (price with pricelist applied).'
        '\n\t- "Last price": the price is obtained from the last confirmed '
        'sales line for that customer and, if there is no sales line, the '
        'sales price of the product form (price with pricelist applied) is '
        'assigned.'
    )
    location_src_id = fields.Many2one(
        comodel_name='stock.location',
        string='Location source',
        compute='_compute_location',
    )
    location_dst_id = fields.Many2one(
        comodel_name='stock.location',
        string='Location destination',
        compute='_compute_location',
    )
    create_invoice = fields.Boolean(
        string='Create invoice',
        default=True,
        help='If this option is selected, the invoice corresponding to the '
             'movements made will be generated. If it is not selected, you '
             'must generate it manually later from the sales order.'
    )

    @api.depends('ttype', 'location_id')
    def _compute_location(self):
        customer_location = self.env.ref('stock.stock_location_customers')
        for wizard in self:
            if not wizard.ttype or not wizard.location_id:
                wizard.location_src_id = False
                wizard.location_dst_id = False
            elif wizard.ttype == 'sale':
                wizard.location_src_id = wizard.location_id.id
                wizard.location_dst_id = customer_location.id

    @api.onchange('partner_id')
    def onchange_partner_id(self):
        if self.partner_id:
            customer_location = self.partner_id.property_stock_customer
            return {
                'domain': {
                    'location_id': [('id', '=', customer_location.id)],
                },
                'value': {
                    'location_id': customer_location.id,
                }
            }

    @api.onchange('location_id')
    def onchange_location_id(self):
        if self.location_id:
            warehouses = self.env['stock.warehouse'].search([
                ('deposit_parent_id', '=', self.location_id.location_id.id),
            ])
            warehouse_id = (
                warehouses and warehouses[0] and warehouses[0].id or None)
            return {
                'domain': {
                    'warehouse_id': [('id', 'in', warehouses.ids)],
                },
                'value': {
                    'warehouse_id': warehouse_id,
                }
            }

    def get_price(self, price_option, sale_line, product, partner):
        price = product.with_context(
            pricelist=partner.property_product_pricelist.id).price
        if price_option == 'real_fifo':
            if sale_line:
                return sale_line.price_unit
            return price
        elif price_option == 'last_price':
            sql = '''
                SELECT sol.id
                FROM sale_order_line AS sol
                LEFT JOIN sale_order AS so ON sol.order_id = so.id
                WHERE
                    sol.state = 'sale'
                    AND so.partner_shipping_id = %s
                    AND sol.product_id = %s
                ORDER BY so.confirmation_date DESC, id DESC
                LIMIT 1
            ''' % (self.partner_id.id, product.id)
            self.env.cr.execute(sql)
            line_ids = self.env.cr.fetchall()
            if line_ids:
                return self.env['sale.order.line'].browse(
                    line_ids[0][0]).price_unit
        else:
            raise UserError(_('Price option unknown!'))
        return price

    def create_inventory(self, location, product, quantity):
        theorical_qty = product.with_context(
            location=location.id).qty_available
        inventory = self.env['stock.inventory'].create({
            'name': _('%s from move stock deposit wizard') % product.display_name,
            'filter': 'product',
            'product_id': product.id,
            'location_id': location.id,
            'line_ids': [
                (0, 0, {
                    'location_id': location.id,
                    'product_id': product.id,
                    'product_uom_id': product.uom_id.id,
                    'product_qty': theorical_qty + quantity,
                }),
            ],
        })
        inventory.action_validate()
        return inventory

    def create_picking(self):
        return self.env['stock.picking'].create({
            'partner_id': self.partner_id.id,
            'picking_type_id': self.warehouse_id.int_type_id.id,
            'location_id': self.location_src_id.id,
            'location_dest_id': self.location_dst_id.id,
        })

    def transfer_picking(self, picking):
        picking.action_confirm()
        picking.action_assign()
        for move in picking.move_lines:
            move.quantity_done = move.product_uom_qty
        picking.action_done()

    def create_sale_order(self):
        order = self.env['sale.order'].create({
            'partner_id': self.partner_id.commercial_partner_id.id,
            'partner_invoice_id': self.partner_id.commercial_partner_id.id,
            'partner_shipping_id': self.partner_id.id,
            'warehouse_id': self.warehouse_id.id,
            'pricelist_id': (
                self.partner_id.property_product_pricelist
                and self.partner_id.property_product_pricelist.id
                or self.env.ref('product.list0').id),
        })
        order.onchange_partner_id()
        return order

    def create_sale_order_line(
            self, order, product, qty, discount, related_line=None):
        vline = self.env['sale.order.line'].new({
            'order_id': order.id,
            'name': product.name,
            'product_id': product.id,
            'product_uom_qty': qty,
            'product_uom': product.uom_id.id,
            'discount': discount,
            'tax_id': [(6, 0, [product.taxes_id.id])],
        })
        vline.product_id_change()
        vline.price_unit = self.get_price(
            self.price_option, related_line, product, order.partner_id)
        return self.env['sale.order.line'].create(
            vline._convert_to_write(vline._cache))

    def join_order_lines(self, sale):
        lines_joined = []
        lines2delete = []
        for line in sale.order_line:
            lines2join = sale.order_line.filtered(
                lambda ln: ln.id != line.id
                and ln.product_id == line.product_id
                and ln.price_unit == line.price_unit
                and ln.discount == line.discount
                and ln.tax_id == line.tax_id
                and ln not in lines_joined
                and ln not in lines2delete
            )
            for line2join in lines2join:
                line.product_uom_qty += line2join.product_uom_qty
                lines_joined.append(line)
                lines2delete.append(line2join)
        [ln.unlink() for ln in lines2delete]

    def action_confirm(self):
        self.ensure_one()
        self.line_ids.check_qty_sale()
        self.line_ids.compute_moves()
        invoice = False
        sale = False
        for wiz_line in self.line_ids:
            sale_lines = wiz_line.move_ids.mapped('sale_line_id')
            rest_qty = wiz_line.qty_sale
            sale_line = self.env['sale.order.line']
            for sale_line in sale_lines:
                qty = (
                    rest_qty - sale_line.product_uom_qty < 0
                    and rest_qty or sale_line.product_uom_qty)
                if not sale:
                    sale = self.create_sale_order()
                self.create_sale_order_line(
                    sale, wiz_line.product_id, qty, sale_line.discount,
                    sale_line)
                rest_qty -= sale_line.product_uom_qty
                if rest_qty <= 0:
                    break
            if rest_qty > 0:
                qty_sales = (
                    sale_lines and sum(sale_lines.mapped('product_uom_qty'))
                    or 0)
                qty_available = (
                    sale_line and sale_line.product_id.with_context(
                        location=self.location_src_id.id).qty_available
                    or wiz_line.product_id.with_context(
                        location=self.location_src_id.id).qty_available)
                if qty_available - qty_sales - rest_qty < 0:
                    self.create_inventory(
                        self.location_src_id, wiz_line.product_id, rest_qty)
                if not sale:
                    sale = self.create_sale_order()
                self.create_sale_order_line(
                    sale, wiz_line.product_id, rest_qty, 0)
        if not sale:
            view = self.env.ref('stock_deposit.stock_deposit_no_sale_wizard')
            return {
                'type': 'ir.actions.act_window',
                'res_model': 'stock.deposit',
                'view_type': 'form',
                'view_mode': 'form',
                'views': [(view.id, 'form')],
                'target': 'new',
            }
        if sale:
            self.join_order_lines(sale)
            sale.action_confirm()
            sale.picking_ids.write({
                'location_id': self.location_src_id.id,
                'location_dest_id': self.location_dst_id.id,
            })
            for move in sale.picking_ids.move_lines:
                move.write({
                    'quantity_done': move.sale_line_id.product_uom_qty,
                    'location_id': self.location_src_id.id,
                    'location_dest_id': self.location_dst_id.id,
                })
                move.move_line_ids.write({
                    'location_id': self.location_src_id.id,
                    'location_dest_id': self.location_dst_id.id,
                })
            sale.picking_ids.action_done()
            if self.create_invoice:
                if not invoice:
                    invoice = self.env['account.invoice'].create(
                        sale._prepare_invoice())
                for sale_line in sale.order_line:
                    sale_line.invoice_line_create(
                        invoice.id, sale_line.product_uom_qty)
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


class StockDepositLine(models.TransientModel):
    _name = 'stock.deposit.line'
    _description = 'Move stock a deposit location'

    name = fields.Char(
        string='Empty',
    )
    deposit_id = fields.Many2one(
        comodel_name='stock.deposit',
        string='Deposit',
        required=True,
    )
    product_id = fields.Many2one(
        comodel_name='product.product',
        string='Product',
        required=True,
    )
    qty_theorical = fields.Float(
        string='Qty theorical',
        compute='_compute_qty_theorical',
        store=True
    )
    qty_real = fields.Float(
        string='Qty real',
    )
    qty_sale = fields.Float(
        string='Qty sale',
    )
    move_ids = fields.Many2many(
        comodel_name='stock.move',
        relation='deposit_line2stock_move_rel',
        column1='deposit_line_id',
        column2='move_id',
    )
    force_inventory = fields.Boolean(
        string='Force inventory adjustment',
        help='You must check this field when there is not enough stock for '
             'the line to validate that the wizard creates an inventory '
             'adjustment.'
    )

    @api.depends('product_id')
    def _compute_qty_theorical(self):
        for line in self:
            if not line.product_id:
                continue
            line.qty_theorical = line.product_id.with_context(
                location=line.deposit_id.location_id.id).qty_available
            line.qty_real = 0
            line.qty_sale = 0

    @api.onchange('qty_sale')
    def onchange_qty_sale(self):
        self.qty_real = self.qty_theorical - self.qty_sale

    @api.onchange('qty_real')
    def onchange_qty_real(self):
        self.qty_sale = self.qty_theorical - self.qty_real

    def check_qty_sale(self):
        lines_without_stock = []
        for line in self:
            if line.qty_sale > line.qty_theorical and not line.force_inventory:
                lines_without_stock.append(line)
        if not lines_without_stock:
            return True
        msg = _(
            'You are trying to move more quantity than you currently have '
            'in stock.'
        )
        for line in lines_without_stock:
            msg += _(
                '\n\n\t- Product \'%s\': you have \'%s\' and you want move '
                '\'%s\'.') % (
                    line.product_id.default_code, line.qty_theorical,
                    line.qty_sale)
        msg += _(
            '\n\nIf you confirm this operation, a stock readjustment will be '
            'created but first you must mark the field "Force inventory '
            'adjustment".')

        raise exceptions.Warning(msg)

    def compute_moves(self):
        move_obj = self.env['stock.move']
        for line in self:
            domain = [
                ('product_id', '=', line.product_id.id),
                ('location_dest_id', '=', line.deposit_id.location_src_id.id),
                ('state', '=', 'done'),
                ('invoice_line_ids', '!=', None),
                ('sale_line_id', '!=', None),
            ]
            qty = line.qty_sale
            for move in move_obj.search(domain, order='id desc'):
                if qty <= 0:
                    break
                line.move_ids = [(4, move.id)]
                qty -= move.product_uom_qty
