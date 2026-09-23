###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
import base64
import copy
import json
import os

from odoo import exceptions, fields
from odoo.modules.module import get_resource_path
from odoo.tests.common import HttpCase
from odoo.tools import config


class TestSaleOrderImportJson(HttpCase):

    def _cleanup_import_error_dir(self):
        error_dir = os.path.join(
            config.filestore(self.env.cr.dbname),
            'sale_order_import_json_error')
        if not os.path.isdir(error_dir):
            return
        for name in os.listdir(error_dir):
            try:
                os.remove(os.path.join(error_dir, name))
            except OSError:
                pass

    def setUp(self):
        super().setUp()
        self.addCleanup(self._cleanup_import_error_dir)
        self.env.ref('product.list0').currency_id = self.env.ref('base.EUR').id
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
        self.customer = self.env['res.partner'].create({
            'name': 'Test customer',
            'street': 'Customer dropshipping street',
            'email': 'dropshipping@partner.com',
            'customer': True,
        })
        self.supplier = self.env['res.partner'].create({
            'name': 'Test supplier',
            'supplier': True,
        })
        self.dropshipping_route = self.env.ref(
            'stock_dropshipping.route_drop_shipping')
        self.product_dropshipping = self.env['product.product'].create({
            'name': 'Test product dropshipping',
            'type': 'product',
            'default_code': 'TEST-DROPSHIP',
            'route_ids': [(6, 0, [self.dropshipping_route.id])],
            'seller_ids': [(0, 0, {
                'name': self.supplier.id,
                'price': 10,
            })],
        })

    def test_url_create_invoice(self):
        self.authenticate('admin', 'admin')
        self.opener.headers.update({
            'Content-type': 'application/json',
            'Accept': 'text/plain',
        })
        date = fields.Datetime.now().strftime('%Y-%m-%d')
        data_json_2 = {
            'name': 'SO1425',
            'invoice_number': 'INV001TEST',
            'invoice_date': date,
        }
        response = self.url_open(
            '/sale_order/create_invoice', data=json.dumps(data_json_2))
        self.assertEqual(response.status_code, 200)

    def test_json_import_create_invoice_from_order(self):
        sale = self.env['sale.order'].create({
            'name': 'SO1425',
            'partner_id': self.partner_1.id,
            'order_line': [
                (0, 0, {
                    'product_id': self.product_1.id,
                    'product_uom_qty': 1}),
                (0, 0, {
                    'product_id': self.product_2.id,
                    'product_uom_qty': 2}),
            ]
        })
        sale.action_confirm()
        self.assertEqual(sale.state, 'sale')
        self.assertEqual(len(sale.invoice_ids), 0)
        self.assertEqual(len(sale.picking_ids), 1)
        data_json_2 = {
            'name': 'SO1425',
            'invoice_number': 'INV001TEST',
            'invoice_date': '2023-01-15',
            'payment_journal_name': self.journal_bank.name,
        }
        self.assertEqual(data_json_2['invoice_number'], 'INV001TEST')
        result_inv = self.env['sale.order'].json_import_create_invoice(
            data_json_2)
        attach = self.env['ir.attachment'].search([
            ('res_id', '=', result_inv[0]),
            ('res_model', '=', 'account.invoice'),
        ])
        self.assertEqual(len(attach), 1)
        data = json.loads(base64.b64decode(attach.datas))
        self.assertEqual(data.get('name'), 'SO1425')
        self.assertEqual(data.get('invoice_number'), 'INV001TEST')
        self.assertEqual(sale.name, data_json_2['name'])
        invoices = self.env['account.invoice'].search([
            ('id', 'in', result_inv),
        ])
        self.assertEqual(len(invoices), 1)
        invoice = invoices[0]
        self.assertIn(invoice.id, result_inv)
        self.assertEqual(invoice.number, data_json_2['invoice_number'])
        self.assertEqual(invoice.invoice_number, data_json_2['invoice_number'])
        self.assertEqual(
            invoice.date.strftime('%Y-%m-%d'),
            data_json_2['invoice_date'])
        self.assertEqual(invoice.origin, data_json_2['name'])
        line_product1 = invoice.invoice_line_ids.filtered(
            lambda ln: ln.product_id.default_code == 'TEST-01')
        self.assertTrue(line_product1)
        self.assertEqual(line_product1.quantity, 1)
        self.assertEqual(line_product1.price_unit, 100)
        line_product2 = invoice.invoice_line_ids.filtered(
            lambda ln: ln.product_id.default_code == 'TEST-02')
        self.assertTrue(line_product2)
        self.assertEqual(line_product2.quantity, 2)
        self.assertEqual(line_product2.price_unit, 100)
        self.assertEqual(sale.state, 'sale')
        self.assertEqual(invoice.state, 'paid')
        self.assertEqual(sale.amount_total, invoice.amount_total)
        payments = invoice.payment_ids
        self.assertEqual(len(payments), 1)
        payment = payments[0]
        self.assertEqual(
            payment.journal_id, self.journal_bank)
        self.assertEqual(
            payment.payment_method_id,
            self.journal_bank.inbound_payment_method_ids)
        self.assertEqual(
            payment.payment_date.strftime('%Y-%m-%d'), '2023-01-15')

    def test_import_order_with_json_and_then_create_invoice_ok(self):
        self.assertFalse(self.free_delivery.include_cheapest_carrier)
        self.free_delivery.include_cheapest_carrier = True
        self.assertTrue(self.free_delivery.include_cheapest_carrier)
        self.data_json.update({
            'name': 'SO1425',
            'state': 'confirmed-no-invoice',
            'invoice_date': '2023-01-15 12:30:00',
        })
        self.assertEqual(self.data_json['state'], 'confirmed-no-invoice')
        result_order = self.env['sale.order'].json_import(self.data_json)
        sales = self.env['sale.order'].search([('id', '=', result_order)])
        self.assertEqual(len(sales), 1)
        self.assertEqual(result_order, sales.id)
        self.assertEqual(sales.name, self.data_json['name'])
        self.assertEqual(sales.state, 'sale')
        self.assertEqual(len(sales.invoice_ids), 0)
        self.assertEqual(len(sales.picking_ids), 1)
        data_json_2 = {
            'name': 'SO1425',
            'invoice_number': 'INV001TEST',
            'invoice_date': '2023-01-15',
        }
        sales.team_id.import_payment_journal_id = self.journal_bank.id
        self.assertEqual(data_json_2['invoice_number'], 'INV001TEST')
        result_inv = self.env['sale.order'].json_import_create_invoice(
            data_json_2)
        attach = self.env['ir.attachment'].search([
            ('res_id', '=', result_inv[0]),
            ('res_model', '=', 'account.invoice'),
        ])
        self.assertEqual(len(attach), 1)
        data = json.loads(base64.b64decode(attach.datas))
        self.assertEqual(data.get('name'), 'SO1425')
        self.assertEqual(data.get('invoice_number'), 'INV001TEST')
        sales = self.env['sale.order'].search([('id', '=', result_order)])
        self.assertEqual(len(sales), 1)
        self.assertEqual(result_order, sales.id)
        self.assertEqual(sales.name, self.data_json['name'])
        invoices = self.env['account.invoice'].search([
            ('id', 'in', result_inv),
        ])
        self.assertEqual(len(invoices), 1)
        invoice = invoices[0]
        self.assertIn(invoice.id, result_inv)
        self.assertEqual(invoice.number, data_json_2['invoice_number'])
        self.assertEqual(invoice.invoice_number, data_json_2['invoice_number'])
        self.assertEqual(
            invoice.date.strftime('%Y-%m-%d'),
            data_json_2['invoice_date'])
        self.assertEqual(invoice.origin, self.data_json['name'])
        line_product1 = invoice.invoice_line_ids.filtered(
            lambda ln: ln.product_id.default_code == 'TEST-01')
        self.assertTrue(line_product1)
        self.assertEqual(line_product1.quantity, 1)
        self.assertEqual(line_product1.price_unit, 79)
        line_product2 = invoice.invoice_line_ids.filtered(
            lambda ln: ln.product_id.default_code == 'TEST-02')
        self.assertTrue(line_product2)
        self.assertEqual(line_product2.quantity, 2)
        self.assertEqual(line_product2.price_unit, 25)
        self.assertEqual(sales.state, 'sale')
        self.assertEqual(invoice.state, 'paid')
        self.assertEqual(sales.amount_total, invoice.amount_total)
        payments = invoice.payment_ids
        self.assertEqual(len(payments), 1)
        payment = payments[0]
        self.assertEqual(
            payment.journal_id, invoice.team_id.import_payment_journal_id)
        self.assertEqual(
            payment.payment_method_id,
            self.journal_bank.inbound_payment_method_ids)
        self.assertEqual(
            payment.payment_date.strftime('%Y-%m-%d'), '2023-01-15')

    def test_create_invoice_without_journal(self):
        self.assertFalse(self.free_delivery.include_cheapest_carrier)
        self.free_delivery.include_cheapest_carrier = True
        self.assertTrue(self.free_delivery.include_cheapest_carrier)
        self.data_json.update({
            'name': 'SO1425',
            'state': 'confirmed-no-invoice',
            'invoice_date': '2023-01-15 12:30:00',
        })
        self.assertEqual(self.data_json['state'], 'confirmed-no-invoice')
        result_order = self.env['sale.order'].json_import(self.data_json)
        sales = self.env['sale.order'].search([('id', '=', result_order)])
        self.assertEqual(len(sales), 1)
        self.assertEqual(result_order, sales.id)
        self.assertEqual(sales.name, self.data_json['name'])
        self.assertEqual(sales.state, 'sale')
        self.assertEqual(len(sales.invoice_ids), 0)
        self.assertEqual(len(sales.picking_ids), 1)
        data_json_2 = {
            'name': 'SO1425',
            'invoice_number': 'INV001TEST',
            'invoice_date': '2023-01-15',
        }
        self.assertEqual(data_json_2['invoice_number'], 'INV001TEST')
        with self.assertRaises(exceptions.ValidationError) as result:
            self.env['sale.order'].json_import_create_invoice(data_json_2)
        self.assertEqual(
            result.exception.name,
            'For payment procces you must pass a payment_journal_name params '
            'or configure sales team.')
        sales = self.env['sale.order'].search([('id', '=', result_order)])
        self.assertEqual(len(sales), 1)
        self.assertEqual(result_order, sales.id)
        self.assertEqual(sales.name, self.data_json['name'])
        self.assertEqual(len(sales.invoice_ids), 1)
        invoices = sales.invoice_ids
        self.assertEqual(len(invoices), 1)
        invoice = invoices[0]
        self.assertEqual(invoice.number, data_json_2['invoice_number'])
        self.assertEqual(invoice.invoice_number, data_json_2['invoice_number'])
        self.assertEqual(
            invoice.date.strftime('%Y-%m-%d'),
            data_json_2['invoice_date'])
        self.assertEqual(invoice.origin, self.data_json['name'])
        line_product1 = invoice.invoice_line_ids.filtered(
            lambda ln: ln.product_id.default_code == 'TEST-01')
        self.assertTrue(line_product1)
        self.assertEqual(line_product1.quantity, 1)
        self.assertEqual(line_product1.price_unit, 79)
        line_product2 = invoice.invoice_line_ids.filtered(
            lambda ln: ln.product_id.default_code == 'TEST-02')
        self.assertTrue(line_product2)
        self.assertEqual(line_product2.quantity, 2)
        self.assertEqual(line_product2.price_unit, 25)
        self.assertEqual(sales.state, 'sale')
        self.assertEqual(invoice.state, 'open')
        self.assertEqual(sales.amount_total, invoice.amount_total)
        self.assertEqual(len(invoice.payment_ids), 0)

    def test_create_invoice_with_journal_name_json(self):
        self.assertFalse(self.free_delivery.include_cheapest_carrier)
        self.free_delivery.include_cheapest_carrier = True
        self.assertTrue(self.free_delivery.include_cheapest_carrier)
        self.data_json.update({
            'name': 'SO1425',
            'state': 'confirmed-no-invoice',
            'invoice_date': '2023-01-15 12:30:00',
        })
        self.assertEqual(self.data_json['state'], 'confirmed-no-invoice')
        result_order = self.env['sale.order'].json_import(self.data_json)
        sales = self.env['sale.order'].search([('id', '=', result_order)])
        self.assertEqual(len(sales), 1)
        self.assertEqual(result_order, sales.id)
        self.assertEqual(sales.name, self.data_json['name'])
        self.assertEqual(sales.state, 'sale')
        self.assertEqual(len(sales.invoice_ids), 0)
        self.assertEqual(len(sales.picking_ids), 1)
        data_json_2 = {
            'name': 'SO1425',
            'invoice_number': 'INV001TEST',
            'invoice_date': '2023-01-15',
            'payment_journal_name': self.journal_bank.name,
        }
        self.assertEqual(data_json_2['invoice_number'], 'INV001TEST')
        result_inv = self.env['sale.order'].json_import_create_invoice(
            data_json_2)
        attach = self.env['ir.attachment'].search([
            ('res_id', '=', result_inv[0]),
            ('res_model', '=', 'account.invoice'),
        ])
        self.assertEqual(len(attach), 1)
        data = json.loads(base64.b64decode(attach.datas))
        self.assertEqual(data.get('name'), 'SO1425')
        self.assertEqual(data.get('invoice_number'), 'INV001TEST')
        sales = self.env['sale.order'].search([('id', '=', result_order)])
        self.assertEqual(len(sales), 1)
        self.assertEqual(result_order, sales.id)
        self.assertEqual(sales.name, self.data_json['name'])
        invoices = self.env['account.invoice'].search([
            ('id', 'in', result_inv),
        ])
        self.assertEqual(len(invoices), 1)
        invoice = invoices[0]
        self.assertIn(invoice.id, result_inv)
        self.assertEqual(invoice.number, data_json_2['invoice_number'])
        self.assertEqual(invoice.invoice_number, data_json_2['invoice_number'])
        self.assertEqual(
            invoice.date.strftime('%Y-%m-%d'),
            data_json_2['invoice_date'])
        self.assertEqual(invoice.origin, self.data_json['name'])
        line_product1 = invoice.invoice_line_ids.filtered(
            lambda ln: ln.product_id.default_code == 'TEST-01')
        self.assertTrue(line_product1)
        self.assertEqual(line_product1.quantity, 1)
        self.assertEqual(line_product1.price_unit, 79)
        line_product2 = invoice.invoice_line_ids.filtered(
            lambda ln: ln.product_id.default_code == 'TEST-02')
        self.assertTrue(line_product2)
        self.assertEqual(line_product2.quantity, 2)
        self.assertEqual(line_product2.price_unit, 25)
        self.assertEqual(sales.state, 'sale')
        self.assertEqual(invoice.state, 'paid')
        self.assertEqual(sales.amount_total, invoice.amount_total)
        payments = invoice.payment_ids
        self.assertEqual(len(payments), 1)
        payment = payments[0]
        self.assertEqual(
            payment.journal_id, self.journal_bank)
        self.assertEqual(
            payment.payment_method_id,
            self.journal_bank.inbound_payment_method_ids)
        self.assertEqual(
            payment.payment_date.strftime('%Y-%m-%d'), '2023-01-15')

    def test_create_invoice_with_payment_method_json(self):
        self.assertFalse(self.free_delivery.include_cheapest_carrier)
        self.free_delivery.include_cheapest_carrier = True
        self.assertTrue(self.free_delivery.include_cheapest_carrier)
        self.data_json.update({
            'name': 'SO1425',
            'state': 'confirmed-no-invoice',
            'invoice_date': '2023-01-15 12:30:00',
        })
        self.assertEqual(self.data_json['state'], 'confirmed-no-invoice')
        result_order = self.env['sale.order'].json_import(self.data_json)
        sales = self.env['sale.order'].search([('id', '=', result_order)])
        self.assertEqual(len(sales), 1)
        self.assertEqual(result_order, sales.id)
        self.assertEqual(sales.name, self.data_json['name'])
        self.assertEqual(sales.state, 'sale')
        self.assertEqual(len(sales.invoice_ids), 0)
        self.assertEqual(len(sales.picking_ids), 1)
        data_json_2 = {
            'name': 'SO1425',
            'invoice_number': 'INV001TEST',
            'invoice_date': '2023-01-15',
            'payment_journal_name': self.journal_bank.name,
            'payment_method_name': self.payment_method.name,
        }
        self.assertEqual(data_json_2['invoice_number'], 'INV001TEST')
        result_inv = self.env['sale.order'].json_import_create_invoice(
            data_json_2)
        attach = self.env['ir.attachment'].search([
            ('res_id', '=', result_inv[0]),
            ('res_model', '=', 'account.invoice'),
        ])
        self.assertEqual(len(attach), 1)
        data = json.loads(base64.b64decode(attach.datas))
        self.assertEqual(data.get('name'), 'SO1425')
        self.assertEqual(data.get('invoice_number'), 'INV001TEST')
        sales = self.env['sale.order'].search([('id', '=', result_order)])
        self.assertEqual(len(sales), 1)
        self.assertEqual(result_order, sales.id)
        self.assertEqual(sales.name, self.data_json['name'])
        invoices = self.env['account.invoice'].search([
            ('id', 'in', result_inv),
        ])
        self.assertEqual(len(invoices), 1)
        invoice = invoices[0]
        self.assertIn(invoice.id, result_inv)
        self.assertEqual(invoice.number, data_json_2['invoice_number'])
        self.assertEqual(invoice.invoice_number, data_json_2['invoice_number'])
        self.assertEqual(
            invoice.date.strftime('%Y-%m-%d'),
            data_json_2['invoice_date'])
        self.assertEqual(invoice.origin, self.data_json['name'])
        line_product1 = invoice.invoice_line_ids.filtered(
            lambda ln: ln.product_id.default_code == 'TEST-01')
        self.assertTrue(line_product1)
        self.assertEqual(line_product1.quantity, 1)
        self.assertEqual(line_product1.price_unit, 79)
        line_product2 = invoice.invoice_line_ids.filtered(
            lambda ln: ln.product_id.default_code == 'TEST-02')
        self.assertTrue(line_product2)
        self.assertEqual(line_product2.quantity, 2)
        self.assertEqual(line_product2.price_unit, 25)
        self.assertEqual(sales.state, 'sale')
        self.assertEqual(invoice.state, 'paid')
        self.assertEqual(sales.amount_total, invoice.amount_total)
        payments = invoice.payment_ids
        self.assertEqual(len(payments), 1)
        payment = payments[0]
        self.assertEqual(
            payment.journal_id, self.journal_bank)
        self.assertEqual(
            payment.payment_method_id,
            self.payment_method)
        self.assertEqual(
            payment.payment_date.strftime('%Y-%m-%d'), '2023-01-15')

    def test_sale_order_not_found(self):
        data_json_2 = {
            'name': 'SO1425',
            'invoice_number': 'INV001TEST',
            'invoice_date': '2023-01-15',
            'payment_journal_name': self.journal_bank.name,
            'payment_method_name': self.payment_method.name,
        }
        self.assertEqual(data_json_2['invoice_number'], 'INV001TEST')
        with self.assertRaises(exceptions.ValidationError) as result:
            self.env['sale.order'].json_import_create_invoice(data_json_2)
        self.assertEqual(
            result.exception.name,
            'Sale order with name "SO1425" not found.')
        sales = self.env['sale.order'].search([('name', '=', 'SO1425')])
        self.assertEqual(len(sales), 0)

    def test_with_multiple_sale_orders_found(self):
        self.env['sale.order'].create({
            'name': 'SO1425',
            'partner_id': self.partner_1.id,
        })
        self.env['sale.order'].create({
            'name': 'SO1425',
            'partner_id': self.partner_2.id,
        })
        data_json_2 = {
            'name': 'SO1425',
            'invoice_number': 'INV001TEST',
            'invoice_date': '2023-01-15',
            'payment_journal_name': self.journal_bank.name,
            'payment_method_name': self.payment_method.name,
        }
        self.assertEqual(data_json_2['invoice_number'], 'INV001TEST')
        with self.assertRaises(exceptions.ValidationError) as result:
            self.env['sale.order'].json_import_create_invoice(data_json_2)
        self.assertEqual(
            result.exception.name,
            'Multiple sale orders with same name "SO1425".')
        sales = self.env['sale.order'].search([('name', '=', 'SO1425')])
        self.assertEqual(len(sales), 2)

    def test_sale_order_with_create_invoices(self):
        sale = self.env['sale.order'].create({
            'name': 'SO1425',
            'partner_id': self.partner_1.id,
            'order_line': [
                (0, 0, {
                    'product_id': self.product_1.id,
                    'product_uom_qty': 10}),
            ]
        })
        sale.action_confirm()
        sale.action_invoice_create()
        self.assertEqual(len(sale), 1)
        self.assertEqual(len(sale.invoice_ids), 1)
        data_json_2 = {
            'name': 'SO1425',
            'invoice_number': 'INV001TEST',
            'invoice_date': '2023-01-15',
            'payment_journal_name': self.journal_bank.name,
            'payment_method_name': self.payment_method.name,
        }
        self.assertEqual(data_json_2['invoice_number'], 'INV001TEST')
        with self.assertRaises(exceptions.ValidationError) as result:
            self.env['sale.order'].json_import_create_invoice(data_json_2)
        self.assertEqual(
            result.exception.name,
            'The sale order "SO1425" already has invoices.')

    def test_sale_order_with_duplicate_invoice_number(self):
        inv = self.env['account.invoice'].create({
            'partner_id': self.partner_1.id,
        })
        inv.number = 'INV001TEST'
        sale = self.env['sale.order'].create({
            'name': 'SO1425',
            'partner_id': self.partner_1.id,
            'order_line': [
                (0, 0, {
                    'product_id': self.product_1.id,
                    'product_uom_qty': 10}),
            ]
        })
        sale.action_confirm()
        self.assertEqual(len(sale), 1)
        self.assertEqual(len(sale.invoice_ids), 0)
        data_json_2 = {
            'name': 'SO1425',
            'invoice_number': 'INV001TEST',
            'invoice_date': '2023-01-15',
            'payment_journal_name': self.journal_bank.name,
            'payment_method_name': self.payment_method.name,
        }
        self.assertEqual(data_json_2['invoice_number'], 'INV001TEST')
        with self.assertRaises(exceptions.ValidationError) as result:
            self.env['sale.order'].json_import_create_invoice(data_json_2)
        self.assertEqual(
            result.exception.name,
            'Already exists an invoice with number "INV001TEST".')

    def test_json_import_create_invoice_without_name(self):
        sale = self.env['sale.order'].create({
            'name': 'SO1425',
            'partner_id': self.partner_1.id,
            'order_line': [
                (0, 0, {
                    'product_id': self.product_1.id,
                    'product_uom_qty': 1}),
                (0, 0, {
                    'product_id': self.product_2.id,
                    'product_uom_qty': 2}),
            ]
        })
        sale.action_confirm()
        self.assertEqual(sale.state, 'sale')
        self.assertEqual(len(sale.invoice_ids), 0)
        self.assertEqual(len(sale.picking_ids), 1)
        data_json_2 = {
            'invoice_number': 'INV001TEST',
            'invoice_date': '2023-01-15',
            'payment_journal_name': self.journal_bank.name,
        }
        self.assertEqual(data_json_2['invoice_number'], 'INV001TEST')
        with self.assertRaises(exceptions.ValidationError) as result:
            self.env['sale.order'].json_import_create_invoice(data_json_2)
        self.assertEqual(
            result.exception.name,
            'Sale order with name "False" not found.')

    def test_json_import_create_invoice_without_invoice_number(self):
        sale = self.env['sale.order'].create({
            'name': 'SO1425',
            'partner_id': self.partner_1.id,
            'order_line': [
                (0, 0, {
                    'product_id': self.product_1.id,
                    'product_uom_qty': 1}),
                (0, 0, {
                    'product_id': self.product_2.id,
                    'product_uom_qty': 2}),
            ]
        })
        sale.action_confirm()
        self.assertEqual(sale.state, 'sale')
        self.assertEqual(len(sale.invoice_ids), 0)
        self.assertEqual(len(sale.picking_ids), 1)
        data_json_2 = {
            'name': 'SO1425',
            'invoice_date': '2023-01-15',
            'payment_journal_name': self.journal_bank.name,
        }
        result_inv = self.env['sale.order'].json_import_create_invoice(
            data_json_2)
        attach = self.env['ir.attachment'].search([
            ('res_id', '=', result_inv[0]),
            ('res_model', '=', 'account.invoice'),
        ])
        self.assertEqual(len(attach), 1)
        data = json.loads(base64.b64decode(attach.datas))
        self.assertEqual(data.get('name'), 'SO1425')
        self.assertEqual(sale.name, data_json_2['name'])
        invoices = self.env['account.invoice'].search([
            ('id', 'in', result_inv),
        ])
        self.assertEqual(len(invoices), 1)
        invoice = invoices[0]
        self.assertIn(invoice.id, result_inv)
        self.assertEqual(
            invoice.date.strftime('%Y-%m-%d'),
            data_json_2['invoice_date'])
        self.assertEqual(invoice.origin, data_json_2['name'])
        line_product1 = invoice.invoice_line_ids.filtered(
            lambda ln: ln.product_id.default_code == 'TEST-01')
        self.assertTrue(line_product1)
        self.assertEqual(line_product1.quantity, 1)
        self.assertEqual(line_product1.price_unit, 100)
        line_product2 = invoice.invoice_line_ids.filtered(
            lambda ln: ln.product_id.default_code == 'TEST-02')
        self.assertTrue(line_product2)
        self.assertEqual(line_product2.quantity, 2)
        self.assertEqual(line_product2.price_unit, 100)
        self.assertEqual(sale.state, 'sale')
        self.assertEqual(invoice.state, 'paid')
        self.assertEqual(sale.amount_total, invoice.amount_total)
        payments = invoice.payment_ids
        self.assertEqual(len(payments), 1)
        payment = payments[0]
        self.assertEqual(
            payment.journal_id, self.journal_bank)
        self.assertEqual(
            payment.payment_method_id,
            self.journal_bank.inbound_payment_method_ids)
        self.assertEqual(
            payment.payment_date.strftime('%Y-%m-%d'), '2023-01-15')

    def test_json_import_create_invoice_without_invoice_date(self):
        sale = self.env['sale.order'].create({
            'name': 'SO1425',
            'partner_id': self.partner_1.id,
            'order_line': [
                (0, 0, {
                    'product_id': self.product_1.id,
                    'product_uom_qty': 1}),
                (0, 0, {
                    'product_id': self.product_2.id,
                    'product_uom_qty': 2}),
            ]
        })
        sale.action_confirm()
        self.assertEqual(sale.state, 'sale')
        self.assertEqual(len(sale.invoice_ids), 0)
        self.assertEqual(len(sale.picking_ids), 1)
        data_json_2 = {
            'name': 'SO1425',
            'invoice_number': 'INV001TEST',
            'payment_journal_name': self.journal_bank.name,
        }
        result_inv = self.env['sale.order'].json_import_create_invoice(
            data_json_2)
        attach = self.env['ir.attachment'].search([
            ('res_id', '=', result_inv[0]),
            ('res_model', '=', 'account.invoice'),
        ])
        self.assertEqual(len(attach), 1)
        data = json.loads(base64.b64decode(attach.datas))
        self.assertEqual(data.get('name'), 'SO1425')
        self.assertEqual(data.get('invoice_number'), 'INV001TEST')
        self.assertEqual(sale.name, data_json_2['name'])
        invoices = self.env['account.invoice'].search([
            ('id', 'in', result_inv),
        ])
        self.assertEqual(len(invoices), 1)
        invoice = invoices[0]
        self.assertIn(invoice.id, result_inv)
        self.assertEqual(invoice.number, data_json_2['invoice_number'])
        self.assertEqual(invoice.invoice_number, data_json_2['invoice_number'])
        self.assertEqual(invoice.date, fields.datetime.now().date())
        self.assertEqual(invoice.origin, data_json_2['name'])
        line_product1 = invoice.invoice_line_ids.filtered(
            lambda ln: ln.product_id.default_code == 'TEST-01')
        self.assertTrue(line_product1)
        self.assertEqual(line_product1.quantity, 1)
        self.assertEqual(line_product1.price_unit, 100)
        line_product2 = invoice.invoice_line_ids.filtered(
            lambda ln: ln.product_id.default_code == 'TEST-02')
        self.assertTrue(line_product2)
        self.assertEqual(line_product2.quantity, 2)
        self.assertEqual(line_product2.price_unit, 100)
        self.assertEqual(sale.state, 'sale')
        self.assertEqual(invoice.state, 'paid')
        self.assertEqual(sale.amount_total, invoice.amount_total)
        payments = invoice.payment_ids
        self.assertEqual(len(payments), 1)
        payment = payments[0]
        self.assertEqual(
            payment.journal_id, self.journal_bank)
        self.assertEqual(
            payment.payment_method_id,
            self.journal_bank.inbound_payment_method_ids)
        self.assertEqual(payment.payment_date, fields.datetime.now().date())

    def test_json_import_create_invoice_order_in_draft(self):
        sale = self.env['sale.order'].create({
            'name': 'SO1425',
            'partner_id': self.partner_1.id,
            'order_line': [
                (0, 0, {
                    'product_id': self.product_1.id,
                    'product_uom_qty': 1}),
                (0, 0, {
                    'product_id': self.product_2.id,
                    'product_uom_qty': 2}),
            ]
        })
        self.assertEqual(sale.state, 'draft')
        self.assertEqual(len(sale.invoice_ids), 0)
        self.assertEqual(len(sale.picking_ids), 0)
        data_json_2 = {
            'name': 'SO1425',
            'invoice_number': 'INV001TEST',
            'invoice_date': '2023-01-15',
            'payment_journal_name': self.journal_bank.name,
        }
        with self.assertRaises(exceptions.ValidationError) as result:
            self.env['sale.order'].json_import_create_invoice(data_json_2)
        self.assertIn(
            'The sale order should be confirmed.',
            result.exception.name)

    def test_url_import(self):
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
        sales = self.env['sale.order'].search([
            ('id', '=', result),
        ])
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
        sales = self.env['sale.order'].search([
            ('id', '=', result),
        ])
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
        sales = self.env['sale.order'].search([
            ('id', '=', result),
        ])
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
        sales = self.env['sale.order'].search([
            ('id', '=', result),
        ])
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
        sales = self.env['sale.order'].search([
            ('id', '=', result),
        ])
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
        sales = self.env['sale.order'].search([
            ('id', '=', result),
        ])
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
        sales = self.env['sale.order'].search([
            ('id', '=', result),
        ])
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
        sales = self.env['sale.order'].search([
            ('id', '=', result),
        ])
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
        sales = self.env['sale.order'].search([
            ('id', '=', result),
        ])
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
        sales = self.env['sale.order'].search([
            ('id', '=', result),
        ])
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
        sales = self.env['sale.order'].search([
            ('id', '=', result),
        ])
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
        sales = self.env['sale.order'].search([
            ('id', '=', result),
        ])
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
        sales = self.env['sale.order'].search([
            ('id', '=', result),
        ])
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
        sales = self.env['sale.order'].search([
            ('id', '=', result),
        ])
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
        sales = self.env['sale.order'].search([
            ('id', '=', result),
        ])
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
        sales = self.env['sale.order'].search([
            ('id', '=', result),
        ])
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
        sales = self.env['sale.order'].search([
            ('id', '=', result),
        ])
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
        sales = self.env['sale.order'].search([
            ('id', '=', result),
        ])
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
        sales = self.env['sale.order'].search([
            ('id', '=', result),
        ])
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
        sales = self.env['sale.order'].search([
            ('id', '=', result),
        ])
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
        sales = self.env['sale.order'].search([
            ('id', '=', result),
        ])
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
        sales = self.env['sale.order'].search([
            ('id', '=', result),
        ])
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
        self.assertIn(
            'Price with taxes does not match with calculated by Odoo:\n'
            'Line taxes in JSON: 82.95\nTotal line taxes calculated '
            'by Odoo: 95.59', result.exception.name)
        self.assertIn('Line/Product [1/TEST-01]', result.exception.name)

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
        sales = self.env['sale.order'].search([
            ('id', '=', result),
        ])
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
        sales = self.env['sale.order'].search([
            ('id', '=', result),
        ])
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
        sales = self.env['sale.order'].search([
            ('id', '=', result),
        ])
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
        sales = self.env['sale.order'].search([
            ('id', '=', result),
        ])
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
        sales = self.env['sale.order'].search([
            ('id', '=', result),
        ])
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
        sales = self.env['sale.order'].search([
            ('id', '=', result),
        ])
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
        sales = self.env['sale.order'].search([
            ('id', '=', result),
        ])
        self.assertEqual(len(sales), 1)
        self.assertEqual(result, sales.id)
        self.assertEqual(sales.name, self.data_json['name'])
        self.assertEqual(sales.state, 'sale')
        self.assertTrue(sales.partner_shipping_id)
        self.assertEqual(partner_shipping_01, sales.partner_shipping_id)
        self.assertEqual(sales.partner_shipping_id.type, 'delivery')
        self.assertFalse(sales.partner_shipping_id.parent_id)

    def test_create_delivery_partner_shipping_no_name_uses_street(self):
        self.free_delivery.include_cheapest_carrier = True
        self.data_json.update({
            'name': 'SODELIVERY03',
            'journal_name': self.journal.name,
            'invoice_date': '2022-01-01',
            'payment_method_name': self.payment_method.name,
            'partner_shipping': {
                'email': self.data_json['partner']['email'],
                'street': 'Street without name',
                'city': 'City test',
                'phone': '555443322',
            },
        })
        result = self.env['sale.order'].json_import(self.data_json)
        sales = self.env['sale.order'].search([
            ('id', '=', result),
        ])
        self.assertEqual(len(sales), 1)
        self.assertTrue(sales.partner_shipping_id)
        self.assertEqual(
            sales.partner_shipping_id.name,
            self.data_json['partner_shipping']['street'])
        self.assertEqual(sales.partner_shipping_id.type, 'delivery')
        self.assertEqual(sales.partner_shipping_id.parent_id, sales.partner_id)

    def test_create_delivery_partner_shipping_no_email_key(self):
        self.free_delivery.include_cheapest_carrier = True
        self.data_json.update({
            'name': 'SODELIVERY04',
            'journal_name': self.journal.name,
            'invoice_date': '2022-01-01',
            'payment_method_name': self.payment_method.name,
            'partner_shipping': {
                'name': 'Shipping without email',
                'street': 'Street without email',
                'city': 'City test',
                'phone': '555443322',
            },
        })
        result = self.env['sale.order'].json_import(self.data_json)
        sales = self.env['sale.order'].search([
            ('id', '=', result),
        ])
        self.assertEqual(len(sales), 1)
        self.assertTrue(sales.partner_shipping_id)
        self.assertEqual(
            sales.partner_shipping_id.name,
            self.data_json['partner_shipping']['name'])
        self.assertEqual(
            sales.partner_shipping_id.street,
            self.data_json['partner_shipping']['street'])

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

    def test_select_supplierinfo_01(self):
        self.assertFalse(self.free_delivery.include_cheapest_carrier)
        self.free_delivery.include_cheapest_carrier = True
        self.assertTrue(self.free_delivery.include_cheapest_carrier)
        order_data = {
            'name': 'SO1235',
            'partner': {
                'name': 'Test customer',
                'street': 'Customer dropshipping street',
                'email': 'dropshipping@partner.com',
            },
            'order_line': [
                {
                    'default_code': 'TEST-DROPSHIP',
                    'product_uom_qty': 1,
                    'price_unit_taxed': 95.59,
                    'price_unit_untaxed': 79,
                },
            ],
            'state': 'confirmed',
            'warehouse_id': 1,
            'payment_journal_name': 'Bank test',
            'journal_name': self.journal.name,
            'invoice_date': '2022-07-01',
            'payment_method_name': self.payment_method.name,
        }
        result = self.env['sale.order'].json_import(order_data)
        sales = self.env['sale.order'].search([
            ('id', '=', result),
        ])
        self.assertEqual(len(sales), 1)
        self.assertEqual(result, sales.id)
        self.assertEqual(sales.name, order_data['name'])
        purchase = self.env['purchase.order'].search([
            ('group_id', '=', sales.procurement_group_id.id),
        ])
        self.assertEquals(len(purchase), 1)
        self.assertEquals(purchase.state, 'draft')
        self.assertEquals(len(purchase.order_line), 1)
        self.assertEquals(purchase.partner_id, self.supplier)
        self.assertEquals(
            purchase.order_line[0].price_unit,
            self.product_dropshipping.seller_ids[0].price)

    def test_select_supplierinfo_02(self):
        self.assertFalse(self.free_delivery.include_cheapest_carrier)
        self.free_delivery.include_cheapest_carrier = True
        self.assertTrue(self.free_delivery.include_cheapest_carrier)
        self.assertEqual(len(self.product_dropshipping.seller_ids), 1)
        supplierinfo = self.product_dropshipping.seller_ids[0]
        order_data = {
            'name': 'SO1300',
            'partner': {
                'name': 'Test customer',
                'street': 'Customer dropshipping street',
                'email': 'dropshipping@partner.com',
            },
            'order_line': [
                {
                    'default_code': 'TEST-DROPSHIP',
                    'product_uom_qty': 1,
                    'price_unit_taxed': 95.59,
                    'price_unit_untaxed': 79,
                },
            ],
            'state': 'confirmed',
            'warehouse_id': 1,
            'payment_journal_name': 'Bank test',
            'journal_name': self.journal.name,
            'invoice_date': '2022-07-01',
            'payment_method_name': self.payment_method.name,
        }
        order_data['order_line'][0].update({
            'supplierinfo_id': supplierinfo.id,
        })
        self.assertEquals(
            order_data['order_line'][0]['supplierinfo_id'], supplierinfo.id)
        result = self.env['sale.order'].json_import(order_data)
        sales = self.env['sale.order'].search([
            ('id', '=', result),
        ])
        self.assertEqual(len(sales), 1)
        self.assertEqual(result, sales.id)
        self.assertEqual(sales.name, order_data['name'])
        purchase = self.env['purchase.order'].search([
            ('group_id', '=', sales.procurement_group_id.id),
        ])
        self.assertEquals(len(purchase), 1)
        self.assertEquals(purchase.state, 'draft')
        self.assertEquals(len(purchase.order_line), 1)
        self.assertEquals(purchase.partner_id, self.supplier)
        self.assertEquals(
            purchase.order_line[0].price_unit,
            self.product_dropshipping.seller_ids[0].price)

    def test_select_supplierinfo_03(self):
        self.assertFalse(self.free_delivery.include_cheapest_carrier)
        self.free_delivery.include_cheapest_carrier = True
        self.assertTrue(self.free_delivery.include_cheapest_carrier)
        self.env['product.supplierinfo'].create({
            'name': self.supplier.id,
            'product_tmpl_id': self.product_dropshipping.product_tmpl_id.id,
            'min_qty': 0,
            'price': 35,
            'sequence': 2,
        })
        self.assertEqual(self.product_dropshipping.seller_ids[1].sequence, 2)
        self.assertEqual(len(self.product_dropshipping.seller_ids), 2)
        order_data = {
            'name': 'SO1367',
            'partner': {
                'name': 'Test customer',
                'street': 'Customer dropshipping street',
                'email': 'dropshipping@partner.com',
            },
            'order_line': [
                {
                    'default_code': 'TEST-DROPSHIP',
                    'product_uom_qty': 1,
                    'price_unit_taxed': 95.59,
                    'price_unit_untaxed': 79,
                },
            ],
            'state': 'confirmed',
            'warehouse_id': 1,
            'payment_journal_name': 'Bank test',
            'journal_name': self.journal.name,
            'invoice_date': '2022-07-01',
            'payment_method_name': self.payment_method.name,
        }
        order_data['order_line'][0].update({
            'supplierinfo_id': self.product_dropshipping.seller_ids[1].id,
        })
        result = self.env['sale.order'].json_import(order_data)
        sales = self.env['sale.order'].search([
            ('id', '=', result),
        ])
        self.assertEqual(len(sales), 1)
        self.assertEqual(result, sales.id)
        self.assertEqual(sales.name, order_data['name'])
        purchase = self.env['purchase.order'].search([
            ('group_id', '=', sales.procurement_group_id.id),
        ])
        self.assertEquals(len(purchase), 1)
        self.assertEquals(purchase.state, 'draft')
        self.assertEquals(len(purchase.order_line), 1)
        self.assertEquals(purchase.partner_id, self.supplier)
        self.assertEquals(
            purchase.order_line[0].price_unit,
            self.product_dropshipping.seller_ids[1].price)

    def test_confirmation_date_equal_json_invoice_date(self):
        self.assertFalse(self.free_delivery.include_cheapest_carrier)
        self.free_delivery.include_cheapest_carrier = True
        self.assertTrue(self.free_delivery.include_cheapest_carrier)
        self.data_json.update({
            'name': 'SO1405',
            'journal_name': self.journal.name,
            'invoice_date': '2022-10-14 15:35:30',
            'payment_method_name': self.payment_method.name,
        })
        result = self.env['sale.order'].json_import(self.data_json)
        sales = self.env['sale.order'].search([
            ('id', '=', result),
        ])
        self.assertEqual(len(sales), 1)
        self.assertEqual(result, sales.id)
        self.assertEqual(sales.name, self.data_json['name'])
        self.assertEqual(
            sales.confirmation_date.strftime('%Y-%m-%d %H:%M:%S'),
            self.data_json['invoice_date'])

    def test_new_state_confirmed_no_invoice(self):
        self.assertFalse(self.free_delivery.include_cheapest_carrier)
        self.free_delivery.include_cheapest_carrier = True
        self.assertTrue(self.free_delivery.include_cheapest_carrier)
        self.data_json.update({
            'name': 'SO1425',
            'state': 'confirmed-no-invoice',
            'invoice_date': '2023-01-15 12:30:00',
        })
        self.assertEqual(self.data_json['state'], 'confirmed-no-invoice')
        result = self.env['sale.order'].json_import(self.data_json)
        sales = self.env['sale.order'].search([
            ('id', '=', result),
        ])
        self.assertEqual(len(sales), 1)
        self.assertEqual(result, sales.id)
        self.assertEqual(sales.name, self.data_json['name'])
        self.assertEqual(sales.state, 'sale')
        self.assertEqual(len(sales.invoice_ids), 0)
        self.assertEqual(len(sales.picking_ids), 1)

    def test_check_all_state_keys(self):
        self.assertFalse(self.free_delivery.include_cheapest_carrier)
        self.free_delivery.include_cheapest_carrier = True
        self.assertTrue(self.free_delivery.include_cheapest_carrier)
        self.data_json.update({
            'name': 'SO1443',
            'state': 'confirmed',
            'journal_name': self.journal.name,
            'payment_method_name': self.payment_method.name,
            'invoice_date': '2023-01-15 12:30:00',
        })
        self.assertEqual(self.data_json['state'], 'confirmed')
        result = self.env['sale.order'].json_import(self.data_json)
        sales = self.env['sale.order'].search([
            ('id', '=', result),
        ])
        self.assertEqual(len(sales), 1)
        self.assertEqual(result, sales.id)
        self.assertEqual(sales.name, self.data_json['name'])
        self.assertEqual(sales.state, 'sale')
        self.assertEqual(len(sales.invoice_ids), 1)
        self.assertEqual(len(sales.picking_ids), 1)
        self.assertEqual(len(sales.invoice_ids[0].payment_ids), 1)
        self.data_json.update({
            'name': 'SO1460',
            'state': 'confirmed-no-payment',
            'invoice_date': '2023-01-16 13:30:00',
        })
        self.assertEqual(self.data_json['state'], 'confirmed-no-payment')
        result = self.env['sale.order'].json_import(self.data_json)
        sales = self.env['sale.order'].search([
            ('id', '=', result),
        ])
        self.assertEqual(len(sales), 1)
        self.assertEqual(result, sales.id)
        self.assertEqual(sales.name, self.data_json['name'])
        self.assertEqual(sales.state, 'sale')
        self.assertEqual(len(sales.invoice_ids), 1)
        self.assertEqual(len(sales.picking_ids), 1)
        self.assertEqual(len(sales.invoice_ids[0].payment_ids), 0)
        self.data_json.update({
            'name': 'SO1475',
            'state': 'confirmed-no-invoice',
            'invoice_date': '2023-01-16 14:30:00',
        })
        self.assertEqual(self.data_json['state'], 'confirmed-no-invoice')
        result = self.env['sale.order'].json_import(self.data_json)
        sales = self.env['sale.order'].search([
            ('id', '=', result),
        ])
        self.assertEqual(len(sales), 1)
        self.assertEqual(result, sales.id)
        self.assertEqual(sales.name, self.data_json['name'])
        self.assertEqual(sales.state, 'sale')
        self.assertEqual(len(sales.invoice_ids), 0)
        self.assertEqual(len(sales.picking_ids), 1)

    def test_sale_import_get_partner_id_ok_01(self):
        self.assertFalse(self.free_delivery.include_cheapest_carrier)
        self.free_delivery.include_cheapest_carrier = True
        self.data_json.update({
            'name': 'SO1443',
            'state': 'confirmed',
            'journal_name': self.journal.name,
            'payment_method_name': self.payment_method.name,
            'invoice_date': '2023-01-15 12:30:00',
        })
        self.data_json['partner']['id'] = self.partner_1.id
        self.assertEqual(self.data_json['partner']['id'], self.partner_1.id)
        result = self.env['sale.order'].json_import(self.data_json)
        sales = self.env['sale.order'].search([
            ('id', '=', result),
        ])
        self.assertEqual(len(sales), 1)
        self.assertEqual(sales.state, 'sale')
        self.assertEqual(sales.partner_id, self.partner_1)

    def test_sale_import_get_partner_id_error_not_found_02(self):
        self.assertFalse(self.free_delivery.include_cheapest_carrier)
        self.free_delivery.include_cheapest_carrier = True
        self.data_json.update({
            'name': 'SO1443',
            'state': 'confirmed',
            'journal_name': self.journal.name,
            'payment_method_name': self.payment_method.name,
            'invoice_date': '2023-01-15 12:30:00',
        })
        self.data_json['partner']['id'] = 9999999
        self.assertEqual(self.data_json['partner']['id'], 9999999)
        with self.assertRaises(exceptions.ValidationError) as result:
            self.env['sale.order'].json_import(self.data_json)
        self.assertEqual(
            result.exception.name,
            'Partner id is not valid. Please review it.')

    def test_sale_import_get_partner_id_error_string_03(self):
        self.assertFalse(self.free_delivery.include_cheapest_carrier)
        self.free_delivery.include_cheapest_carrier = True
        self.data_json.update({
            'name': 'SO1443',
            'state': 'confirmed',
            'journal_name': self.journal.name,
            'payment_method_name': self.payment_method.name,
            'invoice_date': '2023-01-15 12:30:00',
        })
        self.data_json['partner']['id'] = ''
        self.assertEqual(self.data_json['partner']['id'], '')
        result = self.env['sale.order'].json_import(self.data_json)
        sales = self.env['sale.order'].search([
            ('id', '=', result),
        ])
        self.assertEqual(len(sales), 1)
        self.assertEqual(sales.state, 'sale')
        self.assertEqual(
            sales.partner_id.name, self.data_json['partner']['name'])

    def test_sale_import_get_partner_id_error_empty_key_04(self):
        self.assertFalse(self.free_delivery.include_cheapest_carrier)
        self.free_delivery.include_cheapest_carrier = True
        self.data_json.update({
            'name': 'SO1443',
            'state': 'confirmed',
            'journal_name': self.journal.name,
            'payment_method_name': self.payment_method.name,
            'invoice_date': '2023-01-15 12:30:00',
        })
        self.data_json['partner']['id'] = None
        self.assertEqual(self.data_json['partner']['id'], None)
        result = self.env['sale.order'].json_import(self.data_json)
        sales = self.env['sale.order'].search([
            ('id', '=', result),
        ])
        self.assertEqual(len(sales), 1)
        self.assertEqual(sales.state, 'sale')
        self.assertEqual(
            sales.partner_id.name, self.data_json['partner']['name'])

    def test_sale_import_get_partner_id_only_05(self):
        self.assertFalse(self.free_delivery.include_cheapest_carrier)
        self.free_delivery.include_cheapest_carrier = True
        self.data_json.update({
            'name': 'SO1443',
            'state': 'confirmed',
            'journal_name': self.journal.name,
            'payment_method_name': self.payment_method.name,
            'invoice_date': '2023-01-15 12:30:00',
        })
        self.data_json['partner']['id'] = self.partner_1.id
        del self.data_json['partner']['email']
        del self.data_json['partner']['name']
        del self.data_json['partner']['street']
        result = self.env['sale.order'].json_import(self.data_json)
        sales = self.env['sale.order'].search([
            ('id', '=', result),
        ])
        self.assertEqual(len(sales), 1)
        self.assertEqual(sales.state, 'sale')
        self.assertEqual(sales.partner_id, self.partner_1)

    def test_sale_import_get_partner_shipping_id_ok_01(self):
        self.assertFalse(self.free_delivery.include_cheapest_carrier)
        self.free_delivery.include_cheapest_carrier = True
        self.data_json.update({
            'name': 'SO1443',
            'state': 'confirmed',
            'journal_name': self.journal.name,
            'payment_method_name': self.payment_method.name,
            'invoice_date': '2023-01-15 12:30:00',
            'partner_shipping': {
                'name': self.data_json['name'],
                'email': self.data_json['partner']['email'],
                'street': self.data_json['partner']['street'],
                'street2': 'Customer street 2',
                'city': 'City test',
                'phone': '555443322',
            }
        })
        partner_delivery = self.env['res.partner'].create({
            'name': 'Test shipping partner',
            'parent_id': self.partner_1.id,
            'type': 'delivery',
        })
        self.data_json['partner_shipping']['id'] = partner_delivery.id
        self.assertEqual(
            self.data_json['partner_shipping']['id'], partner_delivery.id)
        result = self.env['sale.order'].json_import(self.data_json)
        sales = self.env['sale.order'].search([
            ('id', '=', result),
        ])
        self.assertEqual(len(sales), 1)
        self.assertEqual(sales.state, 'sale')
        self.assertEqual(sales.partner_shipping_id, partner_delivery)

    def test_sale_import_get_partner_shipping_id_error_not_found_02(self):
        self.assertFalse(self.free_delivery.include_cheapest_carrier)
        self.free_delivery.include_cheapest_carrier = True
        self.data_json.update({
            'name': 'SO1443',
            'state': 'confirmed',
            'journal_name': self.journal.name,
            'payment_method_name': self.payment_method.name,
            'invoice_date': '2023-01-15 12:30:00',
            'partner_shipping': {
                'name': self.data_json['name'],
                'email': self.data_json['partner']['email'],
                'street': self.data_json['partner']['street'],
                'street2': 'Customer street 2',
                'city': 'City test',
                'phone': '555443322',
            }
        })
        self.data_json['partner_shipping']['id'] = 9999999
        self.assertEqual(self.data_json['partner_shipping']['id'], 9999999)
        with self.assertRaises(exceptions.ValidationError) as result:
            self.env['sale.order'].json_import(self.data_json)
        self.assertEqual(
            result.exception.name,
            'Partner shipping id is not valid. Please review it.')

    def test_sale_import_get_partner_shipping_id_error_string_03(self):
        self.assertFalse(self.free_delivery.include_cheapest_carrier)
        self.free_delivery.include_cheapest_carrier = True
        self.data_json.update({
            'name': 'SO1443',
            'state': 'confirmed',
            'journal_name': self.journal.name,
            'payment_method_name': self.payment_method.name,
            'invoice_date': '2023-01-15 12:30:00',
            'partner_shipping': {
                'name': self.data_json['name'],
                'email': self.data_json['partner']['email'],
                'street': self.data_json['partner']['street'],
                'street2': 'Customer street 2',
                'city': 'City test',
                'phone': '555443322',
            },
        })
        self.data_json['partner_shipping']['id'] = ''
        self.assertEqual(self.data_json['partner_shipping']['id'], '')
        result = self.env['sale.order'].json_import(self.data_json)
        sales = self.env['sale.order'].search([
            ('id', '=', result),
        ])
        self.assertEqual(len(sales), 1)
        self.assertEqual(sales.state, 'sale')
        self.assertEqual(
            sales.partner_shipping_id.name,
            self.data_json['partner_shipping']['name'])

    def test_sale_import_get_partner_shipping_cast_id_string_04(self):
        self.assertFalse(self.free_delivery.include_cheapest_carrier)
        self.free_delivery.include_cheapest_carrier = True
        self.data_json.update({
            'name': 'SO2336',
            'state': 'confirmed',
            'journal_name': self.journal.name,
            'payment_method_name': self.payment_method.name,
            'invoice_date': '2023-01-15 12:30:00',
            'partner_shipping': {
                'name': self.data_json['name'],
                'email': self.data_json['partner']['email'],
                'street': self.data_json['partner']['street'],
                'street2': 'Customer street 2',
                'city': 'City test',
                'phone': '555443322',
            },
        })
        partner_delivery = self.env['res.partner'].create({
            'name': 'Test shipping partner',
            'parent_id': self.partner_1.id,
            'type': 'delivery',
        })
        self.data_json['partner_shipping']['id'] = '%s' % partner_delivery.id
        self.assertEqual(
            self.data_json['partner_shipping']['id'],
            '%s' % partner_delivery.id)
        result = self.env['sale.order'].json_import(self.data_json)
        sales = self.env['sale.order'].search([
            ('id', '=', result),
        ])
        self.assertEqual(len(sales), 1)
        self.assertEqual(sales.state, 'sale')
        self.assertEqual(sales.partner_shipping_id.name, partner_delivery.name)

    def test_sale_import_get_partner_shipping_id_error_empty_key_04(self):
        self.assertFalse(self.free_delivery.include_cheapest_carrier)
        self.free_delivery.include_cheapest_carrier = True
        self.data_json.update({
            'name': 'SO1443',
            'state': 'confirmed',
            'journal_name': self.journal.name,
            'payment_method_name': self.payment_method.name,
            'invoice_date': '2023-01-15 12:30:00',
            'partner_shipping': {
                'name': self.data_json['name'],
                'email': self.data_json['partner']['email'],
                'street': self.data_json['partner']['street'],
                'street2': 'Customer street 2',
                'city': 'City test',
                'phone': '555443322',
            },
        })
        self.data_json['partner_shipping']['id'] = None
        self.assertEqual(self.data_json['partner_shipping']['id'], None)
        result = self.env['sale.order'].json_import(self.data_json)
        sales = self.env['sale.order'].search([
            ('id', '=', result),
        ])
        self.assertEqual(len(sales), 1)
        self.assertEqual(sales.state, 'sale')
        self.assertEqual(
            sales.partner_shipping_id.name,
            self.data_json['partner_shipping']['name'])

    def test_sale_import_get_partner_shipping_id_only_05(self):
        self.assertFalse(self.free_delivery.include_cheapest_carrier)
        self.free_delivery.include_cheapest_carrier = True
        partner_delivery = self.env['res.partner'].create({
            'name': 'Test shipping partner',
            'parent_id': self.partner_1.id,
            'type': 'delivery',
        })
        self.data_json.update({
            'name': 'SO1443',
            'state': 'confirmed',
            'journal_name': self.journal.name,
            'payment_method_name': self.payment_method.name,
            'invoice_date': '2023-01-15 12:30:00',
            'partner_shipping': {
                'id': partner_delivery.id,
            },
        })
        self.assertEqual(
            self.data_json['partner_shipping']['id'], partner_delivery.id)
        result = self.env['sale.order'].json_import(self.data_json)
        sales = self.env['sale.order'].search([
            ('id', '=', result),
        ])
        self.assertEqual(len(sales), 1)
        self.assertEqual(sales.state, 'sale')
        self.assertTrue(sales.import_by_json)
        self.assertEqual(sales.partner_shipping_id, partner_delivery)

    def test_import_amount_zero_invoice_draft_to_paid_directly_at_open(self):
        self.assertFalse(self.free_delivery.include_cheapest_carrier)
        self.free_delivery.include_cheapest_carrier = True
        partner_delivery = self.env['res.partner'].create({
            'name': 'Test shipping partner',
            'parent_id': self.partner_1.id,
            'type': 'delivery',
        })
        self.data_json.update({
            'name': 'SO2396',
            'state': 'confirmed',
            'journal_name': self.journal.name,
            'payment_method_name': self.payment_method.name,
            'invoice_date': '2023-01-15 12:30:00',
            'partner_shipping': {
                'id': partner_delivery.id,
            },
        })
        self.data_json['order_line'][1]['product_uom_qty'] = 1
        self.data_json['order_line'][1]['price_unit_taxed'] = -95.59
        self.data_json['order_line'][1]['price_unit_untaxed'] = -79
        result = self.env['sale.order'].json_import(self.data_json)
        sales = self.env['sale.order'].search([
            ('id', '=', result),
        ])
        self.assertEqual(len(sales), 1)
        self.assertEqual(sales.state, 'sale')
        self.assertTrue(sales.import_by_json)
        self.assertEqual(sales.amount_total, 0)
        self.assertEqual(len(sales.picking_ids), 1)
        self.assertEqual(sales.picking_ids[0].state, 'assigned')
        self.assertEqual(len(sales.invoice_ids), 1)
        self.assertEqual(sales.invoice_ids[0].amount_total, 0)
        self.assertEqual(sales.invoice_ids[0].state, 'paid')

    def test_import_sale_search_product_by_id_01(self):
        self.assertFalse(self.free_delivery.include_cheapest_carrier)
        self.free_delivery.include_cheapest_carrier = True
        self.data_json.update({
            'name': 'SO2424',
            'journal_name': self.journal.name,
            'invoice_date': '2022-01-01',
            'payment_method_name': self.payment_method.name,
        })
        self.data_json['order_line'][0]['product_id'] = self.product_1.id
        self.data_json['order_line'][1]['product_id'] = self.product_2.id
        self.assertEqual(
            self.data_json['order_line'][0]['product_id'], self.product_1.id)
        self.assertEqual(
            self.data_json['order_line'][1]['product_id'], self.product_2.id)
        result = self.env['sale.order'].json_import(self.data_json)
        sales = self.env['sale.order'].search([
            ('id', '=', result),
        ])
        self.assertEqual(len(sales), 1)
        self.assertEqual(sales.state, 'sale')
        self.assertEqual(sales.order_line[0].product_id, self.product_1)
        self.assertEqual(sales.order_line[1].product_id, self.product_2)

    def test_import_sale_search_product_by_string_id(self):
        self.assertFalse(self.free_delivery.include_cheapest_carrier)
        self.free_delivery.include_cheapest_carrier = True
        self.data_json.update({
            'name': 'SO2446',
            'journal_name': self.journal.name,
            'invoice_date': '2022-01-01',
            'payment_method_name': self.payment_method.name,
        })
        self.data_json['order_line'][0]['product_id'] = str(self.product_1.id)
        self.data_json['order_line'][1]['product_id'] = str(self.product_2.id)
        self.assertEqual(
            self.data_json['order_line'][0]['product_id'],
            str(self.product_1.id))
        self.assertEqual(
            self.data_json['order_line'][1]['product_id'],
            str(self.product_2.id))
        result = self.env['sale.order'].json_import(self.data_json)
        sales = self.env['sale.order'].search([
            ('id', '=', result),
        ])
        self.assertEqual(len(sales), 1)
        self.assertEqual(sales.state, 'sale')
        self.assertEqual(sales.order_line[0].product_id, self.product_1)
        self.assertEqual(sales.order_line[1].product_id, self.product_2)

    def test_import_sale_no_name_in_json_data(self):
        self.assertFalse(self.free_delivery.include_cheapest_carrier)
        self.free_delivery.include_cheapest_carrier = True
        self.data_json.update({
            'journal_name': self.journal.name,
            'invoice_date': '2024-06-30',
            'payment_method_name': self.payment_method.name,
            'state': 'no-confirmed',
        })
        del self.data_json['name']
        self.assertTrue('name' not in self.data_json)
        result = self.env['sale.order'].json_import(self.data_json)
        sales = self.env['sale.order'].search([
            ('id', '=', result),
        ])
        self.assertEqual(len(sales), 1)
        self.assertEqual(sales.state, 'draft')
        self.assertTrue(sales.name)
        self.assertNotEqual(sales.name, '')

    def test_import_sale_line_discount_10(self):
        self.assertFalse(self.free_delivery.include_cheapest_carrier)
        self.free_delivery.include_cheapest_carrier = True
        self.data_json.update({
            'journal_name': self.journal.name,
            'invoice_date': '2024-06-30',
            'payment_method_name': self.payment_method.name,
            'state': 'no-confirmed',
        })
        del self.data_json['name']
        self.data_json['order_line'][0]['discount'] = 10.0
        self.data_json['order_line'][1]['discount'] = 10.0
        result = self.env['sale.order'].json_import(self.data_json)
        sales = self.env['sale.order'].search([
            ('id', '=', result),
        ])
        self.assertEqual(len(sales), 1)
        self.assertEqual(sales.state, 'draft')
        self.assertEqual(sales.order_line[0].discount, 10)
        line_01 = self.data_json['order_line'][0]
        line_01_total = line_01['product_uom_qty'] * line_01['price_unit_taxed']
        line_01_total = line_01_total * (1 - line_01['discount'] / 100)
        self.assertEqual(
            sales.order_line[0].price_total, round(line_01_total, 2))
        self.assertEqual(sales.order_line[1].discount, 10)
        line_02 = self.data_json['order_line'][1]
        line_02_total = line_02['product_uom_qty'] * line_02['price_unit_taxed']
        line_02_total = line_02_total * (1 - line_02['discount'] / 100)
        self.assertEqual(
            sales.order_line[1].price_total, line_02_total)

    def test_import_sale_line_discount_100(self):
        self.assertFalse(self.free_delivery.include_cheapest_carrier)
        self.free_delivery.include_cheapest_carrier = True
        self.data_json.update({
            'journal_name': self.journal.name,
            'invoice_date': '2024-06-30',
            'payment_method_name': self.payment_method.name,
            'state': 'no-confirmed',
        })
        del self.data_json['name']
        self.data_json['order_line'][1]['discount'] = 100.0
        self.assertTrue('discount' not in self.data_json['order_line'][0])
        self.assertEqual(self.data_json['order_line'][1]['discount'], 100.0)
        result = self.env['sale.order'].json_import(self.data_json)
        sales = self.env['sale.order'].search([
            ('id', '=', result),
        ])
        self.assertEqual(len(sales), 1)
        self.assertEqual(sales.state, 'draft')
        self.assertEqual(sales.order_line[0].discount, 0)
        self.assertEqual(sales.order_line[1].discount, 100)
        line_02 = self.data_json['order_line'][1]
        line_02_total = line_02['product_uom_qty'] * line_02['price_unit_taxed']
        line_02_total = line_02_total * (1 - line_02['discount'] / 100)
        self.assertEqual(
            sales.order_line[1].price_total, line_02_total)

    def test_import_sale_extra_attachments_txt(self):
        self.assertFalse(self.free_delivery.include_cheapest_carrier)
        self.free_delivery.include_cheapest_carrier = True
        self.data_json.update({
            'journal_name': self.journal.name,
            'invoice_date': '2024-06-30',
            'payment_method_name': self.payment_method.name,
            'state': 'no-confirmed',
        })
        del self.data_json['name']
        file_name = 'test_extra_attachment.txt'
        text = 'Text string test'
        text = base64.b64encode(text.encode('utf-8'))
        self.data_json['attachments'] = [
            {
                'name': file_name,
                'type': 'binary',
                'mimetype': 'text/plain',
                'datas': '%s' % text,
            },
        ]
        result = self.env['sale.order'].json_import(self.data_json)
        sales = self.env['sale.order'].search([
            ('id', '=', result),
        ])
        self.assertEqual(len(sales), 1)
        self.assertEqual(sales.state, 'draft')
        attachments = self.env['ir.attachment'].search([
            ('res_id', '=', sales.id),
            ('res_model', '=', sales._name),
        ])
        self.assertEquals(len(attachments), 2)
        txt_file = attachments.filtered(lambda a: a.datas_fname == file_name)
        self.assertEqual(len(txt_file), 1)

    def test_import_sale_extra_attachments_pdf(self):
        self.assertFalse(self.free_delivery.include_cheapest_carrier)
        self.free_delivery.include_cheapest_carrier = True
        self.data_json.update({
            'journal_name': self.journal.name,
            'invoice_date': '2024-06-30',
            'payment_method_name': self.payment_method.name,
            'state': 'no-confirmed',
        })
        del self.data_json['name']
        file_name = 'test_extra_attachment.pdf'
        path_file = '%s/tools/sale_order_document.pdf' % get_resource_path(
            'sale_order_import_json')
        with open(path_file, 'rb') as file:
            pdf_content = base64.b64encode(file.read()).decode('utf-8')
            self.data_json['attachments'] = [
                {
                    'name': file_name,
                    'type': 'binary',
                    'mimetype': 'application/pdf',
                    'datas': pdf_content,
                }
            ]
        result = self.env['sale.order'].json_import(self.data_json)
        sales = self.env['sale.order'].search([
            ('id', '=', result),
        ])
        self.assertEqual(len(sales), 1)
        self.assertEqual(sales.state, 'draft')
        attachments = self.env['ir.attachment'].search([
            ('res_id', '=', sales.id),
            ('res_model', '=', sales._name),
        ])
        self.assertEqual(len(attachments), 2)
        pdf_file = attachments.filtered(lambda a: a.datas_fname == file_name)
        self.assertEqual(len(pdf_file), 1)

    def test_import_sale_multiple_extra_attachments(self):
        self.assertFalse(self.free_delivery.include_cheapest_carrier)
        self.free_delivery.include_cheapest_carrier = True
        self.data_json.update({
            'journal_name': self.journal.name,
            'invoice_date': '2024-06-30',
            'payment_method_name': self.payment_method.name,
            'state': 'no-confirmed',
        })
        del self.data_json['name']
        pdf_name = 'test_extra_attachment.pdf'
        path_file = '%s/tools/sale_order_document.pdf' % get_resource_path(
            'sale_order_import_json')
        with open(path_file, 'rb') as file:
            pdf_content = base64.b64encode(file.read()).decode('utf-8')
        txt_name = 'test_extra_attachment.txt'
        text = 'Text string test'
        text = base64.b64encode(text.encode('utf-8'))
        self.data_json['attachments'] = [
            {
                'name': txt_name,
                'type': 'binary',
                'mimetype': 'text/plain',
                'datas': '%s' % text,
            },
            {
                'name': pdf_name,
                'type': 'binary',
                'mimetype': 'application/pdf',
                'datas': pdf_content,
            }
        ]
        result = self.env['sale.order'].json_import(self.data_json)
        sales = self.env['sale.order'].search([
            ('id', '=', result),
        ])
        self.assertEqual(len(sales), 1)
        self.assertEqual(sales.state, 'draft')
        attachments = self.env['ir.attachment'].search([
            ('res_id', '=', sales.id),
            ('res_model', '=', sales._name),
        ])
        self.assertEqual(len(attachments), 3)
        pdf_file = attachments.filtered(lambda a: a.datas_fname == pdf_name)
        self.assertEqual(len(pdf_file), 1)
        txt_file = attachments.filtered(lambda a: a.datas_fname == txt_name)
        self.assertEqual(len(txt_file), 1)

    def test_import_sale_json_action_msg_error_raise(self):
        self.assertEqual(
            self.env.user.company_id.action_msg_price, 'raise_error')
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
        self.assertIn(
            'Price with taxes does not match with calculated by Odoo:\n'
            'Line taxes in JSON: 82.95\nTotal line taxes calculated '
            'by Odoo: 95.59', result.exception.name)
        self.assertIn('Line/Product [1/TEST-01]', result.exception.name)

    def test_import_sale_json_action_msg_error_post_note(self):
        self.assertEqual(
            self.env.user.company_id.action_msg_price, 'raise_error')
        self.env.user.company_id.action_msg_price = 'post_note'
        self.assertEqual(self.env.user.company_id.action_msg_price, 'post_note')
        self.free_delivery.include_cheapest_carrier = True
        self.assertTrue(self.free_delivery.include_cheapest_carrier)
        self.data_json.update({
            'name': 'SOTAX3',
            'journal_name': self.journal.name,
            'invoice_date': '2022-01-01',
            'payment_method_name': self.payment_method.name,
        })
        self.data_json['order_line'][0].update({
            'price_unit_taxed': '83',
        })
        self.assertEqual(
            self.data_json['order_line'][0]['price_unit_taxed'], '83')
        result = self.env['sale.order'].json_import(self.data_json)
        sales = self.env['sale.order'].search([
            ('id', '=', result),
        ])
        self.assertEqual(len(sales), 1)
        self.assertEqual(sales.state, 'sale')
        msg = sales.message_ids.filtered(
            lambda m: 'taxes does not match' in m.body)
        self.assertEqual(len(msg), 1)

    def test_import_sale_json_email_duplicated(self):
        partner_duplicated = self.env['res.partner'].create({
            'name': 'Partner test 1 duplicated',
            'street': 'Partner street 1 duplicated',
            'email': 'partner@partner.com',
        })
        self.assertEqual(
            self.env.user.company_id.action_msg_price, 'raise_error')
        self.env.user.company_id.action_msg_price = 'post_note'
        self.assertEqual(
            self.env.user.company_id.action_msg_price, 'post_note')
        self.free_delivery.include_cheapest_carrier = True
        self.assertTrue(self.free_delivery.include_cheapest_carrier)
        self.data_json.update({
            'name': 'SOTAX3',
            'journal_name': self.journal.name,
            'invoice_date': '2022-01-01',
            'payment_method_name': self.payment_method.name,
            'partner': {
                'name': partner_duplicated.name,
                'street': partner_duplicated.street,
                'email': partner_duplicated.email,
            },
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
            'Multiple partners with same email "partner@partner.com"')

    def test_import_json_sequence_not_incremented_on_error(self):
        self.free_delivery.include_cheapest_carrier = True
        sale_seq = self.env['ir.sequence'].search([
            ('code', '=', 'sale.order'),
        ], limit=1)
        initial_next_number = sale_seq.number_next_actual
        invalid_data = self.data_json.copy()
        invalid_data.pop('name', None)
        invalid_data['order_line'][0]['default_code'] = 'TEST-FAIL'
        with self.assertRaises(exceptions.ValidationError):
            self.env['sale.order'].json_import(invalid_data)
        self.assertEqual(sale_seq.number_next_actual, initial_next_number)
        valid_data = self.data_json.copy()
        valid_data.pop('name', None)
        valid_data['order_line'][0]['default_code'] = 'TEST-01'
        result_id = self.env['sale.order'].json_import(valid_data)
        sale = self.env['sale.order'].browse(result_id)
        self.assertTrue(sale.name.startswith('SO'))
        self.assertEqual(sale_seq.number_next_actual, initial_next_number + 1)

    def test_import_sale_line_name_kept_after_onchange_chain(self):
        self.free_delivery.include_cheapest_carrier = True
        self.data_json.update({
            'name': 'SONAME01',
            'journal_name': self.journal.name,
            'invoice_date': '2022-01-01',
            'payment_method_name': self.payment_method.name,
        })
        result = self.env['sale.order'].json_import(self.data_json)
        sale = self.env['sale.order'].search([('id', '=', result)])
        self.assertEqual(len(sale.order_line), 2)
        self.assertTrue(sale.order_line[0].name)
        self.assertIn(self.product_1.name, sale.order_line[0].name)
        self.assertTrue(sale.order_line[1].name)
        self.assertIn(self.product_2.name, sale.order_line[1].name)

    def test_import_json_error_saved_to_filestore(self):
        self.authenticate('admin', 'admin')
        self.opener.headers.update({
            'Content-type': 'application/json',
            'Accept': 'text/plain',
        })
        error_dir = os.path.join(
            config.filestore(self.env.cr.dbname),
            'sale_order_import_json_error')
        self._cleanup_import_error_dir()
        invalid_data = copy.deepcopy(self.data_json)
        invalid_data['order_line'][0]['default_code'] = 'TEST-DOES-NOT-EXIST'
        response = self.url_open(
            '/sale_order/import', data=json.dumps(invalid_data))
        self.assertEqual(response.status_code, 200)
        self.assertTrue(os.path.exists(error_dir))
        new_files = [
            f for f in os.listdir(error_dir)
            if f.startswith('import_') and f.endswith('.json')]
        self.assertEqual(len(new_files), 1)
        error_file = os.path.join(error_dir, new_files[0])
        with open(error_file) as f:
            content = json.load(f)
        self.assertIn('error', content)
        self.assertIn('TEST-DOES-NOT-EXIST', content['error'])
        self.assertEqual(content['data']['name'], invalid_data['name'])
        self.assertEqual(
            content['data']['order_line'][0]['default_code'],
            'TEST-DOES-NOT-EXIST')
