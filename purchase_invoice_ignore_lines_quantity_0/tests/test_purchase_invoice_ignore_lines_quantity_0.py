###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import fields
from odoo.tests.common import TransactionCase


class TestPurchaseInvoiceIgnoreLinesQuantity0(TransactionCase):

    def setUp(self):
        super().setUp()
        self.partner = self.env['res.partner'].create({
            'name': 'Partner test',
        })
        self.product = self.env['product.product'].create({
            'type': 'consu',
            'company_id': False,
            'name': 'Cosumable product',
            'standard_price': 10,
            'list_price': 100,
            'purchase_method': 'purchase',
        })
        self.product2 = self.env['product.product'].create({
            'type': 'service',
            'company_id': False,
            'name': 'Service product 2',
            'standard_price': 10,
            'list_price': 100,
            'purchase_method': 'purchase',
        })
        self.journal = self.env['account.journal'].search([
            ('company_id', '=', self.env.user.company_id.id),
            ('type', '=', 'sale'),
        ], limit=1)
        self.account = self.env.user.company_id.get_chart_of_accounts_or_fail()

    def test_onchange_purchase_id_2_lines_ignore_quantity_0(self):
        purchase = self.env['purchase.order'].create({
            'partner_id': self.partner.id,
            'order_line': [
                (0, 0, {
                    'name': self.product.name,
                    'product_id': self.product.id,
                    'product_qty': 2,
                    'price_unit': 100.0,
                    'date_planned': fields.Date.today(),
                    'product_uom': self.product.uom_po_id.id,
                }),
                (0, 0, {
                    'name': self.product2.name,
                    'product_id': self.product2.id,
                    'product_qty': 0,
                    'price_unit': 100.0,
                    'date_planned': fields.Date.today(),
                    'product_uom': self.product2.uom_po_id.id,
                }),
            ]
        })
        purchase.button_confirm()
        line_product2 = purchase.order_line.filtered(
            lambda ln: ln.product_id == self.product2)
        line_product2.qty_received = 2
        invoice = self.env['account.invoice'].create({
            'partner_id': purchase.partner_id.id,
            'purchase_id': purchase.id,
            'account_id': purchase.partner_id.property_account_payable_id.id,
            'type': 'in_invoice',
        })

        invoice.purchase_order_change()
        line_product = purchase.order_line.filtered(
            lambda ln: ln.product_id == self.product)
        invoice_line = invoice.invoice_line_ids.filtered(
            lambda ln: ln.product_id == self.product)
        self.assertEquals(line_product.product_qty, 2)
        self.assertEquals(line_product2.product_qty, 0)
        self.assertEquals(len(purchase.order_line), 2)
        self.assertEquals(len(invoice.invoice_line_ids), 1)
        self.assertEquals(invoice_line.quantity, line_product.product_qty)

    def test_onchange_purchase_id_2_lines_none_quantity_0(self):
        purchase = self.env['purchase.order'].create({
            'partner_id': self.partner.id,
        })
        line_obj = self.env['purchase.order.line']
        purchase_line_1 = line_obj.create({
            'name': self.product.name,
            'product_id': self.product.id,
            'product_qty': 2,
            'price_unit': 100.0,
            'order_id': purchase.id,
            'date_planned': fields.Date.today(),
            'product_uom': self.product.uom_po_id.id,
        })
        line_obj.create({
            'name': self.product2.name,
            'product_id': self.product2.id,
            'product_qty': 1,
            'price_unit': 100.0,
            'order_id': purchase.id,
            'date_planned': fields.Date.today(),
            'product_uom': self.product2.uom_po_id.id,
        })
        purchase.button_confirm()
        purchase_line_1.qty_received = 2
        invoice = self.env['account.invoice'].create({
            'partner_id': purchase.partner_id.id,
            'purchase_id': purchase.id,
            'account_id': purchase.partner_id.property_account_payable_id.id,
            'type': 'in_invoice',
        })
        invoice.purchase_order_change()
        line_product = purchase.order_line.filtered(
            lambda ln: ln.product_id == self.product)
        self.assertEquals(line_product.product_qty, 2)
        line_product2 = purchase.order_line.filtered(
            lambda ln: ln.product_id == self.product2)
        self.assertEquals(line_product2.product_qty, 1)
        invoice_line = invoice.invoice_line_ids.filtered(
            lambda ln: ln.product_id == self.product)
        self.assertEquals(invoice_line.quantity, line_product.product_qty)
        invoice_line2 = invoice.invoice_line_ids.filtered(
            lambda ln: ln.product_id == self.product2)
        self.assertEquals(invoice_line2.quantity, line_product2.product_qty)
        self.assertEquals(len(purchase.order_line), 2)
        self.assertEquals(len(invoice.invoice_line_ids), 2)
