###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
import json

from odoo import exceptions, fields
from odoo.tests.common import HttpCase


class TestSaleOrderImportJson(HttpCase):

    def setUp(self):
        super().setUp()
        self.partner_1 = self.env['res.partner'].create({
            'name': 'Partner test 1',
            'street': 'Partner street 1',
            'email': 'partner@partner.com',
        })
        self.partner_2 = self.env['res.partner'].create({
            'name': 'Partner test 2',
            'street': 'Partner street 2',
            'email': 'partner@partner.es',
        })
        self.tax = self.env['account.tax'].create({
            'name': 'Tax test 21%',
            'type_tax_use': 'sale',
            'amount_type': 'percent',
            'amount': 21,
        })
        self.product_1 = self.env['product.product'].create({
            'type': 'consu',
            'company_id': False,
            'name': 'Product Test 1',
            'standard_price': 10,
            'list_price': 100,
            'default_code': 'TEST-01',
            'taxes_id': [
                (6, 0, [self.tax.id]),
            ],
        })
        self.product_2 = self.env['product.product'].create({
            'type': 'consu',
            'company_id': False,
            'name': 'Product Test 2',
            'standard_price': 10,
            'list_price': 100,
            'default_code': 'TEST-02',
            'taxes_id': [
                (6, 0, [self.tax.id]),
            ],
        })
        self.product_copy = self.env['product.product'].create({
            'type': 'consu',
            'company_id': False,
            'name': 'Product Test 3',
            'standard_price': 10,
            'list_price': 100,
            'default_code': 'E-COM11',
            'taxes_id': [
                (6, 0, [self.tax.id]),
            ],
        })
        self.data_json = {
            'name': 'SO164',
            'partner': {
                'name': 'Customer',
                'street': 'Customer Street',
                'email': 'new@partner.com',
            },
            'order_line': [
                {
                    'default_code': 'TEST-01',
                    'product_uom_qty': 1,
                    'price_unit_taxed': 95.59,
                    'price_unit_untaxed': 79,
                },
                {
                    'default_code': 'TEST-02',
                    'product_uom_qty': 2,
                    'price_unit_taxed': 30.25,
                    'price_unit_untaxed': 25,
                },
            ],
            'state': 'confirmed',
            'warehouse_id': 1,
        }
        self.account_type = self.env.ref('account.data_account_type_receivable')
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
        self.payment_method = self.env['account.payment.method'].create({
            'name': 'Method Test',
            'code': 'CODTEST',
            'payment_type': 'inbound',
        })

    def test_url(self):
        self.authenticate('admin', 'admin')
        self.opener.headers.update({
            'Content-type': 'application/json',
            'Accept': 'text/plain',
        })
        date = fields.Datetime.now().strftime('%Y-%m-%d')
        self.data_json.update({
            'journal_name': self.journal.name,
            'invoice_date': date,
            'payment_method_name': self.payment_method.name,
        })
        response = self.url_open(
            '/sale_order/import', data=json.dumps(self.data_json))
        self.assertEqual(response.status_code, 200)

    def test_sale_order_confirmed(self):
        self.data_json.update({
            'name': 'SO918',
            'journal_name': self.journal.name,
            'invoice_date': fields.Date.today(),
            'payment_method_name': self.payment_method.name,
        })
        result = self.env['sale.order'].json_import(self.data_json)
        sales = self.env['sale.order'].search([('id', '=', result)])
        self.assertEqual(len(sales), 1)
        self.assertEqual(sales.name, self.data_json['name'])
        self.assertEqual(
            sales.partner_id.name,
            self.data_json['partner']['name'])
        self.assertEqual(
            sales.partner_id.street,
            self.data_json['partner']['street'])
        self.assertEqual(
            sales.partner_id.email,
            self.data_json['partner']['email'])
        line_product1 = sales.order_line.filtered(
            lambda ln: ln.product_id.default_code == 'TEST-01')
        self.assertTrue(line_product1)
        self.assertEqual(line_product1.product_uom_qty, 1)
        self.assertEqual(line_product1.price_unit, 79)
        total_product1 = (
            line_product1.price_unit * line_product1.product_uom_qty)
        line_product2 = sales.order_line.filtered(
            lambda ln: ln.product_id.default_code == 'TEST-02')
        self.assertTrue(line_product2)
        self.assertEqual(line_product2.product_uom_qty, 2)
        self.assertEqual(line_product2.price_unit, 25)
        total_product2 = (
            line_product2.price_unit * line_product2.product_uom_qty)
        self.assertEqual(sales.state, 'sale')
        total_product1 = (
            self.data_json['order_line'][0]['price_unit_taxed'] * (
                self.data_json['order_line'][0]['product_uom_qty']))
        total_product2 = (
            self.data_json['order_line'][1]['price_unit_taxed'] * (
                self.data_json['order_line'][1]['product_uom_qty']))
        self.assertEqual(
            sales.amount_total, total_product1 + total_product2)

    def test_sale_order_unconfirmed(self):
        self.data_json.update({
            'name': 'SO112',
            'partner': {
                'name': 'Tomer',
                'street': 'Custom Street',
                'email': 'cust@mail.com',
            },
            'state': '',
        })
        result = self.env['sale.order'].json_import(self.data_json)
        sales = self.env['sale.order'].search([('id', '=', result)])
        self.assertEqual(len(sales), 1)
        self.assertEqual(sales.name, self.data_json['name'])
        self.assertEqual(
            sales.partner_id.name,
            self.data_json['partner']['name'])
        self.assertEqual(
            sales.partner_id.street,
            self.data_json['partner']['street'])
        self.assertEqual(
            sales.partner_id.email,
            self.data_json['partner']['email'])
        line_product1 = sales.order_line.filtered(
            lambda ln: ln.product_id.default_code == 'TEST-01')
        self.assertTrue(line_product1)
        self.assertEqual(line_product1.product_uom_qty, 1)
        self.assertEqual(line_product1.price_unit, 79)
        line_product2 = sales.order_line.filtered(
            lambda ln: ln.product_id.default_code == 'TEST-02')
        self.assertTrue(line_product2)
        self.assertEqual(line_product2.product_uom_qty, 2)
        self.assertEqual(line_product2.price_unit, 25)
        total_product1 = (
            self.data_json['order_line'][0]['price_unit_taxed'] * (
                self.data_json['order_line'][0]['product_uom_qty']))
        total_product2 = (
            self.data_json['order_line'][1]['price_unit_taxed'] * (
                self.data_json['order_line'][1]['product_uom_qty']))
        self.assertEqual(
            sales.amount_total, total_product1 + total_product2)
        self.assertNotEqual(sales.state, 'sale')
        self.assertEqual(sales.state, 'draft')
        self.assertEqual(len(sales.invoice_ids), 0)

    def test_error_product_not_exist(self):
        self.data_json['order_line'][0]['default_code'] = 'CODE-NOT-EXISTS'
        with self.assertRaises(exceptions.ValidationError) as result:
            self.env['sale.order'].json_import(self.data_json)
        self.assertEqual(
            result.exception.name,
            'Product with code CODE-NOT-EXISTS not exist')

    def test_not_valid_json(self):
        self.data_json['order_line'][0]['product_uom_qty'] = 'xxx1'
        with self.assertRaises(Exception):
            self.env['sale.order'].json_import(self.data_json)

    def test_error_products_with_same_code(self):
        self.data_json['order_line'][0]['default_code'] = 'E-COM11'
        with self.assertRaises(exceptions.ValidationError) as result:
            self.env['sale.order'].json_import(self.data_json)
        self.assertEqual(
            result.exception.name, 'Many products with same code E-COM11')

    def test_note(self):
        self.data_json['note'] = 'Test note'
        self.data_json['state'] = ''
        result = self.env['sale.order'].json_import(self.data_json)
        sales = self.env['sale.order'].search([('id', '=', result)])
        self.assertEqual(len(sales), 1)
        self.assertEqual(sales.note, self.data_json['note'])

    def test_partner_shipping(self):
        self.data_json['partner_shipping'] = {
            'name': 'Shipping',
            'street': 'Custom street',
            'email': 'email@customer.com',
        }
        self.data_json['state'] = ''
        result = self.env['sale.order'].json_import(self.data_json)
        sales = self.env['sale.order'].search([('id', '=', result)])
        self.assertEqual(len(sales), 1)
        self.assertEqual(sales.partner_shipping_id.name, 'Shipping')
        self.assertEqual(sales.partner_id.name, 'Customer')

    def test_payment_transaction_accepted(self):
        self.data_json.update({
            'name': 'SO654',
            'journal_name': self.journal.name,
            'invoice_date': fields.Date.today(),
            'payment_method_name': self.payment_method.name,
        })
        result = self.env['sale.order'].json_import(self.data_json)
        sales = self.env['sale.order'].search([('id', '=', result)])
        self.assertEqual(len(sales), 1)
        self.assertEqual(sales.name, self.data_json['name'])
        self.assertEqual(
            sales.partner_id.name,
            self.data_json['partner']['name'])
        self.assertEqual(
            sales.partner_id.street,
            self.data_json['partner']['street'])
        self.assertEqual(
            sales.partner_id.email,
            self.data_json['partner']['email'])
        line_product1 = sales.order_line.filtered(
            lambda ln: ln.product_id.default_code == 'TEST-01')
        self.assertTrue(line_product1)
        self.assertEqual(line_product1.product_uom_qty, 1)
        self.assertEqual(line_product1.price_unit, 79)
        total_product1 = (
            line_product1.price_unit * line_product1.product_uom_qty)
        line_product2 = sales.order_line.filtered(
            lambda ln: ln.product_id.default_code == 'TEST-02')
        self.assertTrue(line_product2)
        self.assertEqual(line_product2.product_uom_qty, 2)
        self.assertEqual(line_product2.price_unit, 25)
        total_product2 = (
            line_product2.price_unit * line_product2.product_uom_qty)
        self.assertEqual(sales.state, 'sale')
        total_product1 = (
            self.data_json['order_line'][0]['price_unit_taxed'] * (
                self.data_json['order_line'][0]['product_uom_qty']))
        total_product2 = (
            self.data_json['order_line'][1]['price_unit_taxed'] * (
                self.data_json['order_line'][1]['product_uom_qty']))
        self.assertEqual(
            sales.amount_total, total_product1 + total_product2)
        invoices = sales.invoice_ids
        self.assertEqual(len(invoices), 1)
        invoice = invoices[0]
        self.assertEqual(invoice.state, 'paid')
        self.assertEqual(invoice.amount_total, sales.amount_total)
        self.assertEqual(invoice.origin, self.data_json['name'])
        self.assertEqual(invoice.date_invoice, self.data_json['invoice_date'])
        payments = invoice.payment_ids
        self.assertEqual(len(payments), 1)
        payment = payments[0]
        self.assertEqual(payment.journal_id, self.journal)
        self.assertEqual(payment.payment_method_id, self.payment_method)
        self.assertEqual(payment.payment_date, fields.Date.today())

    def test_payment_transaction_error_not_journal_found(self):
        journal_name = 'Journal Test'
        self.data_json.update({
            'name': 'SO654',
            'journal_name': journal_name,
            'invoice_date': fields.Date.today(),
            'payment_method_name': self.payment_method.name,
        })
        with self.assertRaises(exceptions.ValidationError) as result:
            self.env['sale.order'].json_import(self.data_json)
        self.assertEqual(
            result.exception.name,
            'Journal with name "%s" not found' % journal_name)

    def test_payment_transaction_error_multiple_journal_found(self):
        journal_name = 'Customer Invoices - Test'
        journal = self.env['account.journal'].create({
            'name': journal_name,
            'code': 'TTEST',
            'type': 'sale',
            'default_credit_account_id': self.account.id,
            'default_debit_account_id': self.account.id,
            'refund_sequence': True,
        })
        self.data_json.update({
            'name': 'SO654',
            'journal_name': journal.name,
            'invoice_date': fields.Date.today(),
            'payment_method_name': self.payment_method.name,
        })
        with self.assertRaises(exceptions.ValidationError) as result:
            self.env['sale.order'].json_import(self.data_json)
        self.assertEqual(
            result.exception.name,
            'Multiple journals with same name "%s"' % journal_name)

    def test_payment_transaction_payment_method_error_not_found(self):
        payment_method_name = 'Test Method'
        self.data_json.update({
            'name': 'SO654',
            'journal_name': self.journal.name,
            'invoice_date': fields.Date.today(),
            'payment_method_name': payment_method_name,
        })
        with self.assertRaises(exceptions.ValidationError) as result:
            self.env['sale.order'].json_import(self.data_json)
        self.assertEqual(
            result.exception.name,
            'Payment method with name "%s" not found' % payment_method_name)

    def test_payment_transaction_error_multiple_payment_method(self):
        payment_method_name = 'Method Test'
        payment_method = self.env['account.payment.method'].create({
            'name': payment_method_name,
            'code': 'TESTCOD',
            'payment_type': 'inbound',
        })
        self.data_json.update({
            'name': 'SO654',
            'journal_name': self.journal.name,
            'invoice_date': fields.Date.today(),
            'payment_method_name': payment_method.name,
        })
        with self.assertRaises(exceptions.ValidationError) as result:
            self.env['sale.order'].json_import(self.data_json)
        self.assertEqual(
            result.exception.name,
            'Multiple payment method with same name "%s"' % payment_method_name)

    def test_add_team_id(self):
        team_name = 'Sales team test'
        team = self.env['crm.team'].create({
            'name': team_name,
        })
        self.data_json.update({
            'name': 'SO218',
            'journal_name': self.journal.name,
            'invoice_date': fields.Date.today(),
            'payment_method_name': self.payment_method.name,
            'team_name': team_name,
        })
        result = self.env['sale.order'].json_import(self.data_json)
        sales = self.env['sale.order'].search([('id', '=', result)])
        self.assertEqual(len(sales), 1)
        self.assertEqual(sales.name, self.data_json['name'])
        self.assertEqual(sales.team_id.id, team.id)

    def test_team_id_not_found(self):
        team_name = 'Sales team test'
        self.data_json.update({
            'name': 'SO915',
            'team_name': team_name,
            'state': '',
        })
        with self.assertRaises(exceptions.ValidationError) as result:
            self.env['sale.order'].json_import(self.data_json)
        self.assertEqual(
            result.exception.name,
            'Sales team with name "%s" not found' % team_name)

    def test_multiple_team_id_with_same_name(self):
        team_name = 'Sales team test'
        self.env['crm.team'].create({
            'name': team_name,
        })
        self.env['crm.team'].create({
            'name': team_name,
        })
        self.data_json.update({
            'name': 'SO317',
            'team_name': team_name,
            'state': '',
        })
        with self.assertRaises(exceptions.ValidationError) as result:
            self.env['sale.order'].json_import(self.data_json)
        self.assertEqual(
            result.exception.name,
            'Multiple sales team with same name "%s"' % team_name)

    def test_team_id_empty(self):
        team_name = 'Sales team test'
        self.env['crm.team'].create({
            'name': team_name,
        })
        self.data_json.update({
            'name': 'SO551',
            'team_name': '',
            'state': '',
        })
        result = self.env['sale.order'].json_import(self.data_json)
        sales = self.env['sale.order'].search([('id', '=', result)])
        self.assertEqual(len(sales), 1)
        self.assertEqual(sales.name, self.data_json['name'])
        self.assertEqual(len(sales.team_id), 0)

    def test_error_field_name_team_id_in_json(self):
        team_name = 'Sales_team test'
        self.env['crm.team'].create({
            'name': team_name,
        })
        self.data_json.update({
            'name': 'TEST01',
            'team_error': '',
            'journal_name': self.journal.name,
            'invoice_date': fields.Date.today(),
            'payment_method_name': self.payment_method.name,
        })
        result = self.env['sale.order'].json_import(self.data_json)
        sales = self.env['sale.order'].search([('id', '=', result)])
        self.assertEqual(len(sales), 1)
        self.assertEqual(sales.name, self.data_json['name'])
        self.assertEqual(len(sales.team_id), 0)
        invoices = sales.invoice_ids
        self.assertEqual(len(invoices), 1)
        invoice = invoices[0]
        self.assertEqual(invoice.state, 'paid')
        self.assertEqual(invoice.amount_total, sales.amount_total)
        self.assertEqual(invoice.origin, self.data_json['name'])
        self.assertEqual(invoice.date_invoice, self.data_json['invoice_date'])
        payments = invoice.payment_ids
        self.assertEqual(len(payments), 1)
        payment = payments[0]
        self.assertEqual(payment.journal_id, self.journal)
        self.assertEqual(payment.payment_method_id, self.payment_method)
        self.assertEqual(payment.payment_date, fields.Date.today())

    def test_payment_journal_id_not_found_in_json(self):
        self.data_json.update({
            'name': 'TEST/OPT1',
            'invoice_date': fields.Date.today(),
            'payment_method_name': self.payment_method.name,
        })
        result = self.env['sale.order'].json_import(self.data_json)
        sales = self.env['sale.order'].search([('id', '=', result)])
        self.assertEqual(len(sales), 1)
        self.assertEqual(sales.name, self.data_json['name'])
        invoices = sales.invoice_ids
        self.assertEqual(len(invoices), 1)
        invoice = invoices[0]
        self.assertEqual(invoice.state, 'paid')
        self.assertEqual(invoice.amount_total, sales.amount_total)
        self.assertEqual(invoice.origin, self.data_json['name'])
        self.assertEqual(invoice.date_invoice, self.data_json['invoice_date'])
        payments = invoice.payment_ids
        self.assertEqual(len(payments), 1)
        payment = payments[0]
        self.assertNotEqual(payment.journal_id, self.journal)
        self.assertEqual(payment.payment_method_id, self.payment_method)
        self.assertEqual(payment.payment_date, fields.Date.today())
        self.assertEqual(payment.journal_id, invoice.journal_id)

    def test_payment_journal_id_empty_in_json(self):
        self.data_json.update({
            'name': 'TEST/OPT2',
            'journal_name': '',
            'invoice_date': fields.Date.today(),
            'payment_method_name': self.payment_method.name,
        })
        result = self.env['sale.order'].json_import(self.data_json)
        sales = self.env['sale.order'].search([('id', '=', result)])
        self.assertEqual(len(sales), 1)
        self.assertEqual(sales.name, self.data_json['name'])
        invoices = sales.invoice_ids
        self.assertEqual(len(invoices), 1)
        invoice = invoices[0]
        self.assertEqual(invoice.state, 'paid')
        self.assertEqual(invoice.amount_total, sales.amount_total)
        self.assertEqual(invoice.origin, self.data_json['name'])
        self.assertEqual(invoice.date_invoice, self.data_json['invoice_date'])
        payments = invoice.payment_ids
        self.assertEqual(len(payments), 1)
        payment = payments[0]
        self.assertNotEqual(payment.journal_id, self.journal)
        self.assertEqual(payment.journal_id, invoice.journal_id)
        self.assertEqual(payment.payment_method_id, self.payment_method)
        self.assertEqual(payment.payment_date, fields.Date.today())

    def test_same_name_payment_and_sale_order(self):
        self.data_json.update({
            'name': 'TEST/OPT3',
            'journal_name': self.journal.name,
            'invoice_date': fields.Date.today(),
            'payment_method_name': self.payment_method.name,
        })
        result = self.env['sale.order'].json_import(self.data_json)
        sales = self.env['sale.order'].search([('id', '=', result)])
        self.assertEqual(len(sales), 1)
        self.assertEqual(sales.name, self.data_json['name'])
        invoices = sales.invoice_ids
        self.assertEqual(len(invoices), 1)
        invoice = invoices[0]
        self.assertEqual(invoice.state, 'paid')
        self.assertEqual(invoice.amount_total, sales.amount_total)
        self.assertEqual(invoice.origin, self.data_json['name'])
        self.assertEqual(invoice.date_invoice, self.data_json['invoice_date'])
        payments = invoice.payment_ids
        self.assertEqual(len(payments), 1)
        payment = payments[0]
        self.assertEqual(payment.journal_id, self.journal)
        self.assertEqual(payment.payment_method_id, self.payment_method)
        self.assertEqual(payment.payment_date, fields.Date.today())
        self.assertEqual(payment.name, sales.name)

    def test_search_by_barcode_in_default_code(self):
        barcode = '7501031311309'
        self.data_json.update({
            'name': 'SO215',
            'journal_name': self.journal.name,
            'invoice_date': fields.Date.today(),
            'payment_method_name': self.payment_method.name,
        })
        self.product_1.write({
            'barcode': barcode,
        })
        self.data_json['order_line'][0]['default_code'] = barcode
        result = self.env['sale.order'].json_import(self.data_json)
        sales = self.env['sale.order'].search([('id', '=', result)])
        self.assertEqual(len(sales), 1)
        self.assertEqual(sales.name, self.data_json['name'])
        order_line = self.env['sale.order.line'].search([
            ('order_id', '=', result),
            ('product_id', '=', self.product_1.id),
        ])
        self.assertEqual(len(order_line), 1)
        self.assertEqual(order_line.product_id.barcode, self.product_1.barcode)

    def test_error_product_barcode_not_exist(self):
        barcode = '1112223334445'
        self.data_json['order_line'][0]['default_code'] = barcode
        with self.assertRaises(exceptions.ValidationError) as result:
            self.env['sale.order'].json_import(self.data_json)
        self.assertEqual(
            result.exception.name,
            'Product with code %s not exist' % barcode)
