###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo.tests import common


class TestAccountInvoiceLineByDefaultCode(common.TransactionCase):

    def setUp(self):
        super().setUp()
        self.fiscal_position_es = self.env['account.fiscal.position'].create({
            'name': 'Fiscal position es',
            'country_id': self.env.ref('base.es').id,
        })
        self.partner = self.env['res.partner'].create({
            'name': 'Test partner',
            'customer': True,
            'is_company': True,
            'property_account_position_id': self.fiscal_position_es.id,
        })
        self.product_01 = self.env['product.product'].create({
            'type': 'product',
            'company_id': False,
            'name': 'Service product 01',
            'default_code': 'TESTPR01',
            'standard_price': 10,
            'list_price': 30,
        })
        self.product_02 = self.env['product.product'].create({
            'type': 'product',
            'company_id': False,
            'name': 'Service product 02',
            'default_code': 'TESTPR02',
            'standard_price': 10,
            'list_price': 20,
        })
        self.product_03 = self.env['product.product'].create({
            'type': 'product',
            'company_id': False,
            'name': 'Service product 03',
            'default_code': 'TESTPR03',
            'standard_price': 10,
            'list_price': 40,
        })
        self.sale = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'picking_policy': 'direct',
            'order_line': [
                (0, 0, {
                    'product_id': self.product_01.id,
                    'price_unit': 100,
                    'product_uom_qty': 1}),
                (0, 0, {
                    'product_id': self.product_02.id,
                    'price_unit': 100,
                    'product_uom_qty': 2}),
            ]
        })
        self.sale.action_confirm()
        self.sale.action_invoice_create()

    def test_keep_line_with_products_in_wizard(self):
        self.assertEqual(self.sale.state, 'sale')
        self.assertEqual(len(self.sale.invoice_ids), 1)
        invoice = self.sale.invoice_ids[0]
        self.assertEqual(invoice.state, 'draft')
        wizard = self.env['account.invoice.line.by.default.code'].with_context(
            active_ids=invoice.ids).create({
                'name': 'Wizard test',
            })
        self.assertEqual(wizard.invoice_id, invoice)
        self.assertEqual(len(wizard.line_ids), 0)
        wizard.write({
            'line_ids': [
                (0, 0, {
                    'product_id': self.product_01.id,
                    'name': self.product_01.name,
                    'wizard_id': wizard.id,
                }),
                (0, 0, {
                    'product_id': self.product_03.id,
                    'name': self.product_03.name,
                    'wizard_id': wizard.id,
                }),
            ],
        })
        self.assertEqual(len(wizard.line_ids), 2)
        self.assertEqual(len(invoice.invoice_line_ids), 2)
        self.assertEqual(
            invoice.invoice_line_ids[0].product_id,
            wizard.line_ids[0].product_id)
        self.assertNotEqual(
            invoice.invoice_line_ids[1].product_id,
            wizard.line_ids[1].product_id)
        amount_total = invoice.amount_total
        wizard.button_keep_only_wizard_products()
        self.assertEqual(invoice.state, 'draft')
        self.assertEqual(len(invoice.invoice_line_ids), 1)
        self.assertEqual(
            invoice.invoice_line_ids[0].product_id,
            wizard.line_ids[0].product_id)
        self.assertNotEqual(invoice.amount_total, amount_total)

    def test_add_products_to_invoice(self):
        self.assertEqual(self.sale.state, 'sale')
        self.assertEqual(len(self.sale.invoice_ids), 1)
        invoice = self.sale.invoice_ids[0]
        self.assertEqual(invoice.state, 'draft')
        wizard = self.env['account.invoice.line.by.default.code'].with_context(
            active_ids=invoice.ids).create({
                'name': 'Wizard test',
            })
        self.assertEqual(wizard.invoice_id.id, invoice.id)
        self.assertEqual(len(wizard.line_ids), 0)
        wizard.write({
            'line_ids': [
                (0, 0, {
                    'product_id': self.product_03.id,
                    'name': self.product_03.name,
                    'wizard_id': wizard.id,
                }),
                (0, 0, {
                    'wizard_id': wizard.id,
                    'name': self.product_01.name,
                    'product_id': self.product_01.id,
                }),
            ],
        })
        self.assertEqual(len(wizard.line_ids), 2)
        self.assertEqual(len(invoice.invoice_line_ids), 2)
        self.assertEqual(
            invoice.invoice_line_ids[0].product_id,
            wizard.line_ids[1].product_id)
        self.assertNotEqual(
            invoice.invoice_line_ids[1].product_id,
            wizard.line_ids[0].product_id)
        self.assertEqual(invoice.invoice_line_ids[0].quantity, 1)
        self.assertEqual(invoice.invoice_line_ids[1].quantity, 2)
        amount_total = invoice.amount_total
        line_subtotal = invoice.invoice_line_ids[0].price_subtotal
        wizard.button_add_all_products()
        self.assertEqual(invoice.state, 'draft')
        self.assertEqual(len(invoice.invoice_line_ids), 3)
        self.assertEqual(invoice.invoice_line_ids[0].quantity, 2)
        self.assertEqual(invoice.invoice_line_ids[1].quantity, 2)
        self.assertEqual(
            invoice.invoice_line_ids[2].product_id, self.product_03)
        self.assertEqual(invoice.invoice_line_ids[2].quantity, 1)
        self.assertEqual(
            invoice.invoice_line_ids[2].price_unit, self.product_03.list_price)
        self.assertNotEqual(invoice.amount_total, amount_total)
        self.assertNotEqual(
            invoice.invoice_line_ids[0].price_subtotal, line_subtotal)
        self.assertEqual(
            invoice.invoice_line_ids[0].price_subtotal, line_subtotal * 2)
        invoice_line = invoice.invoice_line_ids.filtered(
            lambda l: l.product_id.default_code == 'TESTPR03')
        self.assertEqual(len(invoice_line), 1)
        self.assertTrue(invoice_line.invoice_line_tax_ids)
        self.assertEqual(
            invoice_line.invoice_line_tax_ids,
            invoice.invoice_line_ids[0].invoice_line_tax_ids)
        self.assertEqual(
            invoice_line.invoice_line_tax_ids,
            invoice.invoice_line_ids[1].invoice_line_tax_ids)
