###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo.tests import common


class TestProductCatalogLabel(common.TransactionCase):

    def setUp(self):
        super().setUp()
        self.partner = self.env['res.partner'].create({
            'name': 'Test partner',
            'is_company': True,
        })
        self.catalog_01 = self.env['product.catalog'].create({
            'name': 'Catalog test',
        })
        self.product_01 = self.env['product.product'].create({
            'type': 'service',
            'company_id': False,
            'name': 'Test product 1',
            'standard_price': 10,
            'default_code': '01-PROD',
            'list_price': 100,
        })

    def create_sale(self, partner):
        sale = self.env['sale.order'].create({
            'partner_id': partner.id,
            'order_line': [
                (0, 0, {
                    'product_id': self.product_01.id,
                    'price_unit': 20,
                    'product_uom_qty': 1,
                }),
            ],
        })
        return sale

    def test_product_catalog_sale_line_domain_01(self):
        self.assertFalse(self.env.user.catalog_ids)
        self.assertFalse(self.product_01.catalog_ids)
        self.assertEqual(self.catalog_01.product_count, 0)
        self.assertEqual(self.catalog_01.users_count, 0)
        sale = self.create_sale(self.partner)
        self.assertEqual(len(sale.order_line), 1)
        domain = sale.order_line._get_sale_line_domain()
        self.assertEqual(domain, [('sale_ok', '=', True)])
        products = self.env['product.product'].search(domain)
        self.assertIn(self.product_01.id, products.ids)

    def test_product_catalog_sale_line_domain_02(self):
        self.assertFalse(self.env.user.catalog_ids)
        self.product_01.write({
            'catalog_ids': [(6, 0, [self.catalog_01.id])],
        })
        self.assertTrue(self.product_01.catalog_ids)
        self.assertEqual(self.catalog_01.product_count, 1)
        self.assertEqual(self.catalog_01.users_count, 0)
        sale = self.create_sale(self.partner)
        self.assertEqual(len(sale.order_line), 1)
        domain = sale.order_line._get_sale_line_domain()
        self.assertEqual(domain, [('sale_ok', '=', True)])
        products = self.env['product.product'].search(domain)
        self.assertIn(self.product_01.id, products.ids)

    def test_product_catalog_sale_line_domain_03(self):
        self.env.user.write({
            'catalog_ids': [(6, 0, [self.catalog_01.id])],
        })
        self.assertTrue(self.env.user.catalog_ids)
        self.assertFalse(self.product_01.catalog_ids)
        sale = self.create_sale(self.partner)
        self.assertEqual(len(sale.order_line), 1)
        domain = sale.order_line._get_sale_line_domain()
        products = self.env['product.product'].search(domain)
        self.assertIn(self.product_01.id, products.ids)

    def test_product_catalog_sale_line_domain_04(self):
        self.env.user.write({
            'catalog_ids': [(6, 0, [self.catalog_01.id])],
        })
        self.product_01.write({
            'catalog_ids': [(6, 0, [self.catalog_01.id])],
        })
        self.assertEqual(len(self.env.user.catalog_ids), 1)
        self.assertEqual(len(self.product_01.catalog_ids), 1)
        self.assertEqual(
            self.env.user.catalog_ids[0], self.product_01.catalog_ids[0])
        sale = self.create_sale(self.partner)
        self.assertEqual(len(sale.order_line), 1)
        domain = sale.order_line._get_sale_line_domain()
        products = self.env['product.product'].search(domain)
        self.assertIn(self.product_01.id, products.ids)

    def test_product_catalog_sale_line_domain_05(self):
        self.env.user.write({
            'catalog_ids': [(6, 0, [self.catalog_01.id])],
        })
        catalog_02 = self.env['product.catalog'].create({
            'name': 'Catalog test 2',
        })
        self.product_01.write({
            'catalog_ids': [(6, 0, [catalog_02.id])],
        })
        self.assertEqual(len(self.env.user.catalog_ids), 1)
        self.assertEqual(len(self.product_01.catalog_ids), 1)
        self.assertNotEqual(
            self.env.user.catalog_ids[0], self.product_01.catalog_ids[0])
        sale = self.create_sale(self.partner)
        self.assertEqual(len(sale.order_line), 1)
        domain = sale.order_line._get_sale_line_domain()
        products = self.env['product.product'].search(domain)
        self.assertNotIn(self.product_01.id, products.ids)
