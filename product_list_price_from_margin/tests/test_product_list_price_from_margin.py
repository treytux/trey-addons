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
                'list_price': 0.,
            })
            template._compute_list_price()
            return template.list_price

        self.assertEquals(compute(0, 0), 0)
        self.assertEquals(compute(100, 0), 100)
        self.assertEquals(compute(100, 25), 133.33)
        self.assertEquals(compute(100, 20), 125)
        self.assertEquals(compute(100, 100), 1000000.0)
        self.assertEquals(compute(100, 200), 1000000.0)
        self.assertEquals(compute(100, -100), 50)

    def test_margin(self):
        def compute(standard, price):
            product = self.env['product.template'].new({
                'name': 'Test Product',
                'standard_price': standard,
                'list_price': price,
            })
            product.onchange_list_price()
            return round(product.margin, 2)

        self.assertEquals(compute(0, 0), 0)
        self.assertEquals(compute(100, 100), 0)
        self.assertEquals(compute(100, 133.33), 25)
        self.assertEquals(compute(100, 125), 20)
        self.assertEquals(compute(100, 1000000.0), 99.99)
        self.assertEquals(compute(100, 50), -100)
        self.assertEquals(compute(100, 0), 0)
        self.assertEquals(compute(100, 1), -9900)

    def test_product_template_margin_0(self):
        template = self.env['product.template'].create({
            'name': 'Test Product',
            'standard_price': 100,
            'margin': 0,
            'list_price': 100,
        })
        self.assertEquals(template.standard_price, 100)
        self.assertEquals(template.margin, 0)
        self.assertEquals(template.list_price, 100)
        self.assertEquals(template.product_variant_ids.lst_price, 100)
        template.onchange_list_price()
        self.assertEquals(template.standard_price, 100)
        self.assertEquals(template.margin, 0)
        self.assertEquals(template.list_price, 100)
        self.assertEquals(template.product_variant_ids.lst_price, 100)

    def test_product_product_margin_0(self):
        product = self.env['product.product'].create({
            'name': 'Test Product',
            'standard_price': 100,
            'margin': 0,
            'lst_price': 100,
        })
        product._compute_product_lst_price()
        self.assertEquals(product.standard_price, 100)
        self.assertEquals(product.margin, 0)
        self.assertEquals(product.list_price, 100)
        self.assertEquals(product.lst_price, 100)
        product.onchange_lst_price()
        self.assertEquals(product.standard_price, 100)
        self.assertEquals(product.margin, 0)
        self.assertEquals(product.lst_price, 100)

    def test_product_template(self):
        product = self.env['product.template'].new({
            'name': 'Test Product',
            'standard_price': 0,
            'list_price': 11.11,
        })
        self.assertEquals(product.list_price, 11.11)
        product.onchange_list_price()
        self.assertEquals(product.list_price, 11.11)

    def test_product_product(self):
        product = self.env['product.product'].new({
            'name': 'Test Product',
            'standard_price': 0,
            'list_price': 11.11,
        })
        self.assertEquals(product.list_price, 11.11)
        product.onchange_lst_price()
        self.assertEquals(product.list_price, 11.11)
        product = product.create(product._convert_to_write(product._cache))
        template = product.product_tmpl_id
        self.assertEquals(len(template.product_variant_ids), 1)
        self.assertEquals(template.list_price, product.lst_price)
        template.list_price = 100
        self.assertEquals(template.list_price, 100)
        self.assertEquals(product.lst_price, 100)
        product.lst_price = 200
        self.assertEquals(template.list_price, 200)
        self.assertEquals(product.lst_price, 200)

    def test_margin_change(self):
        template = self.env['product.template'].create({
            'name': 'Test Product',
            'standard_price': 0,
            'list_price': 11.11,
            'margin': 10,
        })
        self.assertEquals(template.margin, 10)
        self.assertEquals(template.product_variant_ids.margin, 10)
        template.margin = 20
        self.assertEquals(template.margin, 20)
        self.assertEquals(template.product_variant_ids.margin, 20)
        template = self.env['product.template'].create({
            'name': 'Test Product',
            'standard_price': 100,
            'list_price': 125,
            'margin': 20,
        })
        self.assertEquals(template.standard_price, 100)
        self.assertEquals(template.list_price, 125)
        self.assertEquals(template.margin, 20)
        self.assertEquals(template.product_variant_ids.margin, 20)
        product = self.env['product.product'].create({
            'name': 'Test Product',
            'standard_price': 0,
            'list_price': 11.11,
            'margin': 10,
        })
        self.assertEquals(product.margin, 10)
        self.assertEquals(product.product_tmpl_id.margin, 10)
        product.margin = 20
        self.assertEquals(product.margin, 20)
        self.assertEquals(product.product_tmpl_id.margin, 20)

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
            'standard_price': 100.00,
            'list_price': 101,
            'margin': 20,
            'attribute_line_ids': [
                (0, 0, {
                    'attribute_id': attr.id,
                    'value_ids': [(6, 0, attr.value_ids.ids)],
                }),
            ]
        })
        self.assertEquals(len(template.product_variant_ids), 3)
        self.assertEquals(
            sum(template.product_variant_ids.mapped('lst_price')), 0)
        self.assertEquals(template.margin, 0)
        product_0 = template.product_variant_ids[0]
        product_1 = template.product_variant_ids[1]
        self.assertEquals(product_0.lst_price, 0)
        product_1.write(dict(lst_price=125, standard_price=100))
        self.assertEquals(product_1.lst_price, 125)
        self.assertEquals(product_1.margin, 20)
        self.assertEquals(product_1.standard_price, 100)
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
        partner = self.env['res.partner'].create({
            'name': 'Partner test',
            'property_product_pricelist': pricelist.id,
        })
        final_price, rule_id = pricelist.get_product_price_rule(
            product_1, 1.0, partner.id,
        )
        self.assertEquals(final_price, 125)
        self.assertEquals(product_0.lst_price, 0)
        self.assertEquals(product_1.lst_price, 125)
        final_price, rule_id = pricelist.get_product_price_rule(
            product_0, 1.0, partner.id,
        )
        self.assertEquals(final_price, 0)
        product_0.write(dict(lst_price=200, standard_price=100))
        final_price, rule_id = pricelist.get_product_price_rule(
            product_0, 1.0, partner.id,
        )
        self.assertEquals(final_price, 200)

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
            'standard_price': 100.00,
            'list_price': 101,
            'margin': 50,
            'attribute_line_ids': [
                (0, 0, {
                    'attribute_id': attr.id,
                    'value_ids': [(6, 0, attr.value_ids.ids)],
                }),
            ]
        })
        self.assertEquals(len(template.product_variant_ids), 3)
        self.assertEquals(
            sum(template.product_variant_ids.mapped('lst_price')), 0)
        product_0 = template.product_variant_ids[0]
        product_0.write(dict(lst_price=125, standard_price=100))
        self.assertEquals(product_0.margin, 20)

        def price_get(product):
            return product.price_compute('variant_lst_price')[product.id]

        self.assertEquals(price_get(product_0), 125)
        product_1 = template.product_variant_ids[1]
        product_1.write(dict(lst_price=150))
        self.assertEquals(price_get(product_1), 150)
