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
        })
        old_company = self.env.user.company_id
        self.env.user.company_id = company.id
        coas = self.env['account.chart.template'].search([])
        coas.try_loading_for_current_company()
        self.env.user.company_id = old_company.id
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

    def create_product(self, unit, area, list_price=33.33):
        return self.env['product.product'].create({
            'type': 'service',
            'company_id': False,
            'unit_id': unit.id,
            'area_id': area.id,
            'name': 'Service product',
            'standard_price': round(list_price / 2),
            'list_price': list_price,
        })

    def test_sale(self):
        product = self.create_product(self.unit_1, self.area_1, 33.33)
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
        self.assertEquals(sale.state, 'draft')
        sale.action_confirm()
        self.assertEquals(sale.state, 'sale')
        self.assertEquals(sale.invoice_count, 0)
        sale.action_invoice_create()
        self.assertEquals(sale.invoice_count, 1)
        self.assertEquals(
            sale.invoice_ids[0].company_id, self.unit_1.company_id)

    def test_sale_two_invoices(self):
        product_1 = self.create_product(self.unit_1, self.area_1, 33.33)
        product_2 = self.create_product(self.unit_2, self.area_2, 33.33)
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
        sale.action_invoice_create()
        self.assertEquals(sale.invoice_count, 2)
        for inv in sale.invoice_ids:
            company = inv.mapped(
                'invoice_line_ids.product_id.unit_id.company_id')
            self.assertEquals(inv.company_id, company)
