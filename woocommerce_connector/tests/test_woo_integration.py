###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo.addons.woocommerce_connector.tests import test_common as common


class TestWooIntegration(common.TestCommon):
    """Integration tests that require a running WooCommerce Docker instance."""

    def test_woo_connection(self):
        """Test basic API connection to WooCommerce."""
        if not self.ensure_woo():
            self.skipTest('WooCommerce server not available')
        api = self.website.woo_api_get()
        self.assertTrue(api)
        response = api.get('products')
        self.assertIn('json', dir(response))

    def test_woo_rpc_get_products(self):
        """Test getting products from WooCommerce."""
        if not self.ensure_woo():
            self.skipTest('WooCommerce server not available')
        self.reset_woo_data_test_product()
        products = self.product.woo_rpc_get()
        self.assertIsInstance(products, list)

    def test_woo_rpc_get_categories(self):
        """Test getting categories from WooCommerce."""
        if not self.ensure_woo():
            self.skipTest('WooCommerce server not available')
        self.reset_woo_data_test_categ()
        categs = self.categ.woo_rpc_get()
        self.assertIsInstance(categs, list)

    def test_woo_rpc_get_tags(self):
        """Test getting tags from WooCommerce."""
        if not self.ensure_woo():
            self.skipTest('WooCommerce server not available')
        self.reset_woo_data_test_tag()
        tags = self.tag_a.woo_rpc_get()
        self.assertIsInstance(tags, list)

    def test_woo_upload_product(self):
        """Test uploading a product to WooCommerce."""
        if not self.ensure_woo():
            self.skipTest('WooCommerce server not available')
        self.reset_woo_data_test_product()
        self.assertIsNone(self.product.woo_get_id())
        self.product.woo_rpc_upload()
        woo_id = self.product.woo_get_id()
        self.assertTrue(isinstance(woo_id, int))
        self.product.woo_rpc_delete()
        self.assertIsNone(self.product.woo_get_id())

    def test_woo_upload_category(self):
        """Test uploading a category to WooCommerce."""
        if not self.ensure_woo():
            self.skipTest('WooCommerce server not available')
        self.reset_woo_data_test_categ()
        self.assertIsNone(self.categ.woo_get_id())
        self.categ.woo_rpc_upload()
        woo_id = self.categ.woo_get_id()
        self.assertTrue(isinstance(woo_id, int))
        self.categ.woo_rpc_delete()
        self.assertIsNone(self.categ.woo_get_id())

    def test_woo_upload_tag(self):
        """Test uploading a tag to WooCommerce."""
        if not self.ensure_woo():
            self.skipTest('WooCommerce server not available')
        self.reset_woo_data_test_tag()
        self.assertIsNone(self.tag_a.woo_get_id())
        self.tag_a.woo_rpc_upload()
        woo_id = self.tag_a.woo_get_id()
        self.assertTrue(isinstance(woo_id, int))
        self.tag_a.woo_rpc_delete()
        self.assertIsNone(self.tag_a.woo_get_id())

    def test_woo_upload_product_with_category(self):
        """Test uploading a product with category to WooCommerce."""
        if not self.ensure_woo():
            self.skipTest('WooCommerce server not available')
        self.reset_woo_data_test()
        self.product.public_categ_ids = [(6, 0, [self.categ.id])]
        self.product.woo_rpc_upload()
        self.assertTrue(isinstance(self.product.woo_get_id(), int))
        self.assertTrue(isinstance(self.categ.woo_get_id(), int))
        self.product.woo_rpc_delete()
        self.categ.woo_rpc_delete()

    def test_woo_upload_product_with_tags(self):
        """Test uploading a product with tags to WooCommerce."""
        if not self.ensure_woo():
            self.skipTest('WooCommerce server not available')
        self.reset_woo_data_test()
        self.product.tag_ids = [(6, 0, [self.tag_a.id, self.tag_b.id])]
        self.product.woo_rpc_upload()
        self.assertTrue(isinstance(self.product.woo_get_id(), int))
        self.assertTrue(isinstance(self.tag_a.woo_get_id(), int))
        self.assertTrue(isinstance(self.tag_b.woo_get_id(), int))
        self.product.woo_rpc_delete()
        self.tag_a.woo_rpc_delete()
        self.tag_b.woo_rpc_delete()

    def test_woo_update_product(self):
        """Test updating a product in WooCommerce."""
        if not self.ensure_woo():
            self.skipTest('WooCommerce server not available')
        self.reset_woo_data_test_product()
        self.product.woo_rpc_upload()
        woo_id = self.product.woo_get_id()
        self.assertTrue(isinstance(woo_id, int))
        self.product.name = '[OdooWooConn] Updated product name'
        self.product.woo_rpc_upload(update_fields=['name'])
        products = self.product.woo_rpc_get(woo_id=woo_id)
        self.assertEqual(products['name'], '[OdooWooConn] Updated product name')
        self.product.woo_rpc_delete()

    def test_woo_delete_product(self):
        """Test deleting a product from WooCommerce."""
        if not self.ensure_woo():
            self.skipTest('WooCommerce server not available')
        self.reset_woo_data_test_product()
        self.product.woo_rpc_upload()
        woo_id = self.product.woo_get_id()
        self.assertTrue(isinstance(woo_id, int))
        products_before = [
            p for p in self.product.woo_rpc_get()
            if p['name'].startswith('[OdooWooConn]')
        ]
        self.product.woo_rpc_delete()
        self.assertIsNone(self.product.woo_get_id())
        products_after = [
            p for p in self.product.woo_rpc_get()
            if p['name'].startswith('[OdooWooConn]')
        ]
        self.assertEqual(len(products_after), len(products_before) - 1)

    def test_woo_sync_import_taxes(self):
        """Test importing taxes from WooCommerce."""
        if not self.ensure_woo():
            self.skipTest('WooCommerce server not available')
        tax_map_obj = self.env['website.woo.mapp.tax'].with_context(
            website=self.website)
        taxes = tax_map_obj.woo_rpc_get()
        self.assertIsInstance(taxes, list)

    def test_woo_category_hierarchy_upload(self):
        """Test uploading category with parent-child relationship."""
        if not self.ensure_woo():
            self.skipTest('WooCommerce server not available')
        self.reset_woo_data_test_categ()
        self.categ_child.woo_rpc_upload()
        self.assertTrue(isinstance(self.categ_child.woo_get_id(), int))
        self.assertTrue(isinstance(self.categ.woo_get_id(), int))
        woo_child = self.categ_child.woo_rpc_get(
            woo_id=self.categ_child.woo_get_id())
        self.assertEqual(woo_child['parent'], self.categ.woo_get_id())
        self.categ_child.woo_rpc_delete()
        self.categ.woo_rpc_delete()
