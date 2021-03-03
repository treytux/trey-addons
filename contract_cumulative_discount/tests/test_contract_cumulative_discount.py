###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import fields
from odoo.tests.common import TransactionCase


class TestContractCumulativeDiscount(TransactionCase):

    def setUp(self):
        super().setUp()
        self.contract_template = self.env['contract.template'].create({
            'name': 'Contract template',
            'contract_type': 'sale',
        })
        self.product = self.env['product.product'].create({
            'type': 'service',
            'company_id': False,
            'name': 'Service product',
            'standard_price': 10,
            'list_price': 100,
            'is_contract': True,
            'contract_template_id': self.contract_template.id,
        })
        self.partner = self.env['res.partner'].create({
            'name': 'Partner test',
        })

    def test_contract_line_without_discount(self):
        contract = self.env['contract.contract'].create({
            'name': 'Test contract',
            'partner_id': self.partner.id,
        })
        line_obj = self.env['contract.line']
        line = line_obj.new({
            'name': 'Test contract',
            'contract_id': contract.id,
            'product_id': self.product.id,
            'multiple_discount': False,
            'discount_name': False,
            'recurring_next_date': fields.Date.today(),
            'quantity': 1,
        })
        line._onchange_product_id()
        line.price_unit = 100
        line.multiple_discount = False
        line = line_obj.create(line_obj._convert_to_write(line._cache))
        self.assertEquals(line.price_subtotal, 100)
        contract.recurring_create_invoice()
        inv_line = self.env['account.invoice.line'].search([
            ('contract_line_id', 'in', line.ids),
        ])
        self.assertEquals(len(inv_line), 1)
        self.assertEquals(inv_line.multiple_discount, line.multiple_discount)
        self.assertEquals(inv_line.discount_name, line.discount_name)
        self.assertEquals(inv_line.price_subtotal, 100)

    def test_contract_line_discount(self):
        contract = self.env['contract.contract'].create({
            'name': 'Test contract',
            'partner_id': self.partner.id,
        })
        line_obj = self.env['contract.line']
        line = line_obj.new({
            'name': 'Test contract',
            'contract_id': contract.id,
            'product_id': self.product.id,
            'multiple_discount': '10+10',
            'discount_name': 'Two discount',
            'recurring_next_date': fields.Date.today(),
            'quantity': 1,
        })
        line._onchange_product_id()
        line.price_unit = 100
        line = line_obj.create(line_obj._convert_to_write(line._cache))
        self.assertEquals(line.price_subtotal, 81.)
        contract.recurring_create_invoice()
        inv_line = self.env['account.invoice.line'].search([
            ('contract_line_id', 'in', line.ids),
        ])
        self.assertEquals(len(inv_line), 1)
        self.assertEquals(inv_line.multiple_discount, line.multiple_discount)
        self.assertEquals(inv_line.discount_name, line.discount_name)
        self.assertEquals(inv_line.price_subtotal, 81.)

    def test_contract_line_discount_from_sale(self):
        sale = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'order_line': [
                (0, 0, {
                    'product_id': self.product.id,
                    'multiple_discount': '10+10',
                    'discount_name': 'Two discount',
                    'price_unit': 100,
                    'product_uom_qty': 1}),
            ]
        })
        sale.order_line[0].onchange_multiple_discount()
        self.assertEquals(sale.order_line[0].price_subtotal, 81.)
        sale.action_confirm()
        contract = sale.order_line.mapped('contract_id')
        self.assertEquals(len(contract), 1)
        line = contract.mapped('contract_line_ids')
        self.assertEquals(len(line), 1)
        self.assertEquals('10+10', sale.order_line[0].multiple_discount)
        self.assertEquals(
            line.multiple_discount, sale.order_line[0].multiple_discount)
        self.assertEquals(
            line.discount_name, sale.order_line[0].discount_name)

    def test_contract_line_onchange(self):
        contract = self.env['contract.contract'].create({
            'name': 'Test contract',
            'partner_id': self.partner.id,
        })
        line_obj = self.env['contract.line']
        line = line_obj.new({
            'name': 'Test contract',
            'contract_id': contract.id,
            'product_id': self.product.id,
            'multiple_discount': '10+10',
            'discount_name': 'Two discount',
            'recurring_next_date': fields.Date.today(),
            'price_unit': 100,
            'quantity': 1,
        })
        self.assertEquals(line.price_subtotal, 81.)
        line.multiple_discount = False
        self.assertEquals(line.price_subtotal, 100.)
        line.multiple_discount = '10+10'
        self.assertEquals(line.price_subtotal, 81.)
