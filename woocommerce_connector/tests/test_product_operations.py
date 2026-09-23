###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo.addons.woocommerce_connector.tests import test_common as common


class TestProductOperations(common.TestCommon):

    def test_product_endpoint_get(self):
        endpoint = self.product.woo_endpoint_get()
        self.assertEqual(endpoint, 'products')
        endpoint = self.product.woo_endpoint_get(woo_id=123)
        self.assertEqual(endpoint, 'products/123')

    def test_product_upload_dict_get(self):
        data = self.product.woo_upload_dict_get()
        self.assertTrue(data['sku'].startswith('ID'))
        self.assertEqual(data['name'], '[OdooWooConn] Service product')
        self.assertEqual(float(data['regular_price']), 100.0)
        self.assertEqual(data['weight'], '11.1')
        self.assertEqual(
            data['short_description'], 'A description sale of product.')

    def test_product_upload_dict_with_sku(self):
        self.product.default_code = 'TEST-SKU-001'
        data = self.product.woo_upload_dict_get()
        self.assertEqual(data['sku'], 'TEST-SKU-001')

    def test_product_upload_dict_update_fields(self):
        data = self.product.woo_upload_dict_get(update_fields=['name'])
        self.assertIn('name', data)
        data = self.product.woo_upload_dict_get(update_fields=['qty_available'])
        self.assertIn('stock_quantity', data)
        self.assertNotIn('name', data)

    def test_product_woo_sync_export_records_active(self):
        products = self.product.woo_sync_export_records(self.website)
        self.assertIn(self.product, products)
        self.product.active = False
        products = self.product.woo_sync_export_records(self.website)
        self.assertNotIn(self.product, products)

    def test_product_woo_sync_export_records_website(self):
        self.product.website_id = False
        products = self.product.woo_sync_export_records(self.website)
        self.assertIn(self.product, products)
        other_website = self.env['website'].create({
            'name': 'Other Website',
            'is_woo': False,
        })
        self.product.website_id = other_website.id
        products = self.product.woo_sync_export_records(self.website)
        self.assertNotIn(self.product, products)


class TestProductCategoryOperations(common.TestCommon):

    def test_category_endpoint_get(self):
        endpoint = self.categ.woo_endpoint_get()
        self.assertEqual(endpoint, 'products/categories')
        endpoint = self.categ.woo_endpoint_get(woo_id=456)
        self.assertEqual(endpoint, 'products/categories/456')

    def test_category_upload_dict_get(self):
        if not self.ensure_woo():
            self.skipTest('WooCommerce server not available')
        data = self.categ.woo_upload_dict_get()
        self.assertEqual(data['name'], '[OdooWooConn] Parent category')
        self.assertFalse(data.get('parent'))
        data_child = self.categ_child.woo_upload_dict_get()
        self.assertEqual(data_child['name'], '[OdooWooConn] Child category')

    def test_category_hierarchy(self):
        self.assertEqual(self.categ_child.parent_id, self.categ)
        self.assertIn(self.categ_child, self.categ.child_id)

    def test_category_woo_sync_export_records(self):
        categs = self.categ.woo_sync_export_records(self.website)
        self.assertEqual(len(categs), 2)
        self.assertIn(self.categ, categs)
        self.assertIn(self.categ_child, categs)


class TestProductTagOperations(common.TestCommon):

    def test_tag_endpoint_get(self):
        endpoint = self.tag_a.woo_endpoint_get()
        self.assertEqual(endpoint, 'products/tags')
        endpoint = self.tag_a.woo_endpoint_get(woo_id=789)
        self.assertEqual(endpoint, 'products/tags/789')

    def test_tag_upload_dict_get(self):
        data = self.tag_a.woo_upload_dict_get()
        self.assertEqual(data['name'], '[OdooWooConn] Woo Tag A')

    def test_product_with_tags(self):
        self.product.tag_ids = [(6, 0, [self.tag_a.id, self.tag_b.id])]
        self.assertEqual(len(self.product.tag_ids), 2)
        self.assertIn(self.tag_a, self.product.tag_ids)
        self.assertIn(self.tag_b, self.product.tag_ids)


class TestWooMixinHelpers(common.TestCommon):

    def test_woo_format_str_to_date(self):
        date_str = '2024-01-15T10:30:00'
        result = self.product.woo_format_str_to_date(date_str)
        self.assertTrue(result)

    def test_woo_format_date_to_str(self):
        from datetime import datetime
        date = datetime(2024, 1, 15, 10, 30, 0)
        result = self.product.woo_format_date_to_str(date)
        self.assertTrue(result)
        self.assertIn('2024-01-15', result)


class TestWooIdsOperations(common.TestCommon):

    def test_woo_ids_get_empty(self):
        self.assertEqual(self.product.woo_ids_get(), {})
        self.assertEqual(self.categ.woo_ids_get(), {})
        self.assertEqual(self.tag_a.woo_ids_get(), {})

    def test_woo_set_and_get_id(self):
        self.assertIsNone(self.product.woo_get_id())
        self.product.woo_set_id(12345)
        self.assertEqual(self.product.woo_get_id(), 12345)
        self.product.woo_set_id(None)
        self.assertIsNone(self.product.woo_get_id())

    def test_woo_search_id(self):
        self.product.woo_set_id(54321)
        result = self.product.woo_search_id(54321)
        self.assertEqual(result, self.product)
        result = self.product.woo_search_id(99999)
        self.assertEqual(len(result), 0)

    def test_woo_ids_multiple_websites(self):
        website2 = self.env['website'].create({
            'name': 'WooCommerce 2',
            'is_woo': True,
            'woo_export_method': 'manual',
        })
        product_ctx1 = self.product.with_context(website=self.website)
        product_ctx2 = self.product.with_context(website=website2)
        product_ctx1.woo_set_id(111)
        product_ctx2.woo_set_id(222)
        self.assertEqual(product_ctx1.woo_get_id(), 111)
        self.assertEqual(product_ctx2.woo_get_id(), 222)
