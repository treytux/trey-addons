###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo.tests import common


class TestSaleOrderImportJsonCreditLimit(common.TransactionCase):

    def setUp(self):
        super().setUp()
        self.credit_limit = 100
        self.partner = self.env['res.partner'].create({
            'name': 'Customer',
            'is_company': True,
            'vat': 'ESA00000000',
            'credit_limit': self.credit_limit,
            'risk_sale_order_include': True,
            'email': 'new@partner.com',
        })
        self.product = self.env['product.product'].create({
            'type': 'service',
            'company_id': False,
            'name': 'Product test',
            'standard_price': 100,
            'list_price': 250,
        })
        self.sale_01 = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'order_line': [
                (0, 0, {
                    'product_id': self.product.id,
                    'price_unit': self.product.list_price,
                    'product_uom_qty': 1,
                }),
            ],
        })
        self.tax = self.env['account.tax'].create({
            'name': 'Tax test 21%',
            'type_tax_use': 'sale',
            'amount_type': 'percent',
            'amount': 21,
        })
        self.free_delivery = self.env.ref('delivery.free_delivery_carrier')
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
        self.journal_bank = self.env['account.journal'].create({
            'name': 'Bank test',
            'code': 'BNKT',
            'type': 'bank',
            'default_credit_account_id': self.account.id,
            'default_debit_account_id': self.account.id,
        })
        self.product_1 = self.env['product.product'].create({
            'type': 'consu',
            'company_id': False,
            'name': 'Product Test 1',
            'standard_price': 10,
            'list_price': 150,
            'default_code': 'TEST-01',
            'taxes_id': [
                (6, 0, [self.tax.id]),
            ],
        })
        self.data_json = {
            'name': 'SO155',
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
            ],
            'state': 'confirmed',
            'warehouse_id': 1,
            'payment_journal_name': 'Bank test',
        }

    def test_confirm_sale_credit_limit_manual_exception(self):
        self.assertEqual(self.partner.credit_limit, self.credit_limit)
        self.assertTrue(self.partner.risk_sale_order_include)
        res = self.sale_01.action_confirm()
        self.assertEqual(res['type'], 'ir.actions.act_window')
        self.assertEqual(res['target'], 'new')
        self.assertEqual(res['res_model'], 'partner.risk.exceeded.wiz')
        self.assertEqual(self.sale_01.state, 'draft')

    def test_confirm_sale_credit_limit_manual_ok(self):
        self.assertEqual(self.partner.credit_limit, self.credit_limit)
        self.assertTrue(self.partner.risk_sale_order_include)
        self.sale_01.order_line[0]['price_unit'] = 50
        self.sale_01.action_confirm()
        self.assertEqual(self.sale_01.state, 'sale')

    def test_sale_import_json_credit_limit_ok(self):
        self.assertEqual(self.partner.credit_limit, self.credit_limit)
        self.assertTrue(self.partner.risk_sale_order_include)
        self.assertFalse(self.free_delivery.include_cheapest_carrier)
        self.free_delivery.include_cheapest_carrier = True
        self.assertTrue(self.free_delivery.include_cheapest_carrier)
        self.data_json.update({
            'journal_name': self.journal_bank.name,
            'invoice_date': '2024-01-01',
            'payment_method_name': self.payment_method.name,
        })
        result = self.env['sale.order'].json_import(self.data_json)
        sale = self.env['sale.order'].search([('id', '=', result)])
        self.assertEqual(len(sale), 1)
        self.assertEqual(result, sale.id)
        self.assertEqual(sale.state, 'sale')

    def test_sale_import_json_credit_limit_exceeded(self):
        self.assertEqual(self.partner.credit_limit, self.credit_limit)
        self.assertTrue(self.partner.risk_sale_order_include)
        self.assertFalse(self.free_delivery.include_cheapest_carrier)
        self.free_delivery.include_cheapest_carrier = True
        self.assertTrue(self.free_delivery.include_cheapest_carrier)
        self.data_json.update({
            'journal_name': self.journal_bank.name,
            'invoice_date': '2024-01-01',
            'payment_method_name': self.payment_method.name,
        })
        self.data_json['order_line'][0]['price_unit_untaxed'] = 100
        self.data_json['order_line'][0]['price_unit_taxed'] = 121
        result = self.env['sale.order'].json_import(self.data_json)
        sales = self.env['sale.order'].search([('id', '=', result)])
        self.assertEqual(len(sales), 1)
        self.assertEqual(result, sales.id)
        self.assertEqual(sales.name, self.data_json['name'])
        self.assertEqual(sales.state, 'sale')
