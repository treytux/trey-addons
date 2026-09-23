###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from datetime import timedelta

from odoo import fields
from odoo.tests.common import TransactionCase


class TestWebsiteSaleProductSupplierinfoCustomer(TransactionCase):

    def setUp(self):
        super().setUp()
        self.company = self.env.company
        self.customer = self.env['res.partner'].create({
            'name': 'Test Website Customer',
            'email': 'test-website-customer@example.com',
        })
        self.portal_user = self.env['res.users'].with_context(
            no_reset_password=True
        ).create({
            'name': 'Test Website Customer User',
            'login': 'test-website-customer@example.com',
            'email': 'test-website-customer@example.com',
            'partner_id': self.customer.id,
            'groups_id': [(6, 0, [self.env.ref('base.group_portal').id])],
        })
        self.pricelist = self.env['product.pricelist'].create({
            'name': 'Test Website Pricelist',
            'currency_id': self.company.currency_id.id,
            'company_id': self.company.id,
        })
        self.website = self.env['website'].create({
            'name': 'Test Website',
            'company_id': self.company.id,
            'user_id': self.env.user.id,
            'pricelist_ids': [(6, 0, [self.pricelist.id])],
        })
        self.product = self.env['product.template'].create({
            'name': 'Test Website Product',
            'list_price': 120.0,
            'sale_ok': True,
            'website_published': True,
            'company_id': self.company.id,
        })

    def _create_customerinfo(
            self, price, min_qty=1, product=None, date_start=False,
            date_end=False, discount=0):
        values = {
            'partner_id': self.customer.id,
            'product_tmpl_id': self.product.id,
            'price': price,
            'min_qty': min_qty,
            'date_start': date_start,
            'date_end': date_end,
        }
        if product:
            values['product_id'] = product.id
        customerinfo = self.env['product.customerinfo'].create(values)
        customerinfo.discount = discount
        return customerinfo

    def test_get_product_customerinfo_filters_customer_quantity_and_dates(self):
        today = fields.Date.context_today(self.product)
        valid_customerinfo = self._create_customerinfo(
            50.0, min_qty=1, date_start=today - timedelta(days=1),
            date_end=today + timedelta(days=1))
        self._create_customerinfo(
            40.0, min_qty=10, date_start=today + timedelta(days=1))
        self._create_customerinfo(
            30.0, min_qty=1,
            date_end=today - timedelta(days=1))
        customerinfo = self.product.get_product_customerinfo(
            self.product.id, 1, self.customer,
            self.product.product_variant_id.id)
        self.assertEqual(customerinfo.price, 50.0)
        valid_customerinfo.unlink()
        customerinfo = self.product.get_product_customerinfo(
            self.product.id, 10, self.customer,
            self.product.product_variant_id.id)
        self.assertFalse(customerinfo)

    def test_get_product_customerinfo_prefers_variant(self):
        attribute = self.env['product.attribute'].create({
            'name': 'Test Attribute',
        })
        value_one = self.env['product.attribute.value'].create({
            'name': 'Test Value One',
            'attribute_id': attribute.id,
        })
        value_two = self.env['product.attribute.value'].create({
            'name': 'Test Value Two',
            'attribute_id': attribute.id,
        })
        self.env['product.template.attribute.line'].create({
            'product_tmpl_id': self.product.id,
            'attribute_id': attribute.id,
            'value_ids': [(6, 0, [value_one.id, value_two.id])],
        })
        variant = self.product.product_variant_ids[0]
        self._create_customerinfo(70.0)
        self._create_customerinfo(60.0, product=variant)
        customerinfo = self.product.get_product_customerinfo(
            self.product.id, 1, self.customer, variant.id)
        self.assertEqual(customerinfo.product_id, variant)
        self.assertEqual(customerinfo.price, 60.0)

    def test_cart_update_applies_customer_pricing(self):
        self._create_customerinfo(90.0, min_qty=1, discount=10.0)
        self._create_customerinfo(80.0, min_qty=2, discount=5.0)
        order = self.env['sale.order'].create({
            'partner_id': self.customer.id,
            'company_id': self.company.id,
            'pricelist_id': self.pricelist.id,
            'website_id': self.website.id,
        })
        result = order._cart_update(
            product_id=self.product.product_variant_id.id, line_id=False,
            add_qty=1)
        line = self.env['sale.order.line'].browse(result['line_id'])
        self.assertEqual(line.product_uom_qty, 1.0)
        self.assertEqual(line.price_unit, 90.0)
        self.assertEqual(line.discount, 10.0)
        order._cart_update(
            product_id=self.product.product_variant_id.id, line_id=line.id,
            set_qty=2)
        self.assertEqual(line.product_uom_qty, 2.0)
        self.assertEqual(line.price_unit, 80.0)
        self.assertEqual(line.discount, 5.0)

    def test_combination_info_applies_customer_price_and_discount(self):
        self._create_customerinfo(90.0, discount=10.0)
        product = self.product.with_user(self.portal_user).with_context(
            website_id=self.website.id)
        combination_info = product._get_combination_info(
            product_id=self.product.product_variant_id.id,
            add_qty=1, pricelist=self.pricelist)
        self.assertEqual(combination_info['price'], 81.0)
        self.assertEqual(combination_info['list_price'], 90.0)
        self.assertTrue(combination_info['has_discounted_price'])

    def test_combination_info_keeps_standard_price_without_customerinfo(self):
        product = self.product.with_user(self.portal_user).with_context(
            website_id=self.website.id)
        combination_info = product._get_combination_info(
            product_id=self.product.product_variant_id.id,
            add_qty=1, pricelist=self.pricelist)
        self.assertEqual(combination_info['price'], 120.0)
