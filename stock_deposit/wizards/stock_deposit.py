###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
import copy

from odoo import _, api, exceptions, fields, models
from odoo.exceptions import UserError, ValidationError


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
    partner_id = fields.Many2one(
        comodel_name='res.partner',
        string='Partner',
        required=True,
        help='Partner\'s shipping address',
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
        'assigned.',
    )
    create_invoice = fields.Boolean(
        string='Create invoice',
        default=True,
        help='If this option is selected, the invoice corresponding to the '
             'movements made will be generated. If it is not selected, you '
             'must generate it manually later from the sales order.',
    )

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

    def action_confirm(self):
        self.ensure_one()
        if self.line_ids.filtered(lambda ln: ln.qty_finish < 0):
            raise UserError(_(
                'You have at least one line marked in red because the actual '
                'quantity is negative. If you want to keep it, you must check '
                'the option "Inventory adjustment" in these lines.'))
        self.line_ids.check_qty()
        self.line_ids.compute_moves()
        invoice = False
        sale = False
        sale_inventory = False
        sales = []
        picking_return_customer = False
        picking_return_stock = False
        picking_return_customer_stock_customer = False
        picking_return_customer_stock_stock = False
        pickings_to_transfer = []
        for line in self.line_ids:
            sale_lines = line.move_ids.mapped('sale_line_id')
            if line.ttype == 'sale':
                partial_sale, partial_sales, do_continue = (
                    self.process_line_sale(line, sale_lines, sale))
                sale = partial_sale
                sales.extend(partial_sales)
                if do_continue:
                    continue
            elif line.ttype == 'inventory':
                partial_sale, partial_sales = self.process_line_inventory(
                    line, sale_lines, sale_inventory)
                sale_inventory = partial_sale
                sales.extend(partial_sales)
            elif line.ttype == 'sale_return_customer':
                picking_return_customer, partial_pickings_to_transfer = (
                    self.process_line_sale_return_customer(
                        line, sale_lines, picking_return_customer))
                pickings_to_transfer.extend(partial_pickings_to_transfer)
                sale_line = sale_lines[0]
            elif line.ttype == 'sale_return_stock':
                picking_return_stock, partial_pickings_to_transfer = (
                    self.process_line_sale_return_stock(
                        line, sale_lines, picking_return_stock))
                pickings_to_transfer.extend(partial_pickings_to_transfer)
            elif line.ttype == 'sale_return_customer_stock':
                picking_return_customer, picking_return_stock,\
                    partial_pickings_to_transfer = (
                        self.process_line_return_customer_stock(
                            line, sale_lines,
                            picking_return_customer_stock_customer,
                            picking_return_customer_stock_stock))
                pickings_to_transfer.extend(partial_pickings_to_transfer)
                sale_line = sale_lines[0]
        for picking in pickings_to_transfer:
            self.transfer_picking(picking)
        if picking_return_customer:
            sale_original = sale_line.order_id
            if self.create_invoice and sale_lines[0].qty_invoiced > 0:
                sale_original.action_invoice_create(final=True)
        if picking_return_customer_stock_customer:
            sale_original = sale_line.order_id
            if self.create_invoice and sale_lines[0].qty_invoiced > 0:
                sale_original.action_invoice_create(final=True)
        if not sales:
            view = self.env.ref('stock_deposit.stock_deposit_no_sale_wizard')
            return {
                'type': 'ir.actions.act_window',
                'res_model': 'stock.deposit',
                'view_type': 'form',
                'view_mode': 'form',
                'views': [(view.id, 'form')],
                'target': 'new',
            }
        else:
            for sale in sales:
                self.join_order_lines(sale)
                sale.action_confirm()
                if self.create_invoice:
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

    def process_line_sale(self, line, sale_lines, sale):
        sales = []
        rest_qty = line.qty
        sale_line = self.env['sale.order.line']
        fake_moves = []
        for sale_line in sale_lines:
            lines = self.env['stock.deposit.line'].get_lines(line)
            lines += fake_moves
            process_lines = line.pending(lines)
            qty_available_pos = [ln[1] for ln in process_lines if ln[1] > 0]
            qty_available = qty_available_pos and qty_available_pos[0] or 0
            qty = rest_qty - qty_available < 0 and rest_qty or qty_available
            if not sale:
                sale = self.create_sale_order(line.ttype)
                sales.append(sale)
            self.create_sale_order_line(
                sale, line.product_id, qty, sale_line.discount, sale_line)
            rest_qty -= qty_available
            fake_moves.append(
                [-qty, 0, 'move_sale_line_%s-%s' % (sale_line.id, line.id)])
            if rest_qty <= 0:
                break
        if rest_qty <= 0:
            return sale, sales, True
        qtys = sale_lines and sum(sale_lines.mapped('product_uom_qty')) or 0
        qty_available = (
            sale_line and sale_line.product_id.with_context(
                location=line.location_src_id.id).qty_available
            or line.product_id.with_context(
                location=line.location_src_id.id).qty_available)
        if qty_available - qtys - rest_qty < 0:
            self.create_inventory(
                line.location_src_id, line.product_id, rest_qty)
        if not sale:
            sale = self.create_sale_order(line.ttype)
            sales.append(sale)
        self.create_sale_order_line(sale, line.product_id, rest_qty, 0)
        return sale, sales, False

    def process_line_inventory(self, line, sale_lines, sale):
        sales = []
        rest_qty = line.qty
        sale_line = self.env['sale.order.line']
        if rest_qty < 0:
            if not sale:
                sale = self.create_sale_order(line.ttype)
                sales.append(sale)
            self.create_sale_order_line(sale, line.product_id, rest_qty, 0)
            return sale, sales
        for sale_line in sale_lines:
            qty_deposit = line.product_id.with_context(
                location=line.deposit_id.location_id.id).qty_available
            rest_qty = abs(qty_deposit - rest_qty)
            if rest_qty < sale_line.product_uom_qty:
                qty = rest_qty
            else:
                qty = sale_line.product_uom_qty
            if not sale:
                sale = self.create_sale_order(line.ttype)
                sales.append(sale)
            self.create_sale_order_line(
                sale, line.product_id, qty, sale_line.discount, sale_line)
            rest_qty -= qty
            if rest_qty <= 0:
                break
        if rest_qty <= 0:
            return sale, sales
        if not sale:
            sale = self.create_sale_order(line.ttype)
            sales.append(sale)
        self.create_sale_order_line(sale, line.product_id, rest_qty, 0)
        return sale, sales

    def process_line_sale_return_customer(self, line, sale_lines, picking):
        pickings_to_transfer = []
        if not sale_lines:
            raise UserError(_(
                'There are no previous order lines for product "%s" in the '
                'system.' % line.product_id.name))
        sale_line = sale_lines[0]
        if not picking:
            picking = self.create_picking_return(
                line, line.location_src_id, line.location_dst_id)
            picking.sale_id = sale_line.order_id.id
            pickings_to_transfer.append(picking)
        move = self.create_stock_move(line, picking, True)
        move.write({
            'sale_line_id': sale_line.id,
            'group_id': sale_line.order_id.procurement_group_id.id,
        })
        return picking, pickings_to_transfer

    def process_line_sale_return_stock(self, line, sale_lines, picking):
        pickings_to_transfer = []
        if not picking:
            picking = self.create_picking_return(
                line, line.location_src_id,
                line.deposit_id.warehouse_id.lot_stock_id)
            pickings_to_transfer.append(picking)
        self.create_stock_move(line, picking, False)
        return picking, pickings_to_transfer

    def process_line_return_customer_stock(
            self, line, sale_lines, picking_customer, picking_stock):
        pickings_to_transfer = []
        if not sale_lines:
            raise UserError(_(
                'There are no previous order lines for product "%s" in the '
                'system.' % line.product_id.name))
        sale_line = sale_lines[0]
        if not picking_customer:
            picking_customer = (
                self.create_picking_return(
                    line, line.location_src_id, line.deposit_id.location_id))
            pickings_to_transfer.append(picking_customer)
            picking_customer.sale_id = sale_line.order_id.id
        move = self.create_stock_move(line, picking_customer, True)
        move.write({
            'sale_line_id': sale_line.id,
            'group_id': sale_line.order_id.procurement_group_id.id,
        })
        if not picking_stock:
            picking_stock = (
                self.create_picking_return(
                    line, line.deposit_id.location_id,
                    line.deposit_id.warehouse_id.lot_stock_id))
            pickings_to_transfer.append(picking_stock)
        self.create_stock_move(line, picking_stock, False)
        return picking_customer, picking_stock, pickings_to_transfer

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
            'name': _(
                '%s from move stock deposit wizard') % product.display_name,
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

    def create_sale_order(self, ttype):
        ttype_name = dict(self.line_ids._fields['ttype'].selection).get(ttype)
        sale = self.env['sale.order'].create({
            'partner_id': self.partner_id.commercial_partner_id.id,
            'partner_invoice_id': self.partner_id.commercial_partner_id.id,
            'partner_shipping_id': self.partner_id.id,
            'warehouse_id': self.warehouse_id.id,
            'pricelist_id': (
                self.partner_id.property_product_pricelist
                and self.partner_id.property_product_pricelist.id
                or self.env.ref('product.list0').id),
            'is_sale_deposit': ttype == 'sale',
            'is_inventory_deposit': ttype == 'inventory',
            'note': _(
                'Sale order created from \'Move stock deposit\' wizard. '
                'Type: \'%s\'.' % ttype_name),
        })
        sale.onchange_partner_id()
        sale.write({
            'partner_invoice_id': self.partner_id.commercial_partner_id.id,
            'partner_shipping_id': self.partner_id.id,
        })
        return sale

    def create_sale_order_line(
            self, sale, product, qty, discount, related_line=None):
        vline = self.env['sale.order.line'].new({
            'order_id': sale.id,
            'name': product.name,
            'product_id': product.id,
            'product_uom_qty': qty,
            'product_uom': product.uom_id.id,
            'discount': discount,
            'tax_id': [(6, 0, [product.taxes_id.id])],
        })
        vline.product_id_change()
        vline.price_unit = self.get_price(
            self.price_option, related_line, product, sale.partner_id)
        return self.env['sale.order.line'].create(
            vline._convert_to_write(vline._cache))

    def create_picking_return(self, wizard_line, location_src, location_dst):
        return self.env['stock.picking'].create({
            'partner_id': self.partner_id.id,
            'picking_type_id': self.warehouse_id.int_type_id.id,
            'location_id': location_src.id,
            'location_dest_id': location_dst.id,
        })

    def create_stock_move(self, wizard_line, picking, to_refund):
        return self.env['stock.move'].create({
            'picking_id': picking.id,
            'product_id': wizard_line.product_id.id,
            'name': wizard_line.product_id.name,
            'product_uom': wizard_line.product_id.uom_id.id,
            'product_uom_qty': wizard_line.qty,
            'location_id': picking.location_id.id,
            'location_dest_id': picking.location_dest_id.id,
            'to_refund': to_refund,
        })

    def transfer_picking(self, picking):
        picking.action_confirm()
        picking.action_assign()
        for move in picking.move_lines:
            move.quantity_done = move.product_uom_qty
        picking.action_done()

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
    ttype = fields.Selection(
        selection=[
            ('sale', 'Sale'),
            ('inventory', 'Inventory'),
            ('sale_return_customer', 'Sale return customer'),
            ('sale_return_stock', 'Sale return stock'),
            ('sale_return_customer_stock', 'Sale return customer stock'),
        ],
        string='Type',
        default='sale',
        required=True,
        help='-"Sale" (deposit -> customers): generates a new sales order '
             'with the quantities to be moved from the deposit location to '
             'the "Customers" location, with its associated internal stock '
             'picking transferred. If the "Create invoice" field of the '
             'wizard is marked, the corresponding invoice is also created.\n'
             '- "Inventory": generates a new sales order with the difference '
             'between the quantities that were moved to the deposit and those '
             'that the deposit says have, it is confirmed and two internal '
             'stock pickings are generated that are automatically '
             'transferred: one that goes from the deposit from the customer '
             'to "Customers" and another that goes from "Customers" to '
             '"Inventory adjustments". If the "Create invoice" field of the '
             'wizard is marked, the corresponding invoice is also created.\n'
             '- "Return to customer" (customers -> deposit): generates a new '
             'internal stock picking from the "Customers" location to the '
             'deposit location whose stock movement is linked to the original '
             'sales order and transfers it. If the "Create invoice" field of '
             'the wizard is marked, the corresponding invoice is also '
             'created\n.'
             '- "Return to central" (deposit -> stock): generates a new '
             'internal stock picking from the deposit location to the "Stock" '
             'location and is transferred. It does not generate an invoice in '
             'any case.\n'
             '- "Return customers -> deposit -> stock" (customers -> deposit '
             '-> stock): perform the two previous operations in a single '
             'step:\n\t> "Return to customer" (customers -> deposit).\n\tand'
             '\n\t> "Return to central" (deposit -> stock).',
    )
    product_id = fields.Many2one(
        comodel_name='product.product',
        string='Product',
        required=True,
    )
    qty_theorical = fields.Float(
        string='Qty theorical',
        compute='_compute_qty_theorical',
        store=True,
        help='Indicate the quantity on hand available at the deposit '
             'location.',
    )
    qty_finish = fields.Float(
        string='Qty final',
        readonly=True,
        help='Indicates the quantity that will be in the deposit location '
             'after confirming the wizard.',
    )
    qty = fields.Float(
        string='Qty',
    )
    move_ids = fields.Many2many(
        comodel_name='stock.move',
        relation='deposit_line2stock_move_rel',
        column1='deposit_line_id',
        column2='move_id',
    )
    force_inventory = fields.Boolean(
        string='Inventory adjustment',
        help='You must check this field when there is not enough stock for '
             'the line to validate that the wizard creates an inventory '
             'adjustment.',
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

    @api.constrains('product_id')
    def check_product_id(self):
        for line in self:
            deposit_lines = self.search([
                ('id', '!=', line.id),
                ('deposit_id', '=', line.deposit_id.id),
                ('product_id', '=', line.product_id.id),
            ])
            if deposit_lines:
                raise ValidationError(_(
                    'There can only be one line for each product.'))

    @api.depends('ttype', 'deposit_id.location_id')
    def _compute_location(self):
        customer_location = self.env.ref('stock.stock_location_customers')
        inventory_location = self.env.ref('stock.location_inventory')
        for line in self:
            stock_location = line.deposit_id.warehouse_id.lot_stock_id
            if not line.ttype or not line.deposit_id.location_id:
                line.location_src_id = False
                line.location_dst_id = False
            elif line.ttype == 'sale':
                line.location_src_id = line.deposit_id.location_id.id
                line.location_dst_id = customer_location.id
            elif line.ttype == 'sale_return_customer':
                line.location_src_id = customer_location.id
                line.location_dst_id = line.deposit_id.location_id.id
            elif line.ttype == 'sale_return_stock':
                line.location_src_id = line.deposit_id.location_id.id
                line.location_dst_id = stock_location.id
            elif line.ttype == 'sale_return_customer_stock':
                line.location_src_id = customer_location.id
                line.location_dst_id = stock_location.id
            elif line.ttype == 'inventory':
                line.location_src_id = line.deposit_id.location_id.id
                line.location_dst_id = inventory_location.id

    @api.depends('product_id')
    def _compute_qty_theorical(self):
        for line in self:
            if not line.product_id:
                continue
            line.qty_theorical = line.product_id.with_context(
                location=line.deposit_id.location_id.id).qty_available
            line.qty_finish = 0
            line.qty = 0

    @api.onchange('qty', 'force_inventory')
    def onchange_qty(self):
        if self.ttype == 'sale_return_customer_stock':
            self.qty_finish = self.qty_theorical
        elif (
                self.force_inventory
                and self.ttype in ['sale', 'sale_return_stock', 'inventory']):
            self.qty_finish = 0
        else:
            if self.ttype == 'sale_return_customer':
                sign = 1
            else:
                sign = -1
            self.qty_finish = self.qty_theorical + sign * self.qty

    def check_qty(self):
        lines_without_stock = []
        for line in self:
            if line.ttype != 'sale':
                continue
            if line.qty > line.qty_theorical and not line.force_inventory:
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
                    line.qty)
        msg += _(
            '\n\nIf you confirm this operation, a stock readjustment will be '
            'created but first you must mark the field "Force inventory '
            'adjustment".')
        raise exceptions.Warning(msg)

    def pending(self, lines):
        for index, line in enumerate(lines):
            if line[0] >= 0:
                continue
            qty_to_rest = line[0]
            for to_rest in filter(lambda l: l[1] > 0, lines[:index]):
                if to_rest[1] + qty_to_rest < 0:
                    qty_to_rest = to_rest[1] + qty_to_rest
                    to_rest[1] = 0
                elif to_rest[1] + qty_to_rest >= 0:
                    to_rest[1] += qty_to_rest
                    qty_to_rest = 0
                    break
        return lines

    def get_lines(self, line):
        domain = [
            ('product_id', '=', line.product_id.id),
            '|',
            ('location_dest_id', '=', line.location_src_id.id),
            ('location_id', '=', line.location_src_id.id),
            ('state', '=', 'done'),
        ]
        if line.ttype == 'sale_return_stock':
            customer_loc = self.env.ref('stock.stock_location_customers')
            domain.append(('location_id', '!=', customer_loc.id))
        if line.deposit_id.price_option == 'real_fifo':
            order = 'id asc'
        elif line.deposit_id.price_option == 'last_price':
            order = 'id desc'
        moves = self.env['stock.move'].search(domain, order=order)
        lines = [[
            m.product_uom_qty
            * (m.location_id.id == line.location_src_id.id and -1 or 1),
            m.product_uom_qty
            * (m.location_id.id != line.location_src_id.id and 1 or 0),
            m.id] for m in moves]
        return lines

    def compute_moves(self):
        for line in self:
            if not line.location_src_id:
                raise UserError(_(
                    'The \'Location source\' field of the line must be '
                    'filled.'))
            lines = self.get_lines(line)
            lines_copied = copy.deepcopy(lines)
            lines_processed = self.pending(lines)
            move_ids = []
            qty = line.qty
            for index, ln in enumerate(lines_copied):
                if qty <= 0:
                    break
                if ln == lines_processed[index] and ln[1] > 0:
                    move_ids.append(ln[2])
                    qty -= lines_processed[index][1]
                if ln != lines_processed[index]:
                    move_ids.append(ln[2])
                    qty -= lines_processed[index][1]
            line.move_ids = [(4, move_id) for move_id in move_ids]
