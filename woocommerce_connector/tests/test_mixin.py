###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
import requests
from odoo.addons.woocommerce_connector.models import website_woo_mixin as mixin
from odoo.addons.woocommerce_connector.tests import test_common as common
from odoo.exceptions import ValidationError


class TestMixin(common.TestCommon):

    def test_check_url(self):
        def check_connection(website, path=''):
            url = '%s/wc-api/v3/%s' % (self.website.woo_url, path)
            res = requests.get(url, timeout=website.woo_timeout)
            if res.status_code != 200:
                raise ValidationError(
                    'URL %s with status code %s' % (url, res.status_code))
            return True

        if not self.website.woo_consumer_key:
            self.skipTest('Without WooCommerce credentials')
        self.assertTrue(check_connection(self.website))
        with self.assertRaises(ValidationError):
            check_connection(self.website, '/this-url-not-exists')
        self.website.woo_url = 'http://domain.not.exists:6666'
        with self.assertRaises(requests.ConnectionError):
            check_connection(self.website, '/this-url-not-exists')

    def test_website_get_and_set_id(self):
        self.assertEqual(self.categ.woo_ids_get(), {})
        self.assertEqual(self.categ.woo_get_id(), None)
        self.categ.woo_set_id(5)
        self.assertEqual(self.categ.woo_get_id(), 5)
        self.categ.woo_set_id(None)
        self.assertEqual(self.categ.woo_get_id(), None)

    def test_website_call(self):
        if not self.website.woo_consumer_key:
            self.skipTest('Without WooCommerce credentials')
        categs = self.categ.woo_rpc_get()
        self.assertTrue(categs)

    def test_notify_errors(self):
        if not self.website.woo_consumer_key:
            self.skipTest('Without WooCommerce credentials')
        self.reset_woo_data_test_categ()
        messages_len = len(self.team.message_ids)
        self.categ.woo_rpc_upload()
        woo_categ_id = self.categ.woo_get_id()
        self.categ.woo_set_id(None)
        with self.assertRaises(mixin.WooError):
            self.categ.woo_rpc_upload()
        self.categ.woo_set_id(woo_categ_id)
        self.categ.woo_rpc_delete()
        self.categ.woo_post_error('[OdooWooConn] error')
        self.assertEqual(messages_len + 1, len(self.team.message_ids))
        self.assertIn(
            'This error is referenced with', self.team.message_ids[0].body)

    def test_product_public_category(self):
        if not self.website.woo_consumer_key:
            self.skipTest('Without WooCommerce credentials')
        self.reset_woo_data_test_categ()
        self.assertEqual(self.categ.woo_get_id(), None)
        self.categ.woo_rpc_upload()
        self.assertTrue(isinstance(self.categ.woo_get_id(), int))
        categs = self.categ.woo_rpc_get()
        self.assertEqual(self.categ.woo_get_id(), categs[0]['id'])
        self.assertEqual(
            len([c for c in categs if c['name'].startswith('[OdooWooConn]')]),
            1)
        self.categ.woo_rpc_delete()
        self.assertEqual(self.categ.woo_get_id(), None)
        categs = self.categ.woo_rpc_get()
        self.assertEqual(
            len([c for c in categs if c['name'].startswith('[OdooWooConn]')]),
            0)
        self.categ_child.woo_rpc_upload()
        self.assertTrue(self.categ_child.woo_get_id())
        self.assertTrue(self.categ.woo_get_id())
        self.categ_child.parent_id.woo_rpc_delete()
        self.categ_child.woo_rpc_delete()
        self.assertFalse(self.categ_child.woo_get_id())
        self.assertFalse(self.categ.woo_get_id())

    def test_product_product_upsell(self):
        if not self.website.woo_consumer_key:
            self.skipTest('Without WooCommerce credentials')
        self.reset_woo_data_test()
        public_categ_obj = self.env['product.public.category'].with_context(
            website=self.website)
        categ_upsell_child = public_categ_obj.create({
            'website_id': self.website.id,
            'name': '[OdooWooConn] Upsell Child category',
            'parent_id': self.categ.id,
        })
        tag_obj = self.env['product.template.tag'].with_context(
            website=self.website)
        tag_upsell = tag_obj.create({
            'name': '[OdooWooConn] Woo Tag Upsell',
        })
        product_obj = self.env['product.product'].with_context(
            website=self.website)
        upsell_product = product_obj.create({
            'type': 'product',
            'company_id': False,
            'name': '[OdooWooConn] Upsell product',
            'standard_price': 10,
            'list_price': 100,
            'website_id': self.website.id,
            'website_published': True,
            'weight': 11.1,
        })
        cross_product = product_obj.create({
            'type': 'product',
            'company_id': False,
            'name': '[OdooWooConn] Cross product',
            'standard_price': 10,
            'list_price': 100,
            'website_id': self.website.id,
            'website_published': True,
            'weight': 11.1,
            'public_categ_ids': [(6, 0, categ_upsell_child.ids)],
            'tag_ids': [(6, 0, tag_upsell.ids)],
        })
        self.product.write({
            'alternative_product_ids': [
                (6, 0, upsell_product.product_tmpl_id.ids)],
            'accessory_product_ids': [
                (6, 0, cross_product.ids)],
        })
        self.product.woo_rpc_upload()
        self.assertTrue(isinstance(categ_upsell_child.woo_get_id(), int))
        self.assertTrue(
            isinstance(categ_upsell_child.parent_id.woo_get_id(), int))
        self.assertTrue(isinstance(tag_upsell.woo_get_id(), int))
        self.assertTrue(isinstance(upsell_product.woo_get_id(), int))
        self.assertTrue(isinstance(cross_product.woo_get_id(), int))
        tag_upsell.woo_rpc_delete()
        upsell_product.woo_rpc_delete()
        cross_product.woo_rpc_delete()
        categ_upsell_child.woo_rpc_delete()
        categ_upsell_child.parent_id.woo_rpc_delete()
        self.product.woo_rpc_delete()

    def test_woo_product_categ(self):
        if not self.website.woo_consumer_key:
            self.skipTest('Without WooCommerce credentials')
        self.reset_woo_data_test()
        self.assertEquals(self.product.woo_get_id(), None)
        self.assertEquals(self.categ.woo_get_id(), None)
        self.assertEquals(self.categ_child.woo_get_id(), None)
        self.product.public_categ_ids = [(6, 0, [self.categ_child.id])]
        self.product.woo_rpc_upload()
        self.assertTrue(isinstance(self.product.woo_get_id(), int))
        self.assertTrue(isinstance(self.categ.woo_get_id(), int))
        self.assertTrue(isinstance(self.categ_child.woo_get_id(), int))
        self.product.woo_rpc_delete()
        self.categ.woo_rpc_delete()
        self.categ_child.woo_rpc_delete()
        self.assertEquals(self.product.woo_get_id(), None)
        self.assertEquals(self.categ.woo_get_id(), None)
        self.assertEquals(self.categ_child.woo_get_id(), None)

    def test_woo_product_price(self):
        data = self.product.woo_upload_dict_get()
        self.assertTrue(data['sku'].startswith('ID'))
        self.product.default_code = 'TEST-PRODUCT-WOO'
        data = self.product.woo_upload_dict_get()
        self.assertEqual(data['sku'], 'TEST-PRODUCT-WOO')
        self.assertEqual(float(data['regular_price']), 100.)
        pricelist = self.env['product.pricelist'].create({
            'name': 'Test pricelist',
            'website_id': self.website.id,
            'item_ids': [
                (0, 0, {
                    'applied_on': '3_global',
                    'base': 'list_price',
                    'compute_price': 'fixed',
                    'fixed_price': 999.99,
                }),
            ],
        })
        self.env.user.partner_id.property_product_pricelist = pricelist.id
        data = self.product.woo_upload_dict_get()
        self.assertEqual(float(data['regular_price']), 999.99)

    def test_search_id(self):
        self.product.woo_set_id(111)
        self.assertEqual(self.product.woo_get_id(), 111)
        products = self.product.woo_search_id(111)
        self.assertEqual(products, self.product)
        products = self.product.woo_search_id(11)
        self.assertEquals(len(products), 0)
