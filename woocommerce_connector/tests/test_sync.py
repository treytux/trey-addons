###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo.addons.woocommerce_connector.tests import test_common as common


class TestSync(common.TestCommon):

    def test_woo_sync_import(self):
        if not self.ensure_woo():
            self.skipTest('WooCommerce server not available')
        self.reset_woo_data_test()
        wizard = self.env['woocommerce.sync'].create({
            'method': 'import',
        })
        self.assertEqual(wizard.website_id, self.website)
        wizard.action_count()
        self.assertEqual(wizard.import_product_count, 0)

    def test_woo_product_sync(self):
        if not self.ensure_woo():
            self.skipTest('WooCommerce server not available')
        self.reset_woo_data_test()
        products = self.product.woo_sync_export_records(self.website)
        if not products:
            products = self.product.woo_sync_export_records(
                self.website, products=self.product)
        self.assertIn(self.product, products)
        self.product.active = False
        products = self.product.woo_sync_export_records(self.website)
        self.assertNotIn(self.product, products)
        self.product.active = True
        self.product.website_published = False
        products = self.product.woo_sync_export_records(self.website)
        self.assertNotIn(self.product, products)
        self.product.website_published = True
        other_website = self.env.ref('website.website2')
        self.product.website_id = other_website.id
        products = self.product.woo_sync_export_records(self.website)
        self.assertNotIn(self.product, products)
        self.product.website_id = False
        products = self.product.woo_sync_export_records(self.website)
        self.assertIn(self.product, products)

    def test_woocommerce_upload_wizard(self):
        if not self.ensure_woo():
            self.skipTest('WooCommerce server not available')
        self.reset_woo_data_test()
        self.assertEqual(self.product.woo_get_id(), None)
        self.product.write({
            'public_categ_ids': [(6, 0, [self.categ.id])],
            'tag_ids': [(6, 0, [self.tag_a.id, self.tag_b.id])],
        })
        wizard_obj = self.env['woocommerce.sync'].with_context(
            active_model='product.product', active_ids=[self.product.id])
        wizard = wizard_obj.create({})
        self.assertTrue(wizard.website_id)
        wizard.with_context(debug=True).action_count()
        self.assertEqual(wizard.product_count, 1)
        self.assertEqual(wizard.public_category_count, 2)
        self.assertEqual(wizard.product_tag_count, 2)
        self.assertEqual(wizard.del_product_count, 0)
        self.assertEqual(wizard.del_public_category_count, 0)
        self.assertEqual(wizard.del_product_tag_count, 0)
        info_categs = self.env['product.public.category']._woo_sync_export_get(
            self.product)
        self.assertEqual(len(info_categs['delete']), 0)
        self.assertEqual(self.product.woo_get_id(), None)
        wizard.action_sync()
        self.assertTrue(isinstance(self.product.woo_get_id(), int))
        self.product.woo_rpc_delete()
        self.categ.woo_rpc_delete()
        self.tag_a.woo_rpc_delete()
        self.tag_b.woo_rpc_delete()

    def test_sync_tags(self):
        if not self.ensure_woo():
            self.skipTest('WooCommerce server not available')
        self.reset_woo_data_test()
        tag = self.tag_a.with_context(website=self.website)
        tag.woo_upload(self.website)
        woo_id = tag.woo_get_id()
        tag.woo_ids = False
        tag_obj = self.env['product.template.tag']
        tags = tag.woo_rpc_get()
        tag_obj.woo_sync_import(self.website, params={}, datas=tags)
        tag.woo_set_id(woo_id)
        tag.woo_rpc_delete()

    def test_sync_with_catalog(self):
        catalog = self.env['product.catalog'].create({
            'name': 'Test catalog',
        })
        self.website.woo_catalog_ids = [(6, 0, [catalog.id])]
        self.product.product_tmpl_id.catalog_ids = [(6, 0, [catalog.id])]
        products = self.product.woo_sync_export_records(self.website)
        self.assertEqual(len(products), 1)
        categs = self.categ.woo_sync_export_records(self.website)
        self.assertEqual(len(categs), 2)
