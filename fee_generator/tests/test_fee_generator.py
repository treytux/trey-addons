# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp.tests import common
from openerp import fields


class TestFeeGenerator(common.TransactionCase):

    def setUp(self):
        super(TestFeeGenerator, self).setUp()
        self.taxs_21 = self.env['account.tax'].create({
            'name': '%21%',
            'type': 'percent',
            'amount': 0.21,
            'type_tax_use': 'all',
            'applicable_type': 'true',
            'sequence': 1,
            'company_id': self.ref('base.main_company')})
        self.customer_01 = self.env['res.partner'].create({
            'name': 'Customer 01',
            'email': 'customer1@test.com',
            'street': 'Avda Andalucia, 23',
            'phone': '958123456'})
        self.pt_01 = self.env['product.template'].create({
            'name': 'Product 01',
            'type': 'consu',
            'taxes_id': [(6, 0, [self.taxs_21.id])]})
        self.pp_01 = self.env['product.product'].create({
            'product_tmpl_id': self.pt_01.id,
            'list_price': 1000})
        self.pt_02 = self.env['product.template'].create({
            'name': 'Product 02',
            'type': 'consu',
            'taxes_id': [(6, 0, [])]})
        self.pp_02 = self.env['product.product'].create({
            'product_tmpl_id': self.pt_02.id,
            'list_price': 2000})
        self.pt_03 = self.env['product.template'].create({
            'name': 'Product 03',
            'type': 'consu',
            'taxes_id': [(6, 0, [self.taxs_21.id])]})
        self.pp_03 = self.env['product.product'].create({
            'product_tmpl_id': self.pt_03.id,
            'list_price': 3000})
        self.order_01 = self.env['sale.order'].create({
            'partner_id': self.customer_01.id,
            'pricelist_id': self.ref('product.list0'),
            'date_order': fields.Date.today()})
        self.fee_gen_01 = self.env['fee.generator'].create({
            'partner_id': self.customer_01.id,
            'fee_product_id': self.pp_01.id,
            'description': 'Producto cuota',
            'reference': 'Referencia factura',
            'total_untaxed': 1200,
            'fee_number': 10,
            'start_date': '2017-01-01',
            'next_date': '2017-01-01',
            'model_id': self.env['ir.model'].search(
                [('model', '=', 'sale.order')])[0].id,
            'res_id': self.order_01.id})

    def test_change_fee_product(self):
        with self.env.do_in_onchange():
            record = self.env['fee.generator'].new()
            record.fee_product_id = self.pp_02.id
            record.onchange_fee_product_id()
            self.assertEqual(record.description, self.pp_02.name)

    def test_change_discount(self):
        self.fee_gen_01.discount = 10.00
        self.assertEqual(self.fee_gen_01.amount_discount, 120)
        self.assertEqual(self.fee_gen_01.residual_untaxed, 1200 * (
            1 - self.fee_gen_01.discount / 100))
        self.assertEqual(self.fee_gen_01.fee_amount_untaxed, 120)

    def test_change_total_untaxed(self):
        self.fee_gen_01.total_untaxed = 2400
        self.assertEqual(self.fee_gen_01.fee_amount_untaxed, 240)

    def test_change_fee_number(self):
        self.fee_gen_01.total_untaxed = 1200
        self.fee_gen_01.fee_number = 12.00
        self.assertEqual(self.fee_gen_01.fee_amount_untaxed, 100)

    def test_change_start_date(self):
        self.fee_gen_01.start_date = '2017-02-01'
        self.fee_gen_01.onchange_start_date()
        self.assertEqual(
            self.fee_gen_01.next_date, self.fee_gen_01.start_date)
        self.assertEqual(self.fee_gen_01.end_date, '2017-11-01')

    def test_change_next_date(self):
        self.fee_gen_01.next_date = '2017-03-01'
        self.assertEqual(self.fee_gen_01.end_date, '2017-12-01')

    def test_change_recurring_interval(self):
        self.fee_gen_01.recurring_interval = 2
        self.assertEqual(
            self.fee_gen_01.next_date, self.fee_gen_01.start_date)
        self.assertEqual(self.fee_gen_01.end_date, '2018-07-01')

    def test_change_recurring_rule_type(self):
        self.fee_gen_01.recurring_rule_type = 'yearly'
        self.assertEqual(
            self.fee_gen_01.next_date, self.fee_gen_01.start_date)
        self.assertEqual(self.fee_gen_01.end_date, '2026-01-01')

    def test_change_recurring_values(self):
        self.fee_gen_01.recurring_interval = 2
        self.fee_gen_01.recurring_rule_type = 'yearly'
        self.assertEqual(
            self.fee_gen_01.next_date, self.fee_gen_01.start_date)
        self.assertEqual(self.fee_gen_01.end_date, '2035-01-01')

    def test_model_resource_not_found(self):
        self.fee_gen_01.model_id = self.env['ir.model'].search(
            [('model', '=', 'sale.order')])[0].id
        self.fee_gen_01.res_id = -10
        self.fee_gen_01.button_generate_next_invoice()
        self.assertEqual(len(self.fee_gen_01.invoice_ids), 1)
        self.assertEqual(self.fee_gen_01.invoice_ids[0].origin, False)

    def test_generate_invoices(self):
        [self.fee_gen_01.button_generate_next_invoice() for i in range(10)]
        self.assertEqual(len(self.fee_gen_01.invoice_ids), 10)
        self.assertEqual(self.fee_gen_01.residual_untaxed, 0.00)
