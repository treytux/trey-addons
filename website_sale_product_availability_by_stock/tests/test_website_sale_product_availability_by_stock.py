###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo.tests import common


class TestWebsiteSaleProductAvailabilityByStock(common.TransactionCase):

    def setUp(self):
        super().setUp()
        self.partner = self.env['res.partner'].create({
            'name': 'Partner test',
        })
        self.product_01 = self.env['product.product'].create({
            'type': 'product',
            'company_id': False,
            'name': 'Product test 1',
            'standard_price': 10,
            'list_price': 20,
            'website_published': False,
        })
        self.product_02 = self.env['product.product'].create({
            'type': 'product',
            'company_id': False,
            'name': 'Product test 2',
            'standard_price': 40,
            'list_price': 80,
            'website_published': False,
        })
        self.location = self.env.ref('stock.stock_location_stock')

    def create_inventory(self, product, location, qty):
        inventory = self.env['stock.inventory'].create({
            'name': 'Add products for tests',
            'filter': 'partial',
            'location_id': location.id,
            'exhausted': True,
        })
        inventory.action_start()
        inventory.line_ids.create({
            'inventory_id': inventory.id,
            'product_id': product.id,
            'product_qty': qty,
            'location_id': location.id,
        })
        inventory._action_done()
        self.assertEquals(
            product.with_context(location=location.id).qty_available, qty)

    def test_check_cron_post_products_on_website_no_stock(self):
        self.assertFalse(self.product_01.website_published)
        self.assertFalse(self.product_02.website_published)
        self.assertFalse(self.product_01.published_by_stock)
        self.assertFalse(self.product_02.published_by_stock)
        self.assertEquals(self.product_01.qty_available_real, 0)
        self.assertEquals(self.product_02.qty_available_real, 0)
        self.env['product.template'].cron_products_website()
        self.assertFalse(self.product_01.website_published)
        self.assertFalse(self.product_02.website_published)
        self.product_01.website_published = True
        self.product_02.website_published = True
        self.assertTrue(self.product_01.website_published)
        self.assertTrue(self.product_02.website_published)
        self.env['product.template'].cron_products_website()
        self.assertTrue(self.product_01.website_published)
        self.assertTrue(self.product_02.website_published)
        self.product_01.published_by_stock = True
        self.product_02.published_by_stock = True
        self.assertTrue(self.product_01.published_by_stock)
        self.assertTrue(self.product_02.published_by_stock)
        self.env['product.template'].cron_products_website()
        self.assertFalse(self.product_01.website_published)
        self.assertFalse(self.product_02.website_published)

    def test_check_cron_post_products_on_website_with_stock(self):
        self.create_inventory(self.product_01, self.location, 1)
        self.create_inventory(self.product_02, self.location, 1)
        self.assertEquals(self.product_01.qty_available_real, 1)
        self.assertEquals(self.product_02.qty_available_real, 1)
        self.assertFalse(self.product_01.website_published)
        self.assertFalse(self.product_01.website_published)
        self.assertFalse(self.product_01.published_by_stock)
        self.assertFalse(self.product_02.published_by_stock)
        self.env['product.template'].cron_products_website()
        self.assertFalse(self.product_01.website_published)
        self.assertFalse(self.product_02.website_published)
        self.product_01.website_published = True
        self.product_02.website_published = True
        self.assertTrue(self.product_01.website_published)
        self.assertTrue(self.product_02.website_published)
        self.env['product.template'].cron_products_website()
        self.assertTrue(self.product_01.website_published)
        self.assertTrue(self.product_02.website_published)
        self.product_01.website_published = False
        self.product_02.website_published = False
        self.assertFalse(self.product_01.website_published)
        self.assertFalse(self.product_02.website_published)
        self.product_01.published_by_stock = True
        self.product_02.published_by_stock = True
        self.assertTrue(self.product_01.published_by_stock)
        self.assertTrue(self.product_02.published_by_stock)
        self.env['product.template'].cron_products_website()
        self.assertTrue(self.product_01.website_published)
        self.assertTrue(self.product_02.website_published)

    def test_product_variants_qty_available_real(self):
        attr = self.env['product.attribute'].create({
            'name': 'Attribute test',
        })
        for value in ['A', 'B', 'C']:
            self.env['product.attribute.value'].create({
                'attribute_id': attr.id,
                'name': value,
            })
        product_tmpl = self.env['product.template'].create({
            'name': 'Test product template',
            'type': 'product',
            'standard_price': 10,
            'attribute_line_ids': [
                (0, 0, {
                    'attribute_id': attr.id,
                    'value_ids': [(6, 0, attr.value_ids.ids)],
                }),
            ],
        })
        self.assertEquals(len(product_tmpl.product_variant_ids), 3)
        quant_obj = self.env['stock.quant']
        qty_1 = 5
        quant_obj._update_available_quantity(
            product_tmpl.product_variant_ids[0], self.location, qty_1)
        qty_2 = 10
        quant_obj._update_available_quantity(
            product_tmpl.product_variant_ids[1], self.location, qty_2)
        qty_3 = 15
        quant_obj._update_available_quantity(
            product_tmpl.product_variant_ids[2], self.location, qty_3)
        total_qty = qty_1 + qty_2 + qty_3
        product_uom_qty = 3
        sale_01 = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'order_line': [
                (0, 0, {
                    'product_id': product_tmpl.product_variant_ids[0].id,
                    'price_unit': 100,
                    'product_uom_qty': product_uom_qty}),
                (0, 0, {
                    'product_id': product_tmpl.product_variant_ids[1].id,
                    'price_unit': 100,
                    'product_uom_qty': product_uom_qty}),
                (0, 0, {
                    'product_id': product_tmpl.product_variant_ids[2].id,
                    'price_unit': 100,
                    'product_uom_qty': product_uom_qty}),
            ],
        })
        self.assertEquals(product_tmpl.qty_available_real, total_qty)
        sale_01.action_confirm()
        self.assertEquals(
            product_tmpl.qty_available_real, total_qty - (product_uom_qty * 3))
        product_tmpl.published_by_stock = True
        self.assertTrue(product_tmpl.published_by_stock)
        self.env['product.template'].cron_products_website()
        self.assertTrue(product_tmpl.website_published)
        sale_02 = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'order_line': [
                (0, 0, {
                    'product_id': product_tmpl.product_variant_ids[0].id,
                    'price_unit': 100,
                    'product_uom_qty': 2}),
            ],
        })
        sale_02.action_confirm()
        self.assertEquals(product_tmpl.qty_available_real, 19)
        self.assertTrue(product_tmpl.published_by_stock)
        self.env['product.template'].cron_products_website()
        self.assertTrue(product_tmpl.website_published)
        sale_03 = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'order_line': [
                (0, 0, {
                    'product_id': product_tmpl.product_variant_ids[0].id,
                    'price_unit': 100,
                    'product_uom_qty': 7}),
                (0, 0, {
                    'product_id': product_tmpl.product_variant_ids[0].id,
                    'price_unit': 100,
                    'product_uom_qty': 12}),
            ],
        })
        sale_03.action_confirm()
        self.assertEquals(product_tmpl.qty_available_real, 0)
        self.assertTrue(product_tmpl.published_by_stock)
        self.env['product.template'].cron_products_website()
        self.assertFalse(product_tmpl.website_published)
