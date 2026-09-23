###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo.addons.woocommerce_connector.tests import test_common as common


class TestStock(common.TestCommon):

    def test_stock_sync_realtime_disabled(self):
        self.website.woo_sync_stock_realtime = False
        self.website.woo_export_method = 'manual'
        stock_move_obj = self.env['stock.move']
        websites = stock_move_obj.select_websites()
        self.assertNotIn(self.website, websites)

    def test_stock_sync_realtime_enabled(self):
        self.website.woo_sync_stock_realtime = True
        self.website.woo_export_method = 'orm'
        stock_move_obj = self.env['stock.move']
        websites = stock_move_obj.select_websites()
        self.assertIn(self.website, websites)

    def test_stock_sync_realtime_queue(self):
        self.website.woo_sync_stock_realtime = True
        self.website.woo_export_method = 'queue'
        stock_move_obj = self.env['stock.move']
        websites = stock_move_obj.select_websites()
        self.assertIn(self.website, websites)


class TestTaxMapping(common.TestCommon):

    def test_tax_mapping_create(self):
        tax_map = self.env['website.woo.mapp.tax'].create({
            'website_id': self.website.id,
            'name': 'IVA 21%',
            'woo_id': 1,
            'woo_rate': 21.0,
        })
        self.assertEqual(tax_map.name, 'IVA 21%')
        self.assertEqual(tax_map.woo_rate, 21.0)
        self.assertEqual(tax_map.woo_endpoint_get(), 'taxes')
        self.assertEqual(tax_map.woo_endpoint_get(woo_id=1), 'taxes/1')

    def test_tax_mapping_sync_import(self):
        tax_map_obj = self.env['website.woo.mapp.tax']
        data = {
            'id': 99,
            'name': '[OdooWooConn] EU VAT 21%',
            'rate': 21.0,
        }
        tax_map = tax_map_obj.woo_sync_import_record(self.website, data)
        self.assertTrue(tax_map)
        self.assertEqual(tax_map.name, '[OdooWooConn] EU VAT 21%')
        self.assertEqual(tax_map.woo_id, 99)
        self.assertEqual(tax_map.woo_rate, 21.0)
        data['name'] = '[OdooWooConn] EU VAT 21% Updated'
        result = tax_map_obj.woo_sync_import_record(self.website, data)
        self.assertFalse(result)
        tax_map.refresh()
        self.assertEqual(tax_map.name, '[OdooWooConn] EU VAT 21% Updated')


class TestWebsiteConfig(common.TestCommon):

    def test_website_is_woo(self):
        self.assertTrue(self.website.is_woo)
        website_non_woo = self.env['website'].create({
            'name': 'Non WooCommerce Website',
            'is_woo': False,
        })
        self.assertFalse(website_non_woo.is_woo)

    def test_website_woo_export_methods(self):
        self.website.woo_export_method = 'manual'
        self.assertEqual(self.website.woo_export_method, 'manual')
        self.website.woo_export_method = 'orm'
        self.assertEqual(self.website.woo_export_method, 'orm')
        self.website.woo_export_method = 'queue'
        self.assertEqual(self.website.woo_export_method, 'queue')

    def test_website_woo_api_credentials(self):
        self.assertTrue(self.website.woo_consumer_key)
        self.assertTrue(self.website.woo_consumer_secret)
        self.assertEqual(self.website.woo_version, 'wc/v3')
