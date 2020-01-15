###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo.tests.common import TransactionCase


class TestSale(TransactionCase):

    def setUp(self):
        super().setUp()
        company, unit, area, user = self.create_company('1')
        self.company_1 = company
        self.unit_1 = unit
        self.area_1 = area
        self.user_1 = user
        company, unit, area, user = self.create_company('2')
        self.company_2 = company
        self.unit_2 = unit
        self.area_2 = area
        self.customer = self.env['res.partner'].create({
            'company_id': False,
            'company_type': 'company',
            'customer': True,
            'supplier': False,
            'name': 'Client',
        })

    def create_company(self, key):
        company = self.env['res.company'].create({
            'name': 'Company %s' % key,
            'create_contract_at_sale_order_confirmation': True,
        })
        user = self.env['res.users'].create({
            'name': 'User %s' % key,
            'login': 'user_%s@test.com' % key,
            'company_ids': [(6, 0, [company.id])],
            'company_id': company.id,
        })
        unit = self.env['product.business.unit'].create({
            'name': 'Business unit %s' % key,
            'company_id': company.id,
        })
        area = self.env['product.business.area'].create({
            'name': 'Unit %s' % key,
            'unit_id': unit.id,
        })
        return company, unit, area, user

    def create_product_and_contract(self, unit, area, list_price=33.33):
        contract = self.env['contract.template'].create({
            'name': 'Contract template',
            'contract_type': 'sale',
            'company_id': unit.company_id.id,
            'area_id': area.id,
        })
        product = self.env['product.product'].create({
            'type': 'service',
            'company_id': False,
            'name': 'Contract product',
            'contract_template_id': contract.id,
            'is_contract': True,
            'standard_price': round(list_price / 2),
            'list_price': list_price,
        })
        return product

    def test_sale(self):
        product = self.create_product_and_contract(
            self.unit_1, self.area_1, 33.33)
        contract = product.contract_template_id
        sale = self.env['sale.order'].create({
            'partner_id': self.customer.id,
            'order_line': [
                (0, 0, {
                    'product_id': product.id,
                    'price_unit': 33.33,
                    'product_uom_qty': 1}),
            ]
        })
        self.assertTrue(sale.name)
        self.assertEquals(len(sale.order_line), 1)
        line = sale.order_line[0]
        self.assertTrue(line.is_contract)
        self.assertEquals(sale.state, 'draft')
        sale.action_confirm()
        self.assertEquals(sale.state, 'sale')
        self.assertEquals(sale.contract_count, 1)
        self.assertTrue(line.contract_id)
        self.assertEquals(line.contract_id.unit_id, contract.unit_id)
        self.assertEquals(line.contract_id.area_id, contract.area_id)

    def test_sale_two_contracts(self):
        product_1 = self.create_product_and_contract(
            self.unit_1, self.area_1, 33.33)
        product_2 = self.create_product_and_contract(
            self.unit_2, self.area_2, 33.33)
        sale = self.env['sale.order'].create({
            'partner_id': self.customer.id,
            'order_line': [
                (0, 0, {
                    'product_id': product_1.id,
                    'price_unit': 33.33,
                    'product_uom_qty': 1}),
                (0, 0, {
                    'product_id': product_2.id,
                    'price_unit': 33.33,
                    'product_uom_qty': 1}),
            ]
        })
        sale.action_confirm()
        self.assertEquals(sale.contract_count, 2)
        self.assertEquals(
            sale.order_line[0].contract_id.unit_id, product_1.unit_id)
        self.assertEquals(
            sale.order_line[0].contract_id.area_id, product_1.area_id)
        self.assertEquals(
            sale.order_line[0].contract_id.company_id,
            product_1.unit_id.company_id)
        self.assertEquals(
            sale.order_line[1].contract_id.unit_id, product_2.unit_id)
        self.assertEquals(
            sale.order_line[1].contract_id.area_id, product_2.area_id)
        self.assertEquals(
            sale.order_line[1].contract_id.company_id,
            product_2.unit_id.company_id)

    def test_sale_two_areas_same_unit(self):
        area_11 = self.env['product.business.area'].create({
            'name': 'Unit 11',
            'unit_id': self.unit_1.id,
        })
        product_1 = self.create_product_and_contract(
            self.unit_1, self.area_1, 33.33)
        product_2 = self.create_product_and_contract(
            self.unit_1, area_11, 33.33)
        product_2.contract_template_id = product_1.contract_template_id.id
        sale = self.env['sale.order'].create({
            'partner_id': self.customer.id,
            'order_line': [
                (0, 0, {
                    'product_id': product_1.id,
                    'price_unit': 33.33,
                    'product_uom_qty': 1}),
                (0, 0, {
                    'product_id': product_2.id,
                    'price_unit': 33.33,
                    'product_uom_qty': 1}),
            ]
        })
        sale.with_context(debug=True).action_confirm()
        self.assertEquals(sale.contract_count, 1)
