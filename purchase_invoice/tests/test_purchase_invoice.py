###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo.tests.common import TransactionCase


class TestPurchaseInvoice(TransactionCase):

    def setUp(self):
        super().setUp()
        self.partner = self.env.ref('base.res_partner_3')
        self.product = self.env.ref(
            'product.product_product_3_product_template').product_variant_id

    def picking_done(self, picking):
        picking.action_confirm()
        picking.action_assign()
        for move in picking.move_lines:
            move.quantity_done = move.product_uom_qty
        picking.action_done()

    def create_purchase_line(self, purchase, qty):
        line = self.env['purchase.order.line'].new({
            'order_id': purchase.id,
            'product_id': self.product.id})
        line.onchange_product_id()
        line.price_unit = 99.99
        line.product_qty = qty
        line.create(line._convert_to_write(line._cache))
        return line

    def test_purchase_invoice(self):
        purchase = self.env['purchase.order'].create({
            'partner_id': self.partner.id})
        self.create_purchase_line(purchase, 10)
        self.create_purchase_line(purchase, 1)
        purchase.button_confirm()
        self.assertEquals(purchase.invoice_status, 'no')
        self.picking_done(purchase.picking_ids[0])
        self.assertEquals(purchase.invoice_status, 'to invoice')
        purchase.action_create_invoice()
        self.assertEquals(len(purchase.invoice_ids), 1)
        self.assertEquals(purchase.invoice_status, 'invoiced')
        invoice = purchase.invoice_ids[0]
        self.assertEquals(invoice.invoice_line_ids[0].quantity, 10)
        self.assertEquals(invoice.invoice_line_ids[1].quantity, 1)
        self.assertEquals(invoice.amount_total, purchase.amount_total)
        self.assertEquals(invoice.type, 'in_invoice')

    def test_purchase_merge_invoice(self):
        purchases = self.env['purchase.order'].with_context(
            merge_draft_invoice=True)
        for qty in [10, 5, 1]:
            purchase = self.env['purchase.order'].create({
                'partner_id': self.partner.id})
            self.create_purchase_line(purchase, qty)
            purchase.button_confirm()
            self.picking_done(purchase.picking_ids[0])
            purchases |= purchase
        self.assertEquals(len(purchases), 3)
        invoices = purchases.create_invoices()
        self.assertEquals(len(invoices), 1)
        self.assertEquals(len(purchases[0].invoice_ids), 1)
        self.assertEquals(len(purchases[1].invoice_ids), 1)
        self.assertEquals(len(purchases[2].invoice_ids), 1)
        self.assertEquals(purchases[0].invoice_ids, purchases[1].invoice_ids)
        self.assertEquals(purchases[1].invoice_ids, purchases[2].invoice_ids)
        self.assertEquals(len(invoices.invoice_line_ids), 3)
        self.assertEquals(sum(purchases.mapped('order_line.product_qty')), 16)
        self.assertEquals(
            sum(invoices.mapped('invoice_line_ids.quantity')), 16)
        self.assertEquals(invoices.invoice_line_ids[0].quantity, 10)
        self.assertEquals(invoices.invoice_line_ids[1].quantity, 5)
        self.assertEquals(invoices.invoice_line_ids[2].quantity, 1)
        self.assertEquals(
            sum([p.amount_total for p in purchases]), invoices.amount_total)
