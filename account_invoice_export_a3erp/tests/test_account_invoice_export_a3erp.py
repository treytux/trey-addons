###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
import base64

from odoo import exceptions
from odoo.tests import common


class TestAccountInvoiceExportA3Erp(common.TransactionCase):

    def setUp(self):
        super().setUp()
        self.partner = self.env['res.partner'].create({
            'name': 'Test partner',
            'is_company': True,
        })
        self.product_01 = self.env['product.product'].create({
            'type': 'service',
            'company_id': False,
            'name': 'Service test product 01',
            'standard_price': 5,
            'list_price': 10,
        })
        self.product_02 = self.env['product.product'].create({
            'type': 'service',
            'company_id': False,
            'name': 'Service test product 02',
            'standard_price': 6,
            'list_price': 13,
        })
        self.sale = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'order_line': [
                (0, 0, {
                    'product_id': self.product_01.id,
                    'price_unit': 9.99,
                    'product_uom_qty': 1,
                }),
                (0, 0, {
                    'product_id': self.product_02.id,
                    'price_unit': 19.99,
                    'product_uom_qty': 1,
                }),
            ],
        })
        self.company = self.env['res.company'].browse(1)
        self.company_code_a3erp = '1234'
        self.office_code_a3erp = '6789'
        self.company.write({
            'company_code_a3erp': self.company_code_a3erp,
            'office_code_a3erp': self.office_code_a3erp,
        })
        self.payment_method = self.env['account.payment.method'].create({
            'name': 'Method Test',
            'code': 'CODTEST',
            'payment_type': 'inbound',
        })
        self.account_type = self.env.ref(
            'account.data_account_type_receivable')
        self.account = self.env['account.account'].create({
            'code': '100',
            'user_type_id': self.account_type.id,
            'name': 'Test account',
            'reconcile': True,
        })
        self.journal = self.env['account.journal'].create({
            'name': 'Customer Invoices - Test',
            'code': 'TINV',
            'type': 'sale',
            'default_credit_account_id': self.account.id,
            'default_debit_account_id': self.account.id,
            'refund_sequence': True,
        })

    def test_create_invoice_file(self):
        self.assertEqual(self.sale.state, 'draft')
        self.sale.action_confirm()
        self.assertEqual(self.sale.state, 'sale')
        self.assertEqual(len(self.sale.invoice_ids), 0)
        self.sale.action_invoice_create()
        self.assertEqual(len(self.sale.invoice_ids), 1)
        invoice = self.sale.invoice_ids[0]
        invoice.action_invoice_open()
        self.assertTrue(invoice.date_invoice)
        self.assertTrue(invoice.date_due)
        operation_type_a3erp = '9876'
        tax_type_a3erp = '5432'
        invoice.payment_mode_id.operation_type_a3erp = operation_type_a3erp
        invoice.payment_mode_id.tax_type_a3erp = tax_type_a3erp
        self.assertEqual(
            invoice.company_id.company_code_a3erp, self.company_code_a3erp)
        self.assertEqual(
            invoice.company_id.office_code_a3erp, self.office_code_a3erp)
        self.assertEqual(
            invoice.payment_mode_id.operation_type_a3erp, operation_type_a3erp)
        self.assertEqual(
            invoice.payment_mode_id.tax_type_a3erp, tax_type_a3erp)
        export_a3erp_obj = self.env['account.invoice.export.a3erp']
        wizard = export_a3erp_obj.with_context(
            active_ids=invoice.ids,
            active_id=invoice.ids[0],
        ).create({})
        self.assertFalse(wizard.generated_file)
        wizard.button_generate_invoice_a3erp_file()
        self.assertTrue(wizard.generated_file)
        content = wizard.generated_file
        data = base64.b64decode(content)
        info = data.decode('UTF-8')
        test_line = export_a3erp_obj.generate_invoice_a3erp_file(invoice)
        self.assertEqual(info[8:], test_line[8:])

    def test_create_refund_operations_file(self):
        self.assertEqual(self.sale.state, 'draft')
        self.sale.action_confirm()
        self.assertEqual(self.sale.state, 'sale')
        self.assertEqual(len(self.sale.invoice_ids), 0)
        self.sale.action_invoice_create()
        self.assertEqual(len(self.sale.invoice_ids), 1)
        invoice = self.sale.invoice_ids[0]
        invoice.action_invoice_open()
        self.assertTrue(invoice.date_invoice)
        self.assertTrue(invoice.date_due)
        payment = self.env['account.payment'].with_context(
            active_model='account.invoice',
            active_id=invoice.id,
            active_ids=invoice.ids,
        ).create({
            'name': self.sale.name,
            'payment_method_id': self.payment_method.id,
            'journal_id': self.journal.id,
        })
        payment.action_validate_invoice_payment()
        operation_type_a3erp = '9876'
        tax_type_a3erp = '5432'
        self.env['account.invoice.refund'].with_context(
            active_ids=invoice.ids).create({
                'filter_refund': 'refund',
                'description': 'Refund reason',
            }).invoice_refund()
        self.assertEqual(len(self.sale.invoice_ids), 2)
        invoice_refund = self.sale.invoice_ids - invoice
        self.assertEqual(len(invoice_refund), 1)
        invoice_refund.payment_mode_id.operation_type_a3erp = (
            operation_type_a3erp)
        invoice_refund.payment_mode_id.tax_type_a3erp = tax_type_a3erp
        self.assertEqual(
            invoice_refund.company_id.company_code_a3erp,
            self.company_code_a3erp)
        self.assertEqual(
            invoice_refund.company_id.office_code_a3erp,
            self.office_code_a3erp)
        self.assertEqual(
            invoice_refund.payment_mode_id.operation_type_a3erp,
            operation_type_a3erp)
        self.assertEqual(
            invoice_refund.payment_mode_id.tax_type_a3erp, tax_type_a3erp)
        export_a3erp_obj = self.env['account.invoice.export.a3erp']
        wizard = export_a3erp_obj.with_context(
            active_ids=invoice.ids,
            active_id=invoice.ids[0],
        ).create({})
        self.assertFalse(wizard.generated_file)
        wizard.button_generate_operation_a3erp_file()
        self.assertTrue(wizard.generated_file)
        content = wizard.generated_file
        data = base64.b64decode(content)
        info = data.decode('UTF-8')
        data = ''
        test_line = export_a3erp_obj.generate_operations_a3erp_file(invoice)
        self.assertEqual(info, test_line)

    def test_create_operations_file(self):
        self.assertEqual(self.sale.state, 'draft')
        self.sale.action_confirm()
        self.assertEqual(self.sale.state, 'sale')
        self.assertEqual(len(self.sale.invoice_ids), 0)
        self.sale.action_invoice_create()
        self.assertEqual(len(self.sale.invoice_ids), 1)
        invoice = self.sale.invoice_ids[0]
        invoice.action_invoice_open()
        self.assertTrue(invoice.date_invoice)
        self.assertTrue(invoice.date_due)
        payment = self.env['account.payment'].with_context(
            active_model='account.invoice',
            active_id=invoice.id,
            active_ids=invoice.ids,
        ).create({
            'name': self.sale.name,
            'payment_method_id': self.payment_method.id,
            'journal_id': self.journal.id,
        })
        payment.action_validate_invoice_payment()
        operation_type_a3erp = '9876'
        tax_type_a3erp = '5432'
        invoice.payment_mode_id.operation_type_a3erp = operation_type_a3erp
        invoice.payment_mode_id.tax_type_a3erp = tax_type_a3erp
        self.assertEqual(
            invoice.company_id.company_code_a3erp, self.company_code_a3erp)
        self.assertEqual(
            invoice.company_id.office_code_a3erp, self.office_code_a3erp)
        self.assertEqual(
            invoice.payment_mode_id.operation_type_a3erp, operation_type_a3erp)
        self.assertEqual(
            invoice.payment_mode_id.tax_type_a3erp, tax_type_a3erp)
        export_a3erp_obj = self.env['account.invoice.export.a3erp']
        wizard = export_a3erp_obj.with_context(
            active_ids=invoice.ids,
            active_id=invoice.ids[0],
        ).create({})
        self.assertFalse(wizard.generated_file)
        wizard.button_generate_operation_a3erp_file()
        self.assertTrue(wizard.generated_file)
        content = wizard.generated_file
        data = base64.b64decode(content)
        info = data.decode('UTF-8')
        data = ''
        test_line = export_a3erp_obj.generate_operations_a3erp_file(invoice)
        self.assertEqual(info, test_line)

    def test_error_invoice_per_file(self):
        self.assertEqual(self.sale.state, 'draft')
        self.sale.action_confirm()
        self.assertEqual(self.sale.state, 'sale')
        self.assertEqual(len(self.sale.invoice_ids), 0)
        self.sale.action_invoice_create()
        self.assertEqual(len(self.sale.invoice_ids), 1)
        invoice_01 = self.sale.invoice_ids[0]
        invoice_01.action_invoice_open()
        sale_02 = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'order_line': [
                (0, 0, {
                    'product_id': self.product_01.id,
                    'price_unit': 9.99,
                    'product_uom_qty': 1,
                }),
            ],
        })
        sale_02.action_confirm()
        sale_02.action_invoice_create()
        invoice_02 = sale_02.invoice_ids[0]
        invoice_02.action_invoice_open()
        wizard = self.env['account.invoice.export.a3erp'].with_context(
            active_ids=[invoice_01.id, invoice_02.id],
        ).create({})
        self.assertFalse(wizard.generated_file)
        with self.assertRaises(exceptions.ValidationError) as result:
            wizard.button_generate_invoice_a3erp_file()
        self.assertEqual(
            result.exception.name,
            'No more than one invoice can be generated per file.')

    def test_error_company_office_code(self):
        self.assertEqual(self.sale.state, 'draft')
        self.sale.action_confirm()
        self.assertEqual(self.sale.state, 'sale')
        self.assertEqual(len(self.sale.invoice_ids), 0)
        self.sale.action_invoice_create()
        self.assertEqual(len(self.sale.invoice_ids), 1)
        invoice = self.sale.invoice_ids[0]
        invoice.action_invoice_open()
        operation_type_a3erp = '9876'
        tax_type_a3erp = '5432'
        invoice.payment_mode_id.operation_type_a3erp = operation_type_a3erp
        invoice.payment_mode_id.tax_type_a3erp = tax_type_a3erp
        self.company.company_code_a3erp = False
        self.company.office_code_a3erp = False
        export_a3erp_obj = self.env['account.invoice.export.a3erp']
        wizard = export_a3erp_obj.with_context(
            active_ids=invoice.ids,
            active_id=invoice.ids[0],
        ).create({})
        with self.assertRaises(exceptions.ValidationError) as result:
            wizard.button_generate_invoice_a3erp_file()
        self.assertEqual(
            result.exception.name,
            'Company code for a3ERP is not defined in company %s.' % (
                invoice.company_id.name))
        self.company.company_code_a3erp = '3948'
        export_a3erp_obj = self.env['account.invoice.export.a3erp']
        wizard = export_a3erp_obj.with_context(
            active_ids=invoice.ids,
            active_id=invoice.ids[0],
        ).create({})
        with self.assertRaises(exceptions.ValidationError) as result:
            wizard.button_generate_invoice_a3erp_file()
        self.assertEqual(
            result.exception.name,
            'Office code for a3ERP is not defined in company %s.' % (
                invoice.company_id.name))

    def test_error_payment_mode(self):
        self.assertEqual(self.sale.state, 'draft')
        self.sale.action_confirm()
        self.assertEqual(self.sale.state, 'sale')
        self.assertEqual(len(self.sale.invoice_ids), 0)
        self.sale.action_invoice_create()
        self.assertEqual(len(self.sale.invoice_ids), 1)
        invoice = self.sale.invoice_ids[0]
        invoice.action_invoice_open()
        self.assertTrue(invoice.date_invoice)
        self.assertTrue(invoice.date_due)
        invoice.payment_mode_id = False
        self.assertFalse(invoice.payment_mode_id)
        payment = self.env['account.payment'].with_context(
            active_model='account.invoice',
            active_id=invoice.id,
            active_ids=invoice.ids,
        ).create({
            'name': self.sale.name,
            'payment_method_id': self.payment_method.id,
            'journal_id': self.journal.id,
        })
        payment.action_validate_invoice_payment()
        export_a3erp_obj = self.env['account.invoice.export.a3erp']
        wizard = export_a3erp_obj.with_context(
            active_ids=invoice.ids,
            active_id=invoice.ids[0],
        ).create({})
        with self.assertRaises(exceptions.ValidationError) as result:
            wizard.button_generate_operation_a3erp_file()
        self.assertEqual(
            result.exception.name,
            'The invoice has no payment method.')

    def test_error_no_payment(self):
        self.assertEqual(self.sale.state, 'draft')
        self.sale.action_confirm()
        self.assertEqual(self.sale.state, 'sale')
        self.assertEqual(len(self.sale.invoice_ids), 0)
        self.sale.action_invoice_create()
        self.assertEqual(len(self.sale.invoice_ids), 1)
        invoice = self.sale.invoice_ids[0]
        invoice.action_invoice_open()
        self.assertTrue(invoice.date_invoice)
        self.assertTrue(invoice.date_due)
        invoice.payment_mode_id = False
        self.assertFalse(invoice.payment_mode_id)
        export_a3erp_obj = self.env['account.invoice.export.a3erp']
        wizard = export_a3erp_obj.with_context(
            active_ids=invoice.ids,
            active_id=invoice.ids[0],
        ).create({})
        with self.assertRaises(exceptions.ValidationError) as result:
            wizard.button_generate_operation_a3erp_file()
        self.assertEqual(
            result.exception.name,
            'The invoice has no payment.')

    def test_error_payment_operation_tax_type(self):
        self.assertEqual(self.sale.state, 'draft')
        self.sale.action_confirm()
        self.assertEqual(self.sale.state, 'sale')
        self.assertEqual(len(self.sale.invoice_ids), 0)
        self.sale.action_invoice_create()
        self.assertEqual(len(self.sale.invoice_ids), 1)
        invoice = self.sale.invoice_ids[0]
        invoice.action_invoice_open()
        self.assertTrue(invoice.date_invoice)
        self.assertTrue(invoice.date_due)
        payment = self.env['account.payment'].with_context(
            active_model='account.invoice',
            active_id=invoice.id,
            active_ids=invoice.ids,
        ).create({
            'name': self.sale.name,
            'payment_method_id': self.payment_method.id,
            'journal_id': self.journal.id,
        })
        payment.action_validate_invoice_payment()
        operation_type_a3erp = False
        invoice.payment_mode_id.operation_type_a3erp = operation_type_a3erp
        export_a3erp_obj = self.env['account.invoice.export.a3erp']
        wizard = export_a3erp_obj.with_context(
            active_ids=invoice.ids,
            active_id=invoice.ids[0],
        ).create({})
        with self.assertRaises(exceptions.ValidationError) as result:
            wizard.button_generate_operation_a3erp_file()
        self.assertEqual(
            result.exception.name,
            'The payment mode has no operation code for a3ERP.')
        operation_type_a3erp = '9876'
        tax_type_a3erp = False
        invoice.payment_mode_id.operation_type_a3erp = operation_type_a3erp
        invoice.payment_mode_id.tax_type_a3erp = tax_type_a3erp
        wizard = export_a3erp_obj.with_context(
            active_ids=invoice.ids,
            active_id=invoice.ids[0],
        ).create({})
        with self.assertRaises(exceptions.ValidationError) as result:
            wizard.button_generate_operation_a3erp_file()
        self.assertEqual(
            result.exception.name,
            'The payment mode has no tax type for a3ERP.')
