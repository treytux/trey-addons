###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo.addons.woocommerce_connector.tests import test_common as common


class TestAutoUpload(common.TestCommon):

    def test_auto_upload_orm(self):
        if not self.ensure_woo():
            self.skipTest('WooCommerce server not available')
        self.reset_woo_data_test()
        self.website.woo_export_method = 'orm'
        self.assertEqual(self.product.woo_ids_get(), {})
        self.assertEqual(self.product.woo_get_id(), None)
        self.product.write({
            'default_code': 'SKU-FOR-FORCE-UPLOAD',
        })
        self.assertNotEqual(self.product.woo_get_id(), None)
        woo_products = self.product.woo_rpc_get()
        self.assertIn('SKU-FOR-FORCE-UPLOAD', [p['sku'] for p in woo_products])
        self.product.unlink()
        woo_products = self.product.woo_rpc_get()
        self.assertNotIn(
            'SKU-FOR-FORCE-UPLOAD', [p['sku'] for p in woo_products])
        product_obj = self.env['product.product'].with_context(
            website=self.website)
        products = product_obj.create({
            'type': 'product',
            'company_id': False,
            'default_code': 'SKU-FOR-UPLOAD-1',
            'name': '[OdooWooConn] ORM create 1',
            'standard_price': 10,
            'list_price': 100,
            'website_id': self.website.id,
            'website_published': True,
            'weight': 11.1,
        })
        products.product_tmpl_id.is_published = True
        woo_products = self.product.woo_rpc_get()
        self.assertIn('SKU-FOR-UPLOAD-1', [p['sku'] for p in woo_products])
        products |= product_obj.create({
            'type': 'product',
            'company_id': False,
            'default_code': 'SKU-FOR-UPLOAD-2',
            'name': '[OdooWooConn] ORM create 2',
            'standard_price': 20,
            'list_price': 200,
            'website_id': self.website.id,
            'website_published': True,
            'weight': 22.2,
        })
        products[1].product_tmpl_id.is_published = True
        woo_products = self.product.woo_rpc_get()
        self.assertIn('SKU-FOR-UPLOAD-2', [p['sku'] for p in woo_products])
        products.write({'weight': 99})
        woo_products = self.product.woo_rpc_get()
        weights = {p['sku']: p['weight'] for p in woo_products}
        self.assertEqual(weights[products[0].default_code], '99.0')
        self.assertEqual(weights[products[1].default_code], '99.0')
        products.unlink()
        woo_products = self.product.woo_rpc_get()
        self.assertNotIn('SKU-FOR-UPLOAD-1', [p['sku'] for p in woo_products])
        self.assertNotIn('SKU-FOR-UPLOAD-2', [p['sku'] for p in woo_products])

    def test_auto_upload_queue(self):
        if not self.ensure_woo():
            self.skipTest('WooCommerce server not available')
        self.reset_woo_data_test()
        self.website.woo_export_method = 'queue'
        job_obj = self.env['queue.job']
        jobs = job_obj.search([
            ('method_name', 'in', ['woo_rpc_upload_job', 'woo_rpc_delete_job']),
        ])
        self.assertEqual(len(jobs), 0)
        self.assertEqual(self.product.woo_ids_get(), {})
        self.assertEqual(self.product.woo_get_id(), None)
        self.product.write({
            'default_code': 'SKU-FOR-FORCE-UPLOAD',
        })
        jobs = job_obj.search([
            ('method_name', '=', 'woo_rpc_upload_job'),
        ])
        self.assertEqual(len(jobs), 1)
        self.product.woo_set_id(999)
        self.product.unlink()
        jobs = job_obj.search([
            ('method_name', '=', 'woo_rpc_delete_job'),
        ])
        self.assertEqual(len(jobs), 1)
        product_obj = self.env['product.product'].with_context(
            website=self.website)
        product_obj.create({
            'type': 'product',
            'company_id': False,
            'default_code': 'SKU-FOR-UPLOAD-1',
            'name': '[OdooWooConn] ORM create 1',
            'standard_price': 10,
            'list_price': 100,
            'website_id': self.website.id,
            'website_published': True,
            'is_published': True,
            'weight': 11.1,
        })
        jobs = job_obj.search([
            ('method_name', '=', 'woo_rpc_upload_job'),
        ])
        self.assertEqual(len(jobs), 2)

    def test_auto_upload_queue_remove_duplicate_requests(self):
        if not self.ensure_woo():
            self.skipTest('WooCommerce server not available')
        self.reset_woo_data_test()
        self.website.woo_export_method = 'queue'
        job_obj = self.env['queue.job']
        jobs = job_obj.search([
            ('method_name', 'in', ['woo_rpc_upload_job', 'woo_rpc_delete_job']),
        ])
        self.assertEqual(len(jobs), 0)
        self.assertEqual(self.product.woo_ids_get(), {})
        self.assertEqual(self.product.woo_get_id(), None)
        product = self.env['product.product'].with_context(
            website=self.website).create({
                'type': 'product',
                'company_id': False,
                'default_code': 'SKU-FOR-FORCE-UPLOAD-COPY',
                'name': '[OdooWooConn] Copy product',
                'list_price': 100,
                'website_id': self.website.id,
                'website_published': True,
                'is_published': True,
                'weight': 11.1,
            })
        self.assertFalse(product._context.get('ignore_woo_upload'))
        jobs = job_obj.search([
            ('method_name', '=', 'woo_rpc_upload_job'),
        ])
        self.assertEqual(len(jobs), 1)
        product.woo_set_id(999)
        product.write({'name': 'Other name'})
        jobs = job_obj.search([
            ('method_name', '=', 'woo_rpc_upload_job'),
        ])
        self.assertEqual(len(jobs), 2)
        product.unlink()
        jobs = job_obj.search([
            ('method_name', '=', 'woo_rpc_delete_job'),
        ])
        self.assertEqual(len(jobs), 1)
