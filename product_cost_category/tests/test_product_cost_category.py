###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from datetime import datetime, timedelta

from odoo.exceptions import ValidationError
from odoo.tests.common import TransactionCase


class TestProductCostCategory(TransactionCase):
    def setUp(self):
        super().setUp()
        param = self.set_param('automatic')
        self.assertEquals(param, 'automatic')
        self.past_month = datetime.now() - timedelta(days=30)
        self.next_month = datetime.now() + timedelta(days=30)
        self.cost_category_price = self.env['product.cost.category'].create({
            'name': 'Product Cost Category',
            'date_start': self.past_month,
            'date_end': self.next_month,
            'item_ids': [
                (0, 0, {
                    'from_standard_price': 10,
                    'to_standard_price': 100,
                    'formula': 'standard_price / 2',
                }),
            ]
        })
        self.attr = self.env['product.attribute'].create({
            'name': 'Attribute test',
        })
        for value in ['White', 'Black']:
            self.env['product.attribute.value'].create({
                'attribute_id': self.attr.id,
                'name': value,
            })
        self.product_tmpl_variant = self.env['product.template'].create({
            'name': 'Test product Variant',
            'type': 'service',
            'lst_price': 10.0,
            'company_id': False,
            'default_code': 'T0001',
            'attribute_line_ids': [
                (0, 0, {
                    'attribute_id': self.attr.id,
                    'value_ids': [(6, 0, self.attr.value_ids.ids)],
                }),
            ],
        })
        self.product_tmpl = self.env['product.template'].create({
            'name': 'Test product 1',
            'type': 'service',
            'standard_price': 10.00,
            'company_id': False,
            'default_code': 'T0001',
        })
        self.partner = self.env['res.partner'].create({
            'name': 'Test partner',
        })

    def create_wizard(self, product_tmpl, category):
        wizard = self.env['recalculate.cost.category.price'].with_context({
            'active_model': 'product.template',
            'active_ids': product_tmpl.ids,
        })
        return wizard.create({'category_id': category.id})

    def set_param(self, param):
        self.env['ir.config_parameter'].set_param(
            'product_cost_category.cost_category_price_setting', param)
        value = self.env['ir.config_parameter'].get_param(
            'product_cost_category.cost_category_price_setting')
        self.assertEquals(value, param)
        return value

    def test_product_product_sale_order(self):
        param = self.set_param('automatic')
        self.assertEquals(param, 'automatic')
        pricelist = self.env['product.pricelist'].create({
            'name': 'Pricelist (based on cost_category_price)',
            'item_ids': [(0, 0, {
                'applied_on': '1_product',
                'product_tmpl_id': self.product_tmpl.id,
                'compute_price': 'formula',
                'base': 'cost_category_price',
                'price_discount': 50.0,
            })],
        })
        self.assertEquals(pricelist.item_ids.base, 'cost_category_price')
        sale = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'pricelist_id': pricelist.id,
        })
        self.assertEquals(self.product_tmpl.cost_category_price, 5)
        self.product_tmpl.standard_price = 100
        self.assertEquals(self.product_tmpl.cost_category_price, 50)
        line = self.env['sale.order.line'].create({
            'order_id': sale.id,
            'product_id': self.product_tmpl.product_variant_ids[0].id,
        })
        line.product_id_change()
        self.assertEquals(line.price_unit, 25)

    def test_product_variants_sale_order(self):
        self.set_param('automatic')
        pricelist = self.env['product.pricelist'].create({
            'name': 'Pricelist A (based on cost_category_price)',
            'item_ids': [(0, 0, {
                'applied_on': '1_product',
                'product_tmpl_id': self.product_tmpl_variant.id,
                'compute_price': 'formula',
                'base': 'cost_category_price',
                'price_discount': 50.0,
            })],
        })
        base = pricelist.item_ids.base
        self.assertEquals(base, 'cost_category_price')
        sale = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'pricelist_id': pricelist.id,
        })
        for variant in self.product_tmpl_variant.product_variant_ids:
            self.assertEquals(variant.cost_category_price, 0)
            variant.standard_price = 10
            self.assertEquals(variant.cost_category_price, 5)
        line = self.env['sale.order.line'].create({
            'order_id': sale.id,
            'product_id': self.product_tmpl_variant.product_variant_ids[0].id,
        })
        line.product_id_change()
        self.assertEquals(line.price_unit, 2.5)

    def test_cost_category_price_wizard(self):
        param = self.set_param('manual')
        self.assertEquals(param, 'manual')
        wizard = self.create_wizard(self.product_tmpl, self.cost_category_price)
        self.assertEquals(self.product_tmpl.cost_category_price, 5)
        wizard.recalculate_cost_category_price()
        self.assertEquals(self.product_tmpl.cost_category_price, 5)
        wizard = self.create_wizard(
            self.product_tmpl_variant, self.cost_category_price)
        for variant in self.product_tmpl_variant.product_variant_ids:
            self.assertEquals(variant.cost_category_price, 0)
            variant.standard_price = 10
        wizard.recalculate_cost_category_price()
        for variant in self.product_tmpl_variant.product_variant_ids:
            self.assertEquals(variant.cost_category_price, 5)

    def test_cost_category_price_automatic(self):
        self.set_param('automatic')
        for variant in self.product_tmpl_variant.product_variant_ids:
            self.assertEquals(variant.cost_category_price, 0)
            variant.standard_price = 10
            self.assertEquals(variant.cost_category_price, 5)
        self.assertEquals(self.product_tmpl.cost_category_price, 5)
        self.product_tmpl.standard_price = 100
        self.assertEquals(self.product_tmpl.cost_category_price, 50)

    def test_category_overload_date(self):
        with self.assertRaises(ValidationError) as result:
            self.env['product.cost.category'].create({
                'name': 'Product Cost Category 2',
                'date_start': self.past_month,
                'date_end': self.next_month,
                'item_ids': [
                    (0, 0, {
                        'from_standard_price': 10,
                        'to_standard_price': 100,
                        'formula': 'standard_price / 10',
                    }),
                ]
            })
        self.assertEqual(
            result.exception.name,
            'Cost Category OverLap with: Product Cost Category'
        )

    def test_category_item_standard_price_range(self):
        with self.assertRaises(ValidationError) as result:
            self.env['product.cost.category.item'].create({
                'category_id': self.cost_category_price.id,
                'from_standard_price': 0,
                'to_standard_price': 0,
                'formula': 'standard_price / 10',
            })
        self.assertEqual(
            result.exception.name,
            'From Standard Price and To Standard Price is zero'
        )
        with self.assertRaises(ValidationError) as result:
            self.env['product.cost.category.item'].create({
                'category_id': self.cost_category_price.id,
                'from_standard_price': 100,
                'to_standard_price': 50,
                'formula': 'standard_price / 10',
            })
        self.assertEqual(
            result.exception.name,
            'From Standard Price greater To Standard Price'
        )

    def test_category_item_standard_check_formula(self):
        with self.assertRaises(ValidationError) as result:
            self.env['product.cost.category.item'].create({
                'category_id': self.cost_category_price.id,
                'from_standard_price': 10,
                'to_standard_price': 20,
                'formula': 'standard_price / "5"',
            })
        self.assertIn(
            'Formula Error:unsupported operand', result.exception.name
        )
        with self.assertRaises(ValidationError) as result:
            self.env['product.cost.category.item'].create({
                'category_id': self.cost_category_price.id,
                'from_standard_price': 10,
                'to_standard_price': 20,
                'formula': 'standard_price / text',
            })
        self.assertIn(
            'Formula Error:name', result.exception.name
        )
