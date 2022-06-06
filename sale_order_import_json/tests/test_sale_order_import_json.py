###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
import base64
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
            'payment_journal_name': 'Bank test',
        }
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
        self.journal_bank = self.env['account.journal'].create({
            'name': 'Bank test',
            'code': 'BNKT',
            'type': 'bank',
            'default_credit_account_id': self.account.id,
            'default_debit_account_id': self.account.id,
        })
        self.payment_method = self.env['account.payment.method'].create({
            'name': 'Method Test',
            'code': 'CODTEST',
            'payment_type': 'inbound',
        })
        self.free_delivery = self.env.ref('delivery.free_delivery_carrier')

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
        self.assertFalse(self.free_delivery.include_cheapest_carrier)
        self.free_delivery.include_cheapest_carrier = True
        self.assertTrue(self.free_delivery.include_cheapest_carrier)
        self.data_json.update({
            'name': 'SO918',
            'journal_name': self.journal.name,
            'invoice_date': '2022-01-01',
            'payment_method_name': self.payment_method.name,
        })
        result = self.env['sale.order'].json_import(self.data_json)
        attach = self.env['ir.attachment'].search([
            ('res_id', '=', result),
            ('res_model', '=', 'sale.order'),
        ])
        self.assertEqual(len(attach), 1)
        data = json.loads(base64.b64decode(attach.datas))
        self.assertEqual(data.get('name'), 'SO918')
        sales = self.env['sale.order'].search([('id', '=', result)])
        self.assertEqual(len(sales), 1)
        self.assertEqual(result, sales.id)
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
        self.assertEqual(len(sales[0].picking_ids), 1)
        self.assertNotEqual(sales[0].picking_ids.state, 'done')

    def test_sale_order_unconfirmed(self):
        self.assertFalse(self.free_delivery.include_cheapest_carrier)
        self.free_delivery.include_cheapest_carrier = True
        self.assertTrue(self.free_delivery.include_cheapest_carrier)
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

    def test_sale_order_import_supplierinfo(self):
        self.env['product.supplierinfo'].create({
            'name': self.partner_2.id,
            'product_tmpl_id': self.product_1.product_tmpl_id.id,
            'product_code': 'SUPPLIER_CODE_BY_DEFAULT',
            'route_select': 'product',
            'sequence': 1,
        })
        supplierinfo = self.env['product.supplierinfo'].create({
            'name': self.partner_1.id,
            'product_tmpl_id': self.product_1.product_tmpl_id.id,
            'product_code': 'SUPPLIER_CODE',
            'route_select': 'product',
            'sequence': 10,
        })
        self.data_json.update({
            'state': False,
            'order_line': [
                {
                    'default_code': 'SUPPLIER_CODE',
                    'product_uom_qty': 1,
                    'price_unit_taxed': 95.59,
                    'price_unit_untaxed': 79,
                },
            ]
        })
        self.free_delivery.include_cheapest_carrier = True
        result = self.env['sale.order'].json_import(self.data_json)
        sale = self.env['sale.order'].browse(result)
        self.assertEqual(sale.order_line.product_id, self.product_1)
        self.assertEqual(sale.order_line.product_id, self.product_1)
        if 'supplierinfo_id' in sale.order_line._fields:
            self.assertEqual(sale.order_line.supplierinfo_id, supplierinfo)
            self.assertEqual(sale.order_line.vendor_id, self.partner_1)

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
        self.assertFalse(self.free_delivery.include_cheapest_carrier)
        self.free_delivery.include_cheapest_carrier = True
        self.assertTrue(self.free_delivery.include_cheapest_carrier)
        self.data_json['note'] = 'Test note'
        self.data_json['state'] = ''
        result = self.env['sale.order'].json_import(self.data_json)
        sales = self.env['sale.order'].search([('id', '=', result)])
        self.assertEqual(len(sales), 1)
        self.assertEqual(sales.note, self.data_json['note'])

    def test_partner_shipping(self):
        self.assertFalse(self.free_delivery.include_cheapest_carrier)
        self.free_delivery.include_cheapest_carrier = True
        self.assertTrue(self.free_delivery.include_cheapest_carrier)
        self.data_json['partner_shipping'] = {
            'name': 'Shipping',
            'street': 'Custom street',
            'street2': 'Custom street 2',
            'phone': '666554433',
            'city': 'City test',
            'email': 'email@customer.com',
        }
        self.data_json['state'] = ''
        result = self.env['sale.order'].json_import(self.data_json)
        sales = self.env['sale.order'].search([('id', '=', result)])
        self.assertEqual(len(sales), 1)
        self.assertEqual(sales.partner_shipping_id.name, 'Shipping')
        self.assertEqual(sales.partner_id.name, 'Customer')

    def test_payment_transaction_accepted(self):
        self.assertFalse(self.free_delivery.include_cheapest_carrier)
        self.free_delivery.include_cheapest_carrier = True
        self.assertTrue(self.free_delivery.include_cheapest_carrier)
        bank_journal = self.env['account.journal'].create({
            'name': 'Bank Test',
            'code': 'TBNK',
            'type': 'bank',
        })
        team = self.env['crm.team'].create({
            'name': 'Sales team test',
            'import_payment_journal_id': bank_journal.id,
        })
        self.data_json.update({
            'name': 'SO654',
            'team_name': 'Sales team test',
            'journal_name': self.journal.name,
            'invoice_date': '2022-01-01',
            'payment_method_name': self.payment_method.name,
            'payment_journal_name': False,
        })
        result = self.env['sale.order'].json_import(self.data_json)
        sales = self.env['sale.order'].search([('id', '=', result)])
        self.assertEqual(len(sales), 1)
        self.assertEqual(sales.name, self.data_json['name'])
        self.assertEqual(sales.team_id, team)
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
        self.assertEqual(
            invoice.date_invoice.strftime('%Y-%m-%d'),
            self.data_json['invoice_date'])
        payments = invoice.payment_ids
        self.assertEqual(len(payments), 1)
        payment = payments[0]
        self.assertEqual(
            payment.journal_id, invoice.team_id.import_payment_journal_id)
        self.assertEqual(payment.payment_method_id, self.payment_method)
        self.assertEqual(
            payment.payment_date.strftime('%Y-%m-%d'), '2022-01-01')

    def test_payment_transaction_error_not_journal_found(self):
        self.assertFalse(self.free_delivery.include_cheapest_carrier)
        self.free_delivery.include_cheapest_carrier = True
        self.assertTrue(self.free_delivery.include_cheapest_carrier)
        journal_name = 'Journal Test'
        self.data_json.update({
            'name': 'SO654',
            'journal_name': journal_name,
            'payment_journal_name': 'Unknow',
            'invoice_date': '2022-01-01',
            'payment_method_name': self.payment_method.name,
        })
        with self.assertRaises(exceptions.ValidationError) as result:
            self.env['sale.order'].json_import(self.data_json)
        self.assertEquals(
            'Journal with name "Unknow" not found',
            result.exception.name)

    def test_payment_transaction_payment_method_error_not_found(self):
        self.assertFalse(self.free_delivery.include_cheapest_carrier)
        self.free_delivery.include_cheapest_carrier = True
        self.assertTrue(self.free_delivery.include_cheapest_carrier)
        payment_method_name = 'Test Method'
        self.data_json.update({
            'name': 'SO654',
            'journal_name': self.journal.name,
            'invoice_date': '2022-01-01',
            'payment_method_name': payment_method_name,
        })
        with self.assertRaises(exceptions.ValidationError) as result:
            self.env['sale.order'].json_import(self.data_json)
        self.assertEqual(
            result.exception.name,
            'Payment method with name "%s" not found' % payment_method_name)

    def test_payment_transaction_error_multiple_payment_method(self):
        self.assertFalse(self.free_delivery.include_cheapest_carrier)
        self.free_delivery.include_cheapest_carrier = True
        self.assertTrue(self.free_delivery.include_cheapest_carrier)
        method_name = 'Method Test'
        payment_method = self.env['account.payment.method'].create({
            'name': method_name,
            'code': 'TESTCOD',
            'payment_type': 'inbound',
        })
        self.data_json.update({
            'name': 'SO654',
            'journal_name': self.journal.name,
            'invoice_date': '2022-01-01',
            'payment_method_name': payment_method.name,
        })
        with self.assertRaises(exceptions.ValidationError) as result:
            self.env['sale.order'].json_import(self.data_json)
        self.assertEqual(
            result.exception.name,
            'Multiple payment method with same name "%s"' % method_name)

    def test_add_team_id(self):
        self.assertFalse(self.free_delivery.include_cheapest_carrier)
        self.free_delivery.include_cheapest_carrier = True
        self.assertTrue(self.free_delivery.include_cheapest_carrier)
        team_name = 'Sales team test'
        team = self.env['crm.team'].create({
            'name': team_name,
        })
        self.data_json.update({
            'name': 'SO218',
            'journal_name': self.journal.name,
            'invoice_date': '2022-01-01',
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
        self.assertFalse(self.free_delivery.include_cheapest_carrier)
        self.free_delivery.include_cheapest_carrier = True
        self.assertTrue(self.free_delivery.include_cheapest_carrier)
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
        self.assertEqual(len(sales.team_id), 1)

    def test_error_field_name_team_id_in_json(self):
        self.assertFalse(self.free_delivery.include_cheapest_carrier)
        self.free_delivery.include_cheapest_carrier = True
        self.assertTrue(self.free_delivery.include_cheapest_carrier)
        team_name = 'Sales_team test'
        self.env['crm.team'].create({
            'name': team_name,
        })
        self.data_json.update({
            'name': 'TEST01',
            'team_error': '',
            'journal_name': self.journal.name,
            'invoice_date': '2022-01-01',
            'payment_method_name': self.payment_method.name,
        })
        result = self.env['sale.order'].json_import(self.data_json)
        sales = self.env['sale.order'].search([('id', '=', result)])
        self.assertEqual(len(sales), 1)
        self.assertEqual(sales.name, self.data_json['name'])
        self.assertEqual(len(sales.team_id), 1)
        invoices = sales.invoice_ids
        self.assertEqual(len(invoices), 1)
        invoice = invoices[0]
        self.assertEqual(invoice.state, 'paid')
        self.assertEqual(invoice.amount_total, sales.amount_total)
        self.assertEqual(invoice.origin, self.data_json['name'])
        self.assertEqual(
            invoice.date_invoice.strftime('%Y-%m-%d'),
            self.data_json['invoice_date'])
        payments = invoice.payment_ids
        self.assertEqual(len(payments), 1)
        payment = payments[0]
        self.assertEqual(payment.journal_id, self.journal_bank)
        self.assertEqual(payment.payment_method_id, self.payment_method)
        self.assertEqual(
            payment.payment_date.strftime('%Y-%m-%d'), '2022-01-01')

    def test_payment_journal_id_not_found_in_json(self):
        self.assertFalse(self.free_delivery.include_cheapest_carrier)
        self.free_delivery.include_cheapest_carrier = True
        self.assertTrue(self.free_delivery.include_cheapest_carrier)
        self.env['crm.team'].create({
            'name': 'Sales team test',
            'import_payment_journal_id': self.journal_bank.id,
        })
        self.data_json.update({
            'name': 'TEST/OPT1',
            'invoice_date': '2022-01-01',
            'payment_method_name': self.payment_method.name,
            'payment_journal_name': False,
            'team_name': 'Sales team test',
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
        self.assertEqual(
            invoice.date_invoice.strftime('%Y-%m-%d'),
            self.data_json['invoice_date'])
        payments = invoice.payment_ids
        self.assertEqual(len(payments), 1)
        payment = payments[0]
        self.assertNotEqual(payment.journal_id, self.journal)
        self.assertEqual(payment.payment_method_id, self.payment_method)
        self.assertEqual(
            payment.payment_date.strftime('%Y-%m-%d'), '2022-01-01')

    def test_payment_journal_id_empty_in_json(self):
        self.assertFalse(self.free_delivery.include_cheapest_carrier)
        self.free_delivery.include_cheapest_carrier = True
        self.assertTrue(self.free_delivery.include_cheapest_carrier)
        self.data_json.update({
            'name': 'TEST/OPT2',
            'journal_name': '',
            'invoice_date': '2022-01-01',
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
        self.assertEqual(
            invoice.date_invoice.strftime('%Y-%m-%d'),
            self.data_json['invoice_date'])
        payments = invoice.payment_ids
        self.assertEqual(len(payments), 1)
        payment = payments[0]
        self.assertNotEqual(payment.journal_id, self.journal)
        self.assertEqual(payment.journal_id, self.journal_bank)
        self.assertEqual(payment.payment_method_id, self.payment_method)
        self.assertEqual(
            payment.payment_date.strftime('%Y-%m-%d'), '2022-01-01')

    def test_same_name_payment_and_sale_order(self):
        self.assertFalse(self.free_delivery.include_cheapest_carrier)
        self.free_delivery.include_cheapest_carrier = True
        self.assertTrue(self.free_delivery.include_cheapest_carrier)
        self.data_json.update({
            'name': 'TEST/OPT3',
            'journal_name': self.journal.name,
            'invoice_date': '2022-01-01',
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
        self.assertEqual(
            invoice.date_invoice.strftime('%Y-%m-%d'),
            self.data_json['invoice_date'])
        payments = invoice.payment_ids
        self.assertEqual(len(payments), 1)
        payment = payments[0]
        self.assertEqual(payment.journal_id, self.journal_bank)
        self.assertEqual(payment.payment_method_id, self.payment_method)
        self.assertEqual(
            payment.payment_date.strftime('%Y-%m-%d'), '2022-01-01')
        self.assertEqual(payment.name, sales.name)

    def test_search_by_barcode_in_default_code(self):
        self.assertFalse(self.free_delivery.include_cheapest_carrier)
        self.free_delivery.include_cheapest_carrier = True
        self.assertTrue(self.free_delivery.include_cheapest_carrier)
        barcode = '7501031311309'
        self.data_json.update({
            'name': 'SO215',
            'journal_name': self.journal.name,
            'invoice_date': '2022-01-01',
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

    def test_cost_from_stock_picking(self):
        self.assertFalse(self.free_delivery.include_cheapest_carrier)
        self.free_delivery.include_cheapest_carrier = True
        self.assertTrue(self.free_delivery.include_cheapest_carrier)
        self.data_json.update({
            'name': 'SOCOST',
            'journal_name': self.journal.name,
            'invoice_date': '2022-01-01',
            'payment_method_name': self.payment_method.name,
            'delivery_cost_to_sale_order': True,
        })
        result = self.env['sale.order'].json_import(self.data_json)
        sales = self.env['sale.order'].search([('id', '=', result)])
        self.assertEqual(len(sales), 1)
        self.assertEqual(len(sales.picking_ids), 1)
        picking = sales.picking_ids[0]
        for move in picking.move_lines:
            move.quantity_done = move.product_uom_qty
        picking.action_done()
        self.assertEqual(sales.name, self.data_json['name'])
        self.assertTrue(sales.delivery_cost_to_sale_order)
        self.assertEqual(sales.carrier_id, self.free_delivery)
        self.assertEqual(sales.delivery_price, self.free_delivery.fixed_price)
        self.assertEqual(len(sales.order_line), 3)
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
        line_delivery = sales.order_line.filtered(lambda ln: ln.is_delivery)
        self.assertTrue(line_delivery)
        self.assertEqual(line_delivery.product_uom_qty, 1)
        self.assertEqual(
            line_delivery.price_unit, self.free_delivery.fixed_price)
        self.assertEqual(sales.state, 'sale')
        total_product1 = (
            self.data_json['order_line'][0]['price_unit_taxed'] * (
                self.data_json['order_line'][0]['product_uom_qty']))
        total_product2 = (
            self.data_json['order_line'][1]['price_unit_taxed'] * (
                self.data_json['order_line'][1]['product_uom_qty']))
        self.assertEqual(
            sales.amount_total,
            total_product1 + total_product2 + line_delivery.price_unit)

    def test_assign_delivery_carrier_to_sale_order(self):
        self.data_json.update({
            'name': 'TESTCARRIER',
            'journal_name': self.journal.name,
            'invoice_date': '2022-01-01',
            'payment_method_name': self.payment_method.name,
            'carrier_id': self.free_delivery.name,
        })
        result = self.env['sale.order'].json_import(self.data_json)
        sales = self.env['sale.order'].search([('id', '=', result)])
        self.assertEqual(len(sales), 1)
        self.assertEqual(sales.name, self.data_json['name'])
        self.assertEqual(sales.carrier_id, self.free_delivery)

    def test_assign_carrier_with_empty_value_in_json(self):
        self.assertFalse(self.free_delivery.include_cheapest_carrier)
        self.free_delivery.include_cheapest_carrier = True
        self.assertTrue(self.free_delivery.include_cheapest_carrier)
        self.data_json.update({
            'name': 'TESTCARRIER',
            'journal_name': self.journal.name,
            'invoice_date': '2022-01-01',
            'payment_method_name': self.payment_method.name,
            'carrier_id': '',
        })
        result = self.env['sale.order'].json_import(self.data_json)
        sales = self.env['sale.order'].search([('id', '=', result)])
        self.assertEqual(len(sales), 1)
        self.assertEqual(sales.name, self.data_json['name'])
        self.assertEqual(sales.carrier_id, self.free_delivery)

    def test_assign_carrier_with_none_value_in_json(self):
        self.assertFalse(self.free_delivery.include_cheapest_carrier)
        self.free_delivery.include_cheapest_carrier = True
        self.assertTrue(self.free_delivery.include_cheapest_carrier)
        self.data_json.update({
            'name': 'TESTCARRIER',
            'journal_name': self.journal.name,
            'invoice_date': '2022-01-01',
            'payment_method_name': self.payment_method.name,
            'carrier_id': None,
        })
        result = self.env['sale.order'].json_import(self.data_json)
        sales = self.env['sale.order'].search([('id', '=', result)])
        self.assertEqual(len(sales), 1)
        self.assertEqual(sales.name, self.data_json['name'])
        self.assertEqual(sales.carrier_id, self.free_delivery)

    def test_assign_carrier_without_key_in_json(self):
        self.assertFalse(self.free_delivery.include_cheapest_carrier)
        self.free_delivery.include_cheapest_carrier = True
        self.assertTrue(self.free_delivery.include_cheapest_carrier)
        self.data_json.update({
            'name': 'TESTCARRIER',
            'journal_name': self.journal.name,
            'invoice_date': '2022-01-01',
            'payment_method_name': self.payment_method.name,
        })
        result = self.env['sale.order'].json_import(self.data_json)
        sales = self.env['sale.order'].search([('id', '=', result)])
        self.assertEqual(len(sales), 1)
        self.assertEqual(sales.name, self.data_json['name'])
        self.assertEqual(sales.carrier_id, self.free_delivery)

    def test_error_delivery_carrier_not_found(self):
        self.data_json.update({
            'name': 'TESTCARRIER',
            'journal_name': self.journal.name,
            'invoice_date': '2022-01-01',
            'payment_method_name': self.payment_method.name,
            'carrier_id': 'Carrier invented'
        })
        with self.assertRaises(exceptions.ValidationError) as result:
            self.env['sale.order'].json_import(self.data_json)
        self.assertEqual(
            result.exception.name,
            'Delivery carrier with name "Carrier invented" not found')

    def test_error_multiple_delivery_carrier_found(self):
        product_shipping_costs = self.env['product.product'].create({
            'type': 'service',
            'name': 'Shipping costs',
            'standard_price': 10,
            'list_price': 100,
        })
        self.env['delivery.carrier'].create({
            'name': 'Carrier duplicated',
            'delivery_type': 'fixed',
            'product_id': product_shipping_costs.id,
            'fixed_price': 12,
        })
        self.env['delivery.carrier'].create({
            'name': 'Carrier duplicated',
            'delivery_type': 'fixed',
            'product_id': product_shipping_costs.id,
            'fixed_price': 6,
        })
        self.data_json.update({
            'name': 'TESTCARRIER',
            'journal_name': self.journal.name,
            'invoice_date': '2022-01-01',
            'payment_method_name': self.payment_method.name,
            'carrier_id': 'Carrier duplicated',
        })
        with self.assertRaises(exceptions.ValidationError) as result:
            self.env['sale.order'].json_import(self.data_json)
        self.assertEqual(
            result.exception.name,
            'Multiple carriers with same name "Carrier duplicated"')

    def test_check_delivery_price(self):
        self.assertEqual(self.free_delivery.fixed_price, 0)
        self.free_delivery.fixed_price = 5
        self.data_json.update({
            'name': 'TESTCARRIER',
            'journal_name': self.journal.name,
            'invoice_date': '2022-01-01',
            'payment_method_name': self.payment_method.name,
            'carrier_id': self.free_delivery.name,
        })
        result = self.env['sale.order'].json_import(self.data_json)
        sales = self.env['sale.order'].search([('id', '=', result)])
        self.assertEqual(len(sales), 1)
        self.assertEqual(sales.name, self.data_json['name'])
        self.assertEqual(sales.carrier_id, self.free_delivery)
        self.assertEqual(sales.delivery_price, self.free_delivery.fixed_price)

    def test_no_shipping_methods_assign_cheapest_delivery_carrier(self):
        self.data_json.update({
            'name': 'NOCARRIER',
            'journal_name': self.journal.name,
            'invoice_date': '2022-01-01',
            'payment_method_name': self.payment_method.name,
            'carrier_id': '',
        })
        with self.assertRaises(exceptions.ValidationError) as result:
            self.env['sale.order'].json_import(self.data_json)
        self.assertEqual(
            result.exception.name,
            'No shipping methods found with the check for calculating the '
            'most economical shipping method activated.')

    def test_check_carrier_not_available_from_01(self):
        self.assertFalse(self.free_delivery.include_cheapest_carrier)
        self.assertFalse(self.free_delivery.not_available_from)
        self.free_delivery.write({
            'include_cheapest_carrier': True,
            'not_available_from': True,
            'limit_amount': 200,
        })
        self.assertTrue(self.free_delivery.include_cheapest_carrier)
        self.assertTrue(self.free_delivery.not_available_from)
        self.assertEqual(self.free_delivery.limit_amount, 200)
        self.data_json.update({
            'name': 'NOTAVAILABLE01',
            'journal_name': self.journal.name,
            'invoice_date': '2022-01-01',
            'payment_method_name': self.payment_method.name,
            'carrier_id': '',
        })
        result = self.env['sale.order'].json_import(self.data_json)
        sales = self.env['sale.order'].search([('id', '=', result)])
        self.assertEqual(len(sales), 1)
        self.assertEqual(sales.name, self.data_json['name'])
        carriers = self.env['delivery.carrier'].search(
            sales._get_sale_available_delivery_carrier_domain())
        self.assertEqual(len(carriers), 1)
        self.assertEqual(carriers[0], self.free_delivery)

    def test_check_carrier_not_available_from_02(self):
        self.assertFalse(self.free_delivery.include_cheapest_carrier)
        self.assertFalse(self.free_delivery.not_available_from)
        self.free_delivery.write({
            'include_cheapest_carrier': True,
            'not_available_from': True,
            'limit_amount': 156.09,
        })
        self.assertTrue(self.free_delivery.not_available_from)
        self.assertTrue(self.free_delivery.include_cheapest_carrier)
        self.assertEqual(self.free_delivery.limit_amount, 156.09)
        self.data_json.update({
            'name': 'NOTAVAILABLE02',
            'journal_name': self.journal.name,
            'invoice_date': '2022-01-01',
            'payment_method_name': self.payment_method.name,
            'carrier_id': '',
        })
        result = self.env['sale.order'].json_import(self.data_json)
        sales = self.env['sale.order'].search([('id', '=', result)])
        self.assertEqual(len(sales), 1)
        self.assertEqual(sales.name, self.data_json['name'])
        carriers = self.env['delivery.carrier'].search(
            sales._get_sale_available_delivery_carrier_domain())
        self.assertEqual(len(carriers), 1)
        self.assertEqual(carriers[0], self.free_delivery)

    def test_check_carrier_not_available_from_03(self):
        self.assertFalse(self.free_delivery.include_cheapest_carrier)
        self.assertFalse(self.free_delivery.not_available_from)
        self.free_delivery.write({
            'include_cheapest_carrier': True,
            'not_available_from': True,
            'limit_amount': 100,
        })
        self.assertTrue(self.free_delivery.include_cheapest_carrier)
        self.assertTrue(self.free_delivery.not_available_from)
        self.assertEqual(self.free_delivery.limit_amount, 100)
        self.data_json.update({
            'name': 'NOTAVAILABLE03',
            'journal_name': self.journal.name,
            'invoice_date': '2022-01-01',
            'payment_method_name': self.payment_method.name,
            'carrier_id': '',
        })
        with self.assertRaises(exceptions.ValidationError) as result:
            self.env['sale.order'].json_import(self.data_json)
        self.assertEqual(
            result.exception.name,
            'No shipping methods found with the check for calculating the '
            'most economical shipping method activated.')

    def test_check_warehouse_json(self):
        self.assertFalse(self.free_delivery.include_cheapest_carrier)
        self.free_delivery.include_cheapest_carrier = True
        self.assertTrue(self.free_delivery.include_cheapest_carrier)
        self.data_json.update({
            'name': 'SOWH1',
            'journal_name': self.journal.name,
            'invoice_date': '2022-01-01',
            'payment_method_name': self.payment_method.name,
        })
        result = self.env['sale.order'].json_import(self.data_json)
        sales = self.env['sale.order'].search([('id', '=', result)])
        self.assertEqual(len(sales), 1)
        self.assertEqual(result, sales.id)
        self.assertEqual(sales.name, self.data_json['name'])
        self.assertEqual(sales.warehouse_id.id, self.data_json['warehouse_id'])

    def test_check_not_warehouse_json(self):
        self.assertFalse(self.free_delivery.include_cheapest_carrier)
        self.free_delivery.include_cheapest_carrier = True
        self.assertTrue(self.free_delivery.include_cheapest_carrier)
        self.data_json.update({
            'name': 'SOWH2',
            'journal_name': self.journal.name,
            'invoice_date': '2022-01-01',
            'payment_method_name': self.payment_method.name,
        })
        del self.data_json['warehouse_id']
        self.assertTrue('warehouse_id' not in self.data_json)
        result = self.env['sale.order'].json_import(self.data_json)
        sales = self.env['sale.order'].search([('id', '=', result)])
        self.assertEqual(len(sales), 1)
        self.assertEqual(result, sales.id)
        self.assertEqual(sales.name, self.data_json['name'])
        self.assertTrue(sales.warehouse_id)
        default_data = self.env['sale.order']._add_missing_default_values({})
        self.assertEqual(sales.warehouse_id.id, default_data['warehouse_id'])

    def test_error_price_with_taxes_calculated(self):
        self.assertFalse(self.free_delivery.include_cheapest_carrier)
        self.free_delivery.include_cheapest_carrier = True
        self.assertTrue(self.free_delivery.include_cheapest_carrier)
        self.data_json.update({
            'name': 'SOTAX2',
            'journal_name': self.journal.name,
            'invoice_date': '2022-01-01',
            'payment_method_name': self.payment_method.name,
        })
        self.data_json['order_line'][0].update({
            'price_unit_taxed': '83',
        })
        self.assertEqual(
            self.data_json['order_line'][0]['price_unit_taxed'], '83')
        with self.assertRaises(exceptions.ValidationError) as result:
            self.env['sale.order'].json_import(self.data_json)
        self.assertEqual(
            result.exception.name,
            'Price with taxes does not match with calculated by Odoo:\n'
            'Line taxes in JSON: 83.0\nTotal line taxes calculated '
            'by Odoo: 95.59')

    def test_check_key_no_payment_true(self):
        self.assertFalse(self.free_delivery.include_cheapest_carrier)
        self.free_delivery.include_cheapest_carrier = True
        self.assertTrue(self.free_delivery.include_cheapest_carrier)
        self.data_json.update({
            'name': 'SONOPAYMENT01',
            'journal_name': self.journal.name,
            'invoice_date': '2022-01-01',
            'payment_method_name': self.payment_method.name,
            'no_payment': True,
        })
        result = self.env['sale.order'].json_import(self.data_json)
        sales = self.env['sale.order'].search([('id', '=', result)])
        self.assertEqual(len(sales), 1)
        self.assertEqual(result, sales.id)
        self.assertEqual(sales.name, self.data_json['name'])
        self.assertEqual(sales.state, 'sale')
        self.assertEqual(len(sales.invoice_ids), 1)
        self.assertEqual(sales.invoice_ids[0].state, 'paid')

    def test_check_key_no_payment_false(self):
        self.assertFalse(self.free_delivery.include_cheapest_carrier)
        self.free_delivery.include_cheapest_carrier = True
        self.assertTrue(self.free_delivery.include_cheapest_carrier)
        self.data_json.update({
            'name': 'SONOPAYMENT02',
            'journal_name': self.journal.name,
            'invoice_date': '2022-01-01',
            'payment_method_name': self.payment_method.name,
        })
        result = self.env['sale.order'].json_import(self.data_json)
        sales = self.env['sale.order'].search([('id', '=', result)])
        self.assertEqual(len(sales), 1)
        self.assertEqual(result, sales.id)
        self.assertEqual(sales.name, self.data_json['name'])
        self.assertEqual(sales.state, 'sale')
        self.assertEqual(len(sales.invoice_ids), 1)
        self.assertEqual(sales.invoice_ids[0].state, 'paid')

    def test_check_key_no_payment_empty(self):
        self.assertFalse(self.free_delivery.include_cheapest_carrier)
        self.free_delivery.include_cheapest_carrier = True
        self.assertTrue(self.free_delivery.include_cheapest_carrier)
        self.data_json.update({
            'name': 'SONOPAYMENT03',
            'journal_name': self.journal.name,
            'invoice_date': '2022-01-01',
            'payment_method_name': self.payment_method.name,
            'no_payment': '',
        })
        result = self.env['sale.order'].json_import(self.data_json)
        sales = self.env['sale.order'].search([('id', '=', result)])
        self.assertEqual(len(sales), 1)
        self.assertEqual(result, sales.id)
        self.assertEqual(sales.name, self.data_json['name'])
        self.assertEqual(sales.state, 'sale')
        self.assertEqual(len(sales.invoice_ids), 1)
        self.assertEqual(sales.invoice_ids[0].state, 'paid')

    def test_check_key_no_payment_none(self):
        self.assertFalse(self.free_delivery.include_cheapest_carrier)
        self.free_delivery.include_cheapest_carrier = True
        self.assertTrue(self.free_delivery.include_cheapest_carrier)
        self.data_json.update({
            'name': 'SONOPAYMENT04',
            'journal_name': self.journal.name,
            'invoice_date': '2022-01-01',
            'payment_method_name': self.payment_method.name,
            'no_payment': None,
        })
        result = self.env['sale.order'].json_import(self.data_json)
        sales = self.env['sale.order'].search([('id', '=', result)])
        self.assertEqual(len(sales), 1)
        self.assertEqual(result, sales.id)
        self.assertEqual(sales.name, self.data_json['name'])
        self.assertEqual(sales.state, 'sale')
        self.assertEqual(len(sales.invoice_ids), 1)
        self.assertEqual(sales.invoice_ids[0].state, 'paid')

    def test_check_no_key_no_payment_included_in_json(self):
        self.assertFalse(self.free_delivery.include_cheapest_carrier)
        self.free_delivery.include_cheapest_carrier = True
        self.assertTrue(self.free_delivery.include_cheapest_carrier)
        self.data_json.update({
            'name': 'SONOPAYMENT05',
            'journal_name': self.journal.name,
            'invoice_date': '2022-01-01',
            'payment_method_name': self.payment_method.name,
        })
        result = self.env['sale.order'].json_import(self.data_json)
        sales = self.env['sale.order'].search([('id', '=', result)])
        self.assertEqual(len(sales), 1)
        self.assertEqual(result, sales.id)
        self.assertEqual(sales.name, self.data_json['name'])
        self.assertEqual(sales.state, 'sale')
        self.assertEqual(len(sales.invoice_ids), 1)
        self.assertEqual(sales.invoice_ids[0].state, 'paid')

    def test_create_delivery_partner_shipping_id(self):
        self.assertFalse(self.free_delivery.include_cheapest_carrier)
        self.free_delivery.include_cheapest_carrier = True
        self.assertTrue(self.free_delivery.include_cheapest_carrier)
        self.data_json.update({
            'name': 'SODELIVERY01',
            'journal_name': self.journal.name,
            'invoice_date': '2022-01-01',
            'payment_method_name': self.payment_method.name,
            'partner_shipping': {
                'name': self.data_json['name'],
                'email': self.data_json['partner']['email'],
                'street': self.data_json['partner']['street'],
                'street2': 'Customer street 2',
                'city': 'City test',
                'phone': '555443322',
            }
        })
        result = self.env['sale.order'].json_import(self.data_json)
        sales = self.env['sale.order'].search([('id', '=', result)])
        self.assertEqual(len(sales), 1)
        self.assertEqual(result, sales.id)
        self.assertEqual(sales.name, self.data_json['name'])
        self.assertEqual(sales.state, 'sale')
        self.assertTrue(sales.partner_shipping_id)
        self.assertEqual(
            sales.partner_shipping_id.name,
            self.data_json['partner_shipping']['name'])
        self.assertEqual(sales.partner_shipping_id.type, 'delivery')
        self.assertEqual(sales.partner_shipping_id.parent_id, sales.partner_id)

    def test_no_create_delivery_partner_shipping_id(self):
        self.assertFalse(self.free_delivery.include_cheapest_carrier)
        self.free_delivery.include_cheapest_carrier = True
        self.assertTrue(self.free_delivery.include_cheapest_carrier)
        self.data_json['partner'].update({
            'street2': 'Customer street 2',
            'city': 'City test',
            'phone': '222331155',
        })
        partner_shipping_01 = self.env['res.partner'].create({
            'type': 'delivery',
            'name': self.data_json['name'],
            'email': 'customerexample@mail.es',
            'street': self.data_json['partner']['street'],
            'street2': self.data_json['partner']['street2'],
            'city': self.data_json['partner']['city'],
            'phone': self.data_json['partner']['phone'],
        })
        self.data_json.update({
            'name': 'SODELIVERY02',
            'journal_name': self.journal.name,
            'invoice_date': '2022-01-01',
            'payment_method_name': self.payment_method.name,
            'partner_shipping': {
                'name': self.data_json['name'],
                'email': 'customerexample@mail.es',
                'street': self.data_json['partner']['street'],
                'street2': self.data_json['partner']['street2'],
                'city': self.data_json['partner']['city'],
                'phone': self.data_json['partner']['phone'],
            }
        })
        result = self.env['sale.order'].json_import(self.data_json)
        sales = self.env['sale.order'].search([('id', '=', result)])
        self.assertEqual(len(sales), 1)
        self.assertEqual(result, sales.id)
        self.assertEqual(sales.name, self.data_json['name'])
        self.assertEqual(sales.state, 'sale')
        self.assertTrue(sales.partner_shipping_id)
        self.assertEqual(partner_shipping_01, sales.partner_shipping_id)
        self.assertEqual(sales.partner_shipping_id.type, 'delivery')
        self.assertFalse(sales.partner_shipping_id.parent_id)

    def test_lines_without_qty_to_invoice(self):
        self.assertFalse(self.free_delivery.include_cheapest_carrier)
        self.free_delivery.include_cheapest_carrier = True
        self.assertTrue(self.free_delivery.include_cheapest_carrier)
        self.data_json.update({
            'name': 'SOQTYINVOICE',
            'journal_name': self.journal.name,
            'invoice_date': '2022-01-01',
            'payment_method_name': self.payment_method.name,
        })
        self.assertEqual(self.product_1.invoice_policy, 'order')
        self.assertEqual(self.product_2.invoice_policy, 'order')
        self.product_1.invoice_policy = 'delivery'
        self.product_2.invoice_policy = 'delivery'
        self.assertEqual(self.product_1.invoice_policy, 'delivery')
        self.assertEqual(self.product_2.invoice_policy, 'delivery')
        with self.assertRaises(exceptions.ValidationError) as result:
            self.env['sale.order'].json_import(self.data_json)
        self.assertEqual(
            result.exception.name,
            'Lines without quantity to be invoiced for order %s' % (
                self.data_json['name']))
