###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo.exceptions import UserError
from odoo.tests.common import TransactionCase

# Important note! Install an account package


class TestSaleReturn(TransactionCase):

    def setUp(self):
        super().setUp()
        self.partner = self.env.ref('base.res_partner_3')
        self.product = self.env.ref(
            'product.product_product_3_product_template').product_variant_id
        self.inventory(9999)

    def tearDown(self):
        super().tearDown()
        self.inventory(0)

    def inventory(self, qty):
        location = self.env.ref('stock.stock_location_stock')
        inventory = self.env['stock.inventory'].create({
            'name': 'add products for tests',
            'filter': 'product',
            'location_id': location.id,
            'product_id': self.product.id,
            'exhausted': True})
        inventory.action_start()
        stock_loc = self.env.ref('stock.stock_location_stock')
        inventory.line_ids.write({
            'product_qty': qty,
            'location_id': stock_loc.id})
        inventory._action_done()

    def picking_done(self, picking):
        picking.action_confirm()
        picking.action_assign()
        for move in picking.move_lines:
            move.quantity_done = move.product_uom_qty
        picking.action_done()

    def create_sale(self, confirm_picking=True):
        sale = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'order_line': [(0, 0, {
                'product_id': self.product.id,
                'product_uom_qty': 10})]
        })
        sale.action_confirm()
        if confirm_picking:
            self.picking_done(sale.picking_ids[0])
        return sale

    def invoice_sale(self, sales, method='delivered'):
        ctx = {
            'tracking_disable': True,
            'mail_notrack': True,
            'mail_create_nolog': True,
            'active_model': 'sale.order',
            'active_ids': sales.ids,
            'active_id': sales[0].id}
        payment_obj = self.env['sale.advance.payment.inv'].with_context(ctx)
        payment = payment_obj.create({
            'advance_payment_method': method})
        payment.with_context(ctx).create_invoices()
        invoices = self.env['account.invoice']
        for sale in sales:
            invoices |= sale.invoice_ids
        return invoices.sorted(key='id')

    def test_return_location_with_changes(self):
        location = self.env.ref('stock.location_dispatch_zone')
        turn = self.env['sale.order'].create({
            'is_return': True,
            'partner_id': self.partner.id,
            'order_line': [(0, 0, {
                'product_id': self.product.id,
                'location_id': location.id,
                'price_unit': 33.33,
                'qty_change': 2,
                'product_uom_qty': 3})]
        })
        self.assertEquals(turn.amount_total, -33.33)
        turn.action_confirm()
        self.assertEquals(len(turn.picking_ids), 2)
        self.assertEquals(len(turn.picking_ids[0].move_lines), 1)
        self.assertEquals(len(turn.picking_ids[1].move_lines), 1)
        customer_loc = self.env.ref('stock.stock_location_customers')
        stock_loc = self.env.ref('stock.stock_location_stock')
        type_out = self.env.ref('stock.picking_type_out')
        type_in = type_out.return_picking_type_id
        picks = [p for p in turn.picking_ids if p.picking_type_id == type_in]
        self.assertEquals(len(picks), 1)
        self.picking_done(picks[0])
        self.assertEquals(picks[0].move_line_ids[0].location_id, customer_loc)
        self.assertEquals(picks[0].move_line_ids[0].location_dest_id, location)
        self.assertEquals(picks[0].move_lines[0].location_id, customer_loc)
        self.assertEquals(picks[0].move_lines[0].location_dest_id, location)
        picks = [p for p in turn.picking_ids if p.picking_type_id == type_out]
        self.assertEquals(len(picks), 1)
        self.picking_done(picks[0])
        self.assertEquals(picks[0].move_lines[0].location_id, stock_loc)
        self.assertEquals(
            picks[0].move_lines[0].location_dest_id, customer_loc)
        self.assertEquals(picks[0].move_line_ids[0].location_id, stock_loc)
        self.assertEquals(
            picks[0].move_line_ids[0].location_dest_id, customer_loc)

    def test_return_location(self):
        location = self.env.ref('stock.stock_location_components')
        turn = self.env['sale.order'].create({
            'is_return': True,
            'partner_id': self.partner.id,
            'order_line': [(0, 0, {
                'product_id': self.product.id,
                'location_id': location.id,
                'price_unit': 33.33,
                'product_uom_qty': 3})]
        })
        self.assertEquals(turn.amount_total, -99.99)
        turn.action_confirm()
        self.assertEquals(len(turn.picking_ids), 1)
        self.assertEquals(len(turn.picking_ids[0].move_lines), 1)
        self.assertEquals(
            turn.picking_ids[0].move_lines[0].location_dest_id.id, location.id)

    def test_return_change(self):
        turn = self.env['sale.order'].create({
            'is_return': True,
            'partner_id': self.partner.id,
            'order_line': [(0, 0, {
                'product_id': self.product.id,
                'price_unit': 33.33,
                'product_uom_qty': 3})]
        })
        self.assertEquals(turn.amount_total, -99.99)
        line = turn.order_line[0]
        self.assertEquals(line.product_uom_qty, 3)
        line.qty_change = 99
        self.assertRaises(UserError, line._onchange_qty_change)
        self.assertEquals(line.qty_change, line.product_uom_qty)
        line.qty_change = -1
        line._onchange_qty_change()
        self.assertEquals(line.qty_change, 0)
        line.qty_change = line.product_uom_qty
        turn.action_confirm()
        self.assertEquals(len(turn.picking_ids), 2)

    def test_return_change_same_quantity(self):
        turn = self.env['sale.order'].create({
            'is_return': True,
            'partner_id': self.partner.id,
            'order_line': [(0, 0, {
                'product_id': self.product.id,
                'price_unit': 33.33,
                'qty_change': 10,
                'product_uom_qty': 10})]
        })
        self.assertEquals(turn.amount_total, 0)
        turn.action_confirm()
        self.assertEquals(len(turn.picking_ids), 2)
        self.assertEquals(len(turn.picking_ids[0].move_lines), 1)
        self.assertEquals(len(turn.picking_ids[1].move_lines), 1)
        self.assertRaises(Exception, self.invoice_sale, [turn])

    def test_return_invoice(self):
        turn = self.env['sale.order'].create({
            'is_return': True,
            'partner_id': self.partner.id,
            'order_line': [(0, 0, {
                'product_id': self.product.id,
                'product_uom_qty': 3})]
        })
        turn.action_confirm()
        self.picking_done(turn.picking_ids[0])
        invoice = self.invoice_sale(turn)
        self.assertEquals(len(invoice), 1)
        self.assertEquals(invoice.type, 'out_refund')
        self.assertEquals(len(invoice.invoice_line_ids), 1)
        self.assertEquals(invoice.invoice_line_ids[0].quantity, 3)
        self.assertEquals(invoice.amount_total, (turn.amount_total * -1))

    def test_return_and_invoice(self):
        turn = self.env['sale.order'].create({
            'is_return': True,
            'partner_id': self.partner.id,
            'order_line': [(0, 0, {
                'product_id': self.product.id,
                'product_uom_qty': 3})]
        })
        self.assertEquals(turn.order_line[0].product_uom_qty, 3)
        turn.action_confirm()
        self.assertEquals(turn.delivery_count, 1)
        self.assertEquals(len(turn.picking_ids[0].move_lines), 1)
        self.assertEquals(
            turn.picking_ids[0].move_lines[0].location_id,
            self.env.ref('stock.stock_location_customers'))
        self.assertEquals(turn.picking_ids[0].move_lines[0].product_uom_qty, 3)
        self.assertEquals(turn.order_line[0].product_uom_qty, 3)
        self.assertEquals(turn.order_line[0].qty_returned, 0)
        self.assertEquals(turn.order_line[0].qty_returned_to_invoice, 0)
        self.assertEquals(turn.order_line[0].qty_returned_invoiced, 0)
        self.picking_done(turn.picking_ids[0])
        self.assertEquals(turn.picking_ids[0].state, 'done')
        self.assertEquals(turn.order_line[0].product_uom_qty, 3)
        self.assertEquals(turn.order_line[0].qty_returned, 3)
        self.assertEquals(turn.order_line[0].qty_returned_to_invoice, 3)
        self.assertEquals(turn.order_line[0].qty_returned_invoiced, 0)
        invoice = self.invoice_sale(turn)
        self.assertEquals(invoice.type, 'out_refund')
        self.assertEquals(turn.order_line[0].product_uom_qty, 3)
        self.assertEquals(turn.order_line[0].qty_returned, 3)
        self.assertEquals(turn.order_line[0].qty_returned_to_invoice, 0)
        self.assertEquals(turn.order_line[0].qty_returned_invoiced, 3)
        self.assertEquals(len(invoice.invoice_line_ids), 1)
        self.assertEquals(invoice.invoice_line_ids[0].quantity, 3)
        self.assertEquals(invoice.invoice_line_ids[0].product_id, self.product)

    def test_return_invoice_with_change(self):
        turn = self.env['sale.order'].create({
            'is_return': True,
            'partner_id': self.partner.id,
            'order_line': [(0, 0, {
                'product_id': self.product.id,
                'qty_change': 2,
                'product_uom_qty': 3})]
        })
        turn.action_confirm()
        self.assertEquals(len(turn.picking_ids), 2)
        customer_loc = self.env.ref('stock.stock_location_customers')
        picking = [
            p for p in turn.picking_ids
            if p.location_dest_id != customer_loc][0]
        self.picking_done(picking)
        self.assertEquals(turn.order_line[0].qty_changed, 0)
        self.assertEquals(turn.order_line[0].qty_returned, 3)
        self.assertEquals(turn.order_line[0].qty_returned_to_invoice, 3)
        self.assertEquals(turn.order_line[0].qty_changed_to_invoice, 0)
        self.assertEquals(len(picking.move_lines), 1)
        self.assertEquals(picking.move_lines[0].product_uom_qty, 3)
        picking = [
            p for p in turn.picking_ids
            if p.location_dest_id == customer_loc][0]
        self.picking_done(picking)
        self.assertEquals(turn.order_line[0].qty_changed, 2)
        self.assertEquals(turn.order_line[0].qty_returned, 3)
        self.assertEquals(turn.order_line[0].qty_returned_to_invoice, 3)
        self.assertEquals(turn.order_line[0].qty_changed_to_invoice, 2)
        self.assertEquals(len(picking.move_lines), 1)
        self.assertEquals(picking.move_lines[0].product_uom_qty, 2)
        invoice = self.invoice_sale(turn)
        self.assertEquals(invoice.type, 'out_refund')
        self.assertEquals(len(invoice.invoice_line_ids), 2)
        self.assertEquals(invoice.invoice_line_ids[0].quantity, 3)
        self.assertEquals(invoice.invoice_line_ids[1].quantity, -2)
        self.assertEquals(invoice.amount_total, (turn.amount_total * -1))
        self.assertEquals(turn.order_line[0].qty_changed, 2)
        self.assertEquals(turn.order_line[0].qty_returned, 3)
        self.assertEquals(turn.order_line[0].qty_returned_to_invoice, 0)
        self.assertEquals(turn.order_line[0].qty_changed_to_invoice, 0)

    def test_return_invoice_sale_and_return_with_change(self):
        sale = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'order_line': [(0, 0, {
                'product_id': self.product.id,
                'product_uom_qty': 10})]
        })
        sale.action_confirm()
        self.picking_done(sale.picking_ids[0])
        turn = self.env['sale.order'].create({
            'is_return': True,
            'partner_id': self.partner.id,
            'order_line': [(0, 0, {
                'product_id': self.product.id,
                'qty_change': 2,
                'product_uom_qty': 3})]
        })
        turn.action_confirm()
        self.assertEquals(len(turn.picking_ids), 2)
        customer_loc = self.env.ref('stock.stock_location_customers')
        picking = [
            p for p in turn.picking_ids
            if p.location_dest_id != customer_loc][0]
        self.picking_done(picking)
        self.assertEquals(turn.order_line[0].qty_changed, 0)
        self.assertEquals(turn.order_line[0].qty_returned, 3)
        self.assertEquals(turn.order_line[0].qty_returned_to_invoice, 3)
        self.assertEquals(turn.order_line[0].qty_changed_to_invoice, 0)
        self.assertEquals(len(picking.move_lines), 1)
        self.assertEquals(picking.move_lines[0].product_uom_qty, 3)
        picking = [
            p for p in turn.picking_ids
            if p.location_dest_id == customer_loc][0]
        self.picking_done(picking)
        self.assertEquals(turn.order_line[0].qty_changed, 2)
        self.assertEquals(turn.order_line[0].qty_returned, 3)
        self.assertEquals(turn.order_line[0].qty_returned_to_invoice, 3)
        self.assertEquals(turn.order_line[0].qty_changed_to_invoice, 2)
        self.assertEquals(len(picking.move_lines), 1)
        self.assertEquals(picking.move_lines[0].product_uom_qty, 2)
        price_unit = sale.amount_total / 10
        sale |= turn
        invoice = self.invoice_sale(sale)
        self.assertEquals(invoice.type, 'out_invoice')
        self.assertEquals(len(invoice.invoice_line_ids), 3)
        self.assertEquals(invoice.invoice_line_ids[0].quantity, 10)
        self.assertEquals(invoice.invoice_line_ids[1].quantity, -3)
        self.assertEquals(invoice.invoice_line_ids[2].quantity, 2)
        self.assertEquals(invoice.amount_total, price_unit * 9)
        self.assertEquals(turn.order_line[0].qty_changed, 2)
        self.assertEquals(turn.order_line[0].qty_returned, 3)
        self.assertEquals(turn.order_line[0].qty_returned_to_invoice, 0)
        self.assertEquals(turn.order_line[0].qty_changed_to_invoice, 0)

    def test_return_invoice_same_quantity(self):
        sale = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'order_line': [(0, 0, {
                'product_id': self.product.id,
                'product_uom_qty': 10})]
        })
        sale.action_confirm()
        self.picking_done(sale.picking_ids[0])
        turn = self.env['sale.order'].create({
            'is_return': True,
            'partner_id': self.partner.id,
            'order_line': [(0, 0, {
                'product_id': self.product.id,
                'product_uom_qty': 10})]
        })
        turn.action_confirm()
        self.picking_done(turn.picking_ids[0])
        sale |= turn
        invoices = self.invoice_sale(sale)
        self.assertEquals(len(invoices), 2)
        self.assertTrue(invoices[0].amount_total > 0)
        self.assertEquals(invoices[0].amount_total, invoices[1].amount_total)
        self.assertTrue(invoices[0].type != invoices[1].type)
        self.assertEquals(invoices[0].origin, sale[0].name)
        self.assertEquals(invoices[1].origin, sale[1].name)
