###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo.exceptions import ValidationError
from odoo.tests.common import TransactionCase


class TestSaleOrderNameUnique(TransactionCase):

    def setUp(self):
        super().setUp()
        self.product = self.env['product.product'].create({
            'type': 'service',
            'company_id': False,
            'name': 'Product test',
            'standard_price': 10,
            'list_price': 100,
        })
        self.partner = self.env['res.partner'].create({
            'name': 'Test partner 1',
        })

    def test_duplicated_name_same_company(self):
        self.env['sale.order'].create({
            'name': 'SO467',
            'partner_id': self.partner.id,
            'order_line': [
                (0, 0, {
                    'product_id': self.product.id,
                    'price_unit': 10,
                    'product_uom_qty': 1,
                }),
            ],
        })
        with self.assertRaises(ValidationError) as result:
            self.env['sale.order'].create({
                'name': 'SO467',
                'partner_id': self.partner.id,
                'order_line': [
                    (0, 0, {
                        'product_id': self.product.id,
                        'price_unit': 7,
                        'product_uom_qty': 2,
                    }),
                ],
            })
        self.assertEqual(
            result.exception.name,
            'The order with reference SO467 already exists')

    def test_duplicated_name_not_same_company(self):
        sale_order = self.env['sale.order'].create({
            'name': 'SO764',
            'partner_id': self.partner.id,
            'order_line': [
                (0, 0, {
                    'product_id': self.product.id,
                    'price_unit': 6,
                    'product_uom_qty': 2,
                }),
            ],
        })
        company = self.env.ref('base.main_company')
        self.assertEqual(sale_order.company_id, company)
        company_2 = self.env['res.company'].create({
            'name': 'Company test 2'
        })
        self.env['sale.order'].create({
            'name': 'SO764',
            'partner_id': self.partner.id,
            'company_id': company_2.id,
            'order_line': [
                (0, 0, {
                    'product_id': self.product.id,
                    'price_unit': 2,
                    'product_uom_qty': 4,
                }),
            ],
        })

    def test_duplicate_sale_order(self):
        sale_order = self.env['sale.order'].create({
            'name': 'SO764',
            'partner_id': self.partner.id,
            'order_line': [
                (0, 0, {
                    'product_id': self.product.id,
                    'price_unit': 10,
                    'product_uom_qty': 1,
                }),
            ],
        })
        sale_order_copied = sale_order.copy()
        self.assertNotEqual(sale_order.name, sale_order_copied.name)
