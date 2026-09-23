###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo.tests.common import TransactionCase


class TestProductListPriceFromMargin(TransactionCase):

    def test_list_price(self):
        def compute(standard, margin):
            template = self.env['product.template'].create({
                'name': 'Test Product',
                'standard_price': standard,
                'margin': margin,
                'list_price': 0,
            })
            template._compute_list_price()
            return template.list_price
        self.assertEqual(compute(0, 0), 0)
        self.assertEqual(compute(100, 0), 100)
        self.assertEqual(compute(100, 25), 133.33)
        self.assertEqual(compute(100, 20), 125)
        self.assertEqual(compute(100, 100), 1000000)
        self.assertEqual(compute(100, 200), 1000000)
        self.assertEqual(compute(100, -100), 50)

    def test_margin(self):
        def compute(standard, price):
            product = self.env['product.template'].new({
                'name': 'Test Product',
                'standard_price': standard,
                'list_price': price,
            })
            product.onchange_list_price()
            return round(product.margin, 2)
        self.assertEqual(compute(0, 0), 0)
        self.assertEqual(compute(100, 100), 0)
        self.assertEqual(compute(100, 133.33), 25)
        self.assertEqual(compute(100, 125), 20)
        self.assertEqual(compute(100, 1000000), 99.99)
        self.assertEqual(compute(100, 50), -100)
        self.assertEqual(compute(100, 0), 0)
        self.assertEqual(compute(100, 1), -9900)

    def test_product_template_margin_0(self):
        template = self.env['product.template'].create({
            'name': 'Test Product',
            'standard_price': 100,
            'margin': 0,
            'list_price': 100,
        })
        self.assertEqual(template.standard_price, 100)
        self.assertEqual(template.margin, 0)
        self.assertEqual(template.list_price, 100)
        self.assertEqual(template.product_variant_ids.lst_price, 100)
        template.onchange_list_price()
        self.assertEqual(template.standard_price, 100)
        self.assertEqual(template.margin, 0)
        self.assertEqual(template.list_price, 100)
        self.assertEqual(template.product_variant_ids.lst_price, 100)

    def test_product_product_margin_0(self):
        template = self.env['product.template'].create({
            'name': 'Test Product',
            'standard_price': 100,
            'margin': 0,
            'list_price': 100,
        })
        product = template.product_variant_ids
        product._compute_product_lst_price()
        self.assertEqual(product.standard_price, 100)
        self.assertEqual(product.margin, 0)
        self.assertEqual(product.list_price, 100)
        self.assertEqual(product.lst_price, 100)
        product.onchange_lst_price()
        self.assertEqual(product.standard_price, 100)
        self.assertEqual(product.margin, 0)
        self.assertEqual(product.lst_price, 100)

    def test_product_template(self):
        product = self.env['product.template'].new({
            'name': 'Test Product',
            'standard_price': 0,
            'list_price': 11.11,
        })
        self.assertEqual(product.list_price, 11.11)
        product.onchange_list_price()
        self.assertEqual(product.list_price, 11.11)

    def test_product_product(self):
        product = self.env['product.product'].new({
            'name': 'Test Product',
            'standard_price': 0,
            'list_price': 11.11,
        })
        self.assertEqual(product.list_price, 11.11)
        product.onchange_lst_price()
        self.assertEqual(product.list_price, 11.11)
        product = product.create(product._convert_to_write(product._cache))
        template = product.product_tmpl_id
        self.assertEqual(len(template.product_variant_ids), 1)
        self.assertEqual(template.list_price, product.lst_price)
        template.list_price = 100
        self.assertEqual(template.list_price, 100)
        self.assertEqual(product.lst_price, 100)
        product.lst_price = 200
        self.assertEqual(template.list_price, 200)
        self.assertEqual(product.lst_price, 200)

    def test_margin_change(self):
        template = self.env['product.template'].create({
            'name': 'Test Product',
            'standard_price': 0,
            'list_price': 11.11,
            'margin': 10,
        })
        self.assertEqual(template.margin, 10)
        self.assertEqual(template.product_variant_ids.margin, 10)
        template.margin = 20
        self.assertEqual(template.margin, 20)
        self.assertEqual(template.product_variant_ids.margin, 20)
        template = self.env['product.template'].create({
            'name': 'Test Product',
            'standard_price': 100,
            'list_price': 125,
            'margin': 20,
        })
        self.assertEqual(template.standard_price, 100)
        self.assertEqual(template.list_price, 125)
        self.assertEqual(template.margin, 20)
        self.assertEqual(template.product_variant_ids.margin, 20)
        product = self.env['product.product'].create({
            'name': 'Test Product',
            'standard_price': 0,
            'list_price': 11.11,
            'margin': 10,
        })
        self.assertEqual(product.margin, 10)
        self.assertEqual(product.product_tmpl_id.margin, 10)
        product.margin = 20
        self.assertEqual(product.margin, 20)
        self.assertEqual(product.product_tmpl_id.margin, 20)

    def test_batch_create_with_margins(self):
        templates = self.env['product.template'].create([
            {
                'name': 'Test Product 10',
                'standard_price': 100,
                'margin': 10,
            },
            {
                'name': 'Test Product 20',
                'standard_price': 100,
                'margin': 20,
            },
        ])
        self.assertEqual(templates.mapped('margin'), [10, 20])
        self.assertEqual(
            templates.mapped('product_variant_ids.margin'), [10, 20])

    def test_margin_with_pricelist(self):
        attr = self.env['product.attribute'].create({
            'name': 'Attribute test',
        })
        for value in ['A', 'B', 'C']:
            self.env['product.attribute.value'].create({
                'attribute_id': attr.id,
                'name': value,
            })
        template = self.env['product.template'].create({
            'name': 'Test Purchase Product',
            'purchase_method': 'purchase',
            'type': 'product',
            'standard_price': 100,
            'list_price': 101,
            'margin': 20,
            'attribute_line_ids': [
                (0, 0, {
                    'attribute_id': attr.id,
                    'value_ids': [(6, 0, attr.value_ids.ids)],
                }),
            ],
        })
        self.assertEqual(len(template.product_variant_ids), 3)
        self.assertEqual(
            sum(template.product_variant_ids.mapped('lst_price')), 0)
        self.assertEqual(template.margin, 0)
        product_0 = template.product_variant_ids[0]
        product_1 = template.product_variant_ids[1]
        self.assertEqual(product_0.margin, 20)
        self.assertEqual(product_0.lst_price, 0)
        self.assertEqual(product_1.margin, 20)
        product_1.write(dict(lst_price=125, standard_price=100))
        self.assertEqual(product_1.lst_price, 125)
        self.assertEqual(product_1.margin, 20)
        self.assertEqual(product_1.standard_price, 100)
        pricelist = self.env['product.pricelist'].create({
            'name': 'Test Margin Pricelist',
            'item_ids': [
                (0, 0, {
                    'compute_price': 'formula',
                    'base': 'variant_lst_price',
                    'price_discount': 0,
                }),
            ],
        })
        final_price = pricelist._get_product_price(
            product_1, 1.0, date='2026-01-01')
        self.assertEqual(final_price, 125)
        self.assertEqual(product_0.lst_price, 0)
        self.assertEqual(product_1.lst_price, 125)
        final_price = pricelist._get_product_price(
            product_0, 1.0, date='2026-01-01')
        self.assertEqual(final_price, 0)
        product_0.write(dict(lst_price=200, standard_price=100))
        final_price = pricelist._get_product_price(
            product_0, 1.0, date='2026-01-01')
        self.assertEqual(final_price, 200)

    def test_product_variants_list_price(self):
        attr = self.env['product.attribute'].create({
            'name': 'Attribute test',
        })
        for value in ['A', 'B', 'C']:
            self.env['product.attribute.value'].create({
                'attribute_id': attr.id,
                'name': value,
            })
        template = self.env['product.template'].create({
            'name': 'Test Purchase Product',
            'purchase_method': 'purchase',
            'type': 'product',
            'standard_price': 100,
            'list_price': 101,
            'margin': 50,
            'attribute_line_ids': [
                (0, 0, {
                    'attribute_id': attr.id,
                    'value_ids': [(6, 0, attr.value_ids.ids)],
                }),
            ],
        })
        self.assertEqual(len(template.product_variant_ids), 3)
        self.assertEqual(
            sum(template.product_variant_ids.mapped('lst_price')), 0)
        product_0 = template.product_variant_ids[0]
        self.assertEqual(product_0.margin, 50)
        product_0.write(dict(lst_price=125, standard_price=100))
        self.assertEqual(product_0.margin, 20)

        def price_get(product):
            return product.price_compute('variant_lst_price')[product.id]
        self.assertEqual(price_get(product_0), 125)
        product_1 = template.product_variant_ids[1]
        self.assertEqual(product_1.margin, 50)
        product_1.write(dict(lst_price=150))
        self.assertEqual(price_get(product_1), 150)

    def test_margin_change_based_standard_price(self):
        template = self.env['product.template'].create({
            'name': 'Test Product',
            'standard_price': 10,
            'margin': 25,
        })
        product = template.product_variant_ids
        self.assertEqual(template.margin, 25)
        self.assertEqual(template.list_price, 13.33)
        self.assertEqual(product.margin, 25)
        self.assertEqual(product.list_price, 13.33)
        template.margin = 50
        self.assertEqual(template.margin, 50)
        self.assertEqual(template.list_price, 20)
        self.assertEqual(product.margin, 50)
        self.assertEqual(product.list_price, 20)
