###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo.tests import common


class TestAccountInvoiceSupplierSequence(common.TransactionCase):

    def setUp(self):
        super().setUp()
        self.sequence_1 = self.env['ir.sequence'].create({
            'name': 'Test invoice sequence for partner 1',
            'code': 'account.invoice.partner_1',
            'prefix': 'A-',
            'padding': 3,
        })
        self.partner_1 = self.env['res.partner'].create({
            'name': 'Supplier test 1',
            'invoice_supplier_sequence_id': self.sequence_1.id,
        })
        self.sequence_2 = self.env['ir.sequence'].create({
            'name': 'Test invoice sequence for partner 2',
            'code': 'account.invoice.partner_2',
            'prefix': 'B-',
            'padding': 3,
        })
        self.partner_2 = self.env['res.partner'].create({
            'name': 'Supplier test 2',
            'invoice_supplier_sequence_id': self.sequence_2.id,
        })
        self.product = self.env['product.product'].create({
            'name': 'Product test',
            'type': 'service',
            'company_id': False,
            'standard_price': 100,
            'list_price': 100,
        })

    def create_invoice(self, partner):
        invoice = self.env['account.invoice'].create({
            'partner_id': partner.id,
            'type': 'in_invoice',
        })
        invoice._onchange_partner_id()
        line = self.env['account.invoice.line'].new({
            'invoice_id': invoice.id,
            'product_id': self.product.id,
            'product_uom_qty': 1.0,
            'product_uom': self.ref('uom.product_uom_unit'),
        })
        line._onchange_product_id()
        self.env['account.invoice.line'].with_context({
            'partner_id': partner.id
        }).create(line._cache)
        return invoice

    def test_create_invoice(self):
        invoice = self.create_invoice(self.partner_1)
        self.assertEqual(invoice.reference, 'A-001')
        invoice.action_invoice_open()
        self.assertEqual(invoice.state, 'open')
        self.assertEqual(invoice.reference, 'A-001')
        invoice = self.create_invoice(self.partner_1)
        self.assertEqual(invoice.reference, 'A-002')
        invoice.action_invoice_open()
        self.assertEqual(invoice.state, 'open')
        self.assertEqual(invoice.reference, 'A-002')
        invoice = self.create_invoice(self.partner_2)
        self.assertEqual(invoice.reference, 'B-001')
        invoice.action_invoice_open()
        self.assertEqual(invoice.state, 'open')
        self.assertEqual(invoice.reference, 'B-001')
        invoice = self.create_invoice(self.partner_2)
        self.assertEqual(invoice.reference, 'B-002')
        invoice = self.create_invoice(self.partner_2)
        self.assertEqual(invoice.reference, 'B-003')
        invoice.action_invoice_open()
        self.assertEqual(invoice.state, 'open')
        self.assertEqual(invoice.reference, 'B-003')
