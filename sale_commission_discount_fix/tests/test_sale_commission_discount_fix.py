# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp.tests import common
from openerp import fields


class TestSaleCommissionDiscountFix(common.TransactionCase):

    def setUp(self):
        super(TestSaleCommissionDiscountFix, self).setUp()
        self.taxs_21 = self.env['account.tax'].create({
            'name': '%21%',
            'type': 'percent',
            'amount': 0.21,
            'type_tax_use': 'all',
            'applicable_type': 'true',
            'sequence': 1,
            'company_id': self.ref('base.main_company')})
        self.commission_10 = self.env['sale.commission'].create({
            'name': '10%',
            'amount_base_type': 'net_amount',
            'commission_type': 'fixed',
            'invoice_state': 'open',
            'company_id': 1,
            'fix_qty': 10.00})
        self.agent_01 = self.env['res.partner'].create({
            'name': 'Customer 01',
            'agent': True,
            'supplier': True,
            'agent_type': 'agent',
            'settlement': 'monthly',
            'commission': self.commission_10.id,
            'email': 'agent1@test.com',
            'street': 'Avda Andalucia, 23',
            'phone': '958123456'})
        self.customer_01 = self.env['res.partner'].create({
            'name': 'Customer 01',
            'agent': True,
            'email': 'customer1@test.com',
            'street': 'Avda Andalucia, 23',
            'phone': '958123456',
            'agents': [(6, 0, [self.agent_01.id])]})
        self.pt_01 = self.env['product.template'].create({
            'name': 'Product 01',
            'type': 'consu'})
        self.pp_01 = self.env['product.product'].create({
            'product_tmpl_id': self.pt_01.id,
            'list_price': 100})
        self.order_01 = self.env['sale.order'].create({
            'partner_id': self.customer_01.id,
            'pricelist_id': self.ref('product.list0'),
            'date_order': fields.Date.today()})
        self.order_line_01 = self.env['sale.order.line'].create({
            'order_id': self.order_01.id,
            'name': self.pp_01.name_template,
            'product_id': self.pp_01.id,
            'product_uom_qty': 1,
            'price_unit': self.pp_01.list_price,
            'product_uom': self.ref('product.product_uom_unit'),
            'tax_id': [(6, 0, [self.taxs_21.id])]})
        self.sale_line_agent = self.env['sale.order.line.agent'].create({
            'sale_line': self.order_line_01.id,
            'agent': self.agent_01.id,
            'commission': self.agent_01.commission.id})

    def test_sale_commission_discount_agent_amounts(self):
        self.order_line_01.discount = 10.00
        self.assertEqual(self.order_line_01.agents[0].agent, self.agent_01)
        self.assertEqual(self.order_line_01.price_subtotal, 90)
        self.assertEqual(self.order_line_01.agents[0].amount, 9)
