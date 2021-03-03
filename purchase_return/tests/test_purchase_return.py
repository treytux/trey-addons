###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo.tests.common import TransactionCase


class TestPurchaseReturn(TransactionCase):

    def setUp(self):
        super().setUp()
        self.partner = self.env.ref('base.res_partner_3')
        self.partner2 = self.env.ref('base.res_partner_4')
        self.product = self.env.ref(
            'product.product_product_3_product_template').product_variant_id

    def picking_done(self, picking):
        picking.action_confirm()
        picking.action_assign()
        for move in picking.move_lines:
            move.quantity_done = move.product_uom_qty
        picking.action_done()

    def create_purchase(self, qty):
        purchase = self.env['purchase.order'].create({
            'partner_id': self.partner.id})
        self.create_purchase_line(purchase, qty)
        purchase.button_confirm()
        return purchase

    def create_purchase_line(self, purchase, qty):
        line = self.env['purchase.order.line'].new({
            'order_id': purchase.id,
            'product_id': self.product.id})
        line.onchange_product_id()
        line.price_unit = 99.99
        line.product_qty = qty
        line.create(line._convert_to_write(line._cache))
        return line

    def test_purchase_diferent_lines(self):
        purchase = self.env['purchase.order'].create({
            'partner_id': self.partner.id})
        self.create_purchase_line(purchase, 10)
        self.create_purchase_line(purchase, -9)
        purchase.button_confirm()
        self.assertEquals(len(purchase.picking_ids), 2)
        self.picking_done(purchase.picking_ids[0])
        self.picking_done(purchase.picking_ids[1])

    def test_purchases_invoice(self):
        purchases = self.env['purchase.order']
        purchases |= self.create_purchase(10)
        self.picking_done(purchases[0].picking_ids[0])
        purchases |= self.create_purchase(-1)
        self.picking_done(purchases[1].picking_ids[0])
        invoices = purchases.create_invoices()
        self.assertEquals(len(invoices), 2)
        self.assertEquals(len(purchases[0].invoice_ids[0].invoice_line_ids), 1)
        self.assertEquals(len(purchases[1].invoice_ids[0].invoice_line_ids), 1)
        self.assertEquals(
            purchases[0].invoice_ids[0].invoice_line_ids[0].quantity, 10)
        self.assertEquals(
            purchases[1].invoice_ids[0].invoice_line_ids[0].quantity, 1)
        self.assertEquals(purchases[0].invoice_ids[0].type, 'in_invoice')
        self.assertEquals(purchases[1].invoice_ids[0].type, 'in_refund')

    def test_purchase_invoice_negative(self):
        purchase = self.create_purchase(-10)
        self.assertEquals(purchase.order_line.product_qty, -10)
        self.assertEquals(purchase.order_line.price_unit, 99.99)
        self.assertTrue(purchase.amount_total < 0)
        purchase.button_confirm()
        self.assertEquals(purchase.order_line.product_qty, -10)
        self.assertEquals(purchase.order_line.price_unit, 99.99)
        self.assertTrue(purchase.amount_total < 0)
        self.assertEquals(len(purchase.picking_ids), 1)
        self.picking_done(purchase.picking_ids[0])
        purchase.with_context(create_bill=True).action_view_invoice()
        self.assertEquals(len(purchase.invoice_ids), 1)
        self.assertEquals(purchase.invoice_status, 'invoiced')
        self.assertEquals(
            purchase.invoice_ids[0].amount_total, purchase.amount_total * -1)
        self.assertEquals(
            purchase.invoice_ids[0].invoice_line_ids[0].quantity, 10)
        self.assertEquals(purchase.invoice_ids[0].type, 'in_refund')

    def test_purchase_invoice(self):
        purchase = self.create_purchase(10)
        self.assertEquals(purchase.order_line.product_qty, 10)
        self.assertEquals(purchase.order_line.price_unit, 99.99)
        self.assertTrue(purchase.amount_total > 0)
        purchase.button_confirm()
        self.assertEquals(purchase.order_line.product_qty, 10)
        self.assertEquals(purchase.order_line.price_unit, 99.99)
        self.assertTrue(purchase.amount_total > 0)
        self.assertEquals(len(purchase.picking_ids), 1)
        self.picking_done(purchase.picking_ids[0])
        purchase.with_context(create_bill=True).action_view_invoice()
        self.assertEquals(len(purchase.invoice_ids), 1)
        self.assertEquals(purchase.invoice_status, 'invoiced')
        self.assertEquals(
            purchase.invoice_ids[0].amount_total, purchase.amount_total)
        self.assertEquals(
            purchase.invoice_ids[0].invoice_line_ids[0].quantity, 10)
        self.assertEquals(purchase.invoice_ids[0].type, 'in_invoice')

    def test_negative_qty_without_seller_01(self):
        self.assertEquals(len(self.product.seller_ids), 0)
        purchase = self.env['purchase.order'].create({
            'partner_id': self.partner.id})
        line = self.env['purchase.order.line'].new({
            'order_id': purchase.id,
            'product_id': self.product.id})
        line.onchange_product_id()
        line.product_qty = -1
        line.create(line._convert_to_write(line._cache))
        self.assertEquals(line.product_qty, -1)
        self.assertEquals(line.price_unit, 0)

    def test_negative_qty_without_seller_02(self):
        self.assertEquals(len(self.product.seller_ids), 0)
        purchase = self.env['purchase.order'].create({
            'partner_id': self.partner.id})
        line = self.env['purchase.order.line'].new({
            'order_id': purchase.id,
            'product_id': self.product.id})
        line.onchange_product_id()
        line.product_qty = -2
        line.create(line._convert_to_write(line._cache))
        self.assertEquals(line.product_qty, -2)
        self.assertEquals(line.price_unit, 0)

    def test_negative_qty_with_seller_01(self):
        self.assertEquals(len(self.product.seller_ids), 0)
        self.env['product.supplierinfo'].create({
            'name': self.partner.id,
            'product_tmpl_id': self.product.product_tmpl_id.id,
            'min_qty': 0.0,
            'price': 8888,
        })
        self.assertEquals(len(self.product.seller_ids), 1)
        purchase = self.env['purchase.order'].create({
            'partner_id': self.partner.id})
        line = self.env['purchase.order.line'].new({
            'order_id': purchase.id,
            'product_id': self.product.id})
        line.onchange_product_id()
        line.product_qty = -1
        line.create(line._convert_to_write(line._cache))
        self.assertEquals(line.product_qty, -1)
        self.assertEquals(line.price_unit, 8888)

    def test_negative_qty_with_seller_02(self):
        self.assertEquals(len(self.product.seller_ids), 0)
        self.env['product.supplierinfo'].create({
            'name': self.partner.id,
            'product_tmpl_id': self.product.product_tmpl_id.id,
            'min_qty': 0.0,
            'price': 8888,
        })
        self.assertEquals(len(self.product.seller_ids), 1)
        purchase = self.env['purchase.order'].create({
            'partner_id': self.partner.id})
        line = self.env['purchase.order.line'].new({
            'order_id': purchase.id,
            'product_id': self.product.id})
        line.onchange_product_id()
        line.product_qty = -2
        line.create(line._convert_to_write(line._cache))
        self.assertEquals(line.product_qty, -2)
        self.assertEquals(line.price_unit, 8888)

    def test_negative_qty_with_seller_03(self):
        self.assertEquals(len(self.product.seller_ids), 0)
        self.env['product.supplierinfo'].create({
            'name': self.partner.id,
            'product_tmpl_id': self.product.product_tmpl_id.id,
            'min_qty': 0.0,
            'price': 8888,
        })
        self.assertEquals(
            len(self.product.seller_ids.filtered(
                lambda s: s.name == self.partner)), 1)
        self.assertEquals(
            len(self.product.seller_ids.filtered(
                lambda s: s.name == self.partner2)), 0)
        purchase = self.env['purchase.order'].create({
            'partner_id': self.partner.id})
        line = self.env['purchase.order.line'].new({
            'order_id': purchase.id,
            'product_id': self.product.id})
        line.onchange_product_id()
        line.product_qty = -1
        line.create(line._convert_to_write(line._cache))
        self.assertEquals(line.product_qty, -1)
        self.assertEquals(line.price_unit, 8888)
        purchase2 = self.env['purchase.order'].create({
            'partner_id': self.partner2.id})
        line = self.env['purchase.order.line'].new({
            'order_id': purchase2.id,
            'product_id': self.product.id})
        line.onchange_product_id()
        line.product_qty = -1
        line.create(line._convert_to_write(line._cache))
        self.assertEquals(line.product_qty, -1)
        self.assertEquals(line.price_unit, 0)
