###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
import base64
import os

from odoo.tests.common import HttpCase
from requests import ConnectionError as ReqConnectionError
from woocommerce import API as WooAPI

WOO_URL = os.environ.get('WOO_URL', 'http://localhost:8080')
WOO_CONSUMER_KEY = os.environ.get(
    'WOO_CONSUMER_KEY',
    'a934bb2ebab77dde29925b36ae98bb512666ab9989c62a24f24339bb324902d6')
WOO_CONSUMER_SECRET = os.environ.get(
    'WOO_CONSUMER_SECRET', 'cs_test123456789012345678901234567890123')


class TestCommon(HttpCase):

    def setUp(self):
        super().setUp()
        self.env['product.product'].search([]).write({
            'website_published': False,
        })
        self.pricelist = self.env['product.pricelist'].create({
            'name': 'Test pricelist woocommerce',
        })
        self.team = self.env['crm.team'].create({
            'name': 'WooCommerce team',
        })
        self.team.message_subscribe(partner_ids=[self.env.user.partner_id.id])
        self.website = self.env['website'].create({
            'name': 'WooCommerce',
            'is_woo': True,
            'woo_url': WOO_URL,
            'woo_version': 'wc/v3',
            'woo_consumer_key': WOO_CONSUMER_KEY,
            'woo_consumer_secret': WOO_CONSUMER_SECRET,
            'woo_export_method': 'manual',
            'pricelist_id': self.pricelist.id,
            'salesteam_id': self.team.id,
        })
        public_categ_obj = self.env['product.public.category'].with_context(
            website=self.website)
        self.categ = public_categ_obj.create({
            'website_id': self.website.id,
            'name': '[OdooWooConn] Parent category',
        })
        self.categ_child = public_categ_obj.create({
            'website_id': self.website.id,
            'name': '[OdooWooConn] Child category',
            'parent_id': self.categ.id,
        })
        tag_obj = self.env['product.template.tag'].with_context(
            website=self.website)
        self.tag_a = tag_obj.create({
            'name': '[OdooWooConn] Woo Tag A',
        })
        self.tag_b = tag_obj.create({
            'name': '[OdooWooConn] Woo Tag B',
        })
        fname = os.path.join(
            os.path.dirname(__file__), 'files', 'image_example.jpg')
        with open(fname, 'rb') as fp:
            image = base64.b64encode(fp.read())
        product_obj = self.env['product.product'].with_context(
            website=self.website)
        self.product = product_obj.create({
            'type': 'product',
            'company_id': False,
            'name': '[OdooWooConn] Service product',
            'description_sale': 'A description sale of product.',
            'standard_price': 10,
            'list_price': 100,
            'website_id': self.website.id,
            'website_published': True,
            'weight': 11.1,
            'image_1920': image,
            'product_variant_image_ids': [
                (0, 0, {
                    'name': 'image 1',
                    'image_1920': image,
                }),
                (0, 0, {
                    'name': 'image 2',
                    'image_1920': image,
                }),
            ],
        })
        self.product.product_tmpl_id.is_published = True

    def ensure_woo(self):
        if not self.website.woo_consumer_key:
            return False
        try:
            woo_api = WooAPI(
                url=self.website.woo_url,
                consumer_key=self.website.woo_consumer_key,
                consumer_secret=self.website.woo_consumer_secret,
                version=self.website.woo_version,
            )
            woo_api.get('')
        except ReqConnectionError:
            return False
        return True

    def reset_woo_data_test(self):
        if not self.ensure_woo():
            return
        self.reset_woo_data_test_categ()
        self.reset_woo_data_test_tag()
        self.reset_woo_data_test_product()

    def reset_woo_data_test_categ(self):
        if not self.ensure_woo():
            return
        categ_obj = self.categ.with_context(website=self.website)
        delete_ids = []
        for categ in categ_obj.woo_rpc_get():
            if categ['name'].startswith('[OdooWooConn]'):
                delete_ids.append(categ['id'])
        categ_obj._woo_rpc_delete(delete_ids)

    def reset_woo_data_test_tag(self):
        if not self.ensure_woo():
            return
        tag_obj = self.tag_a.with_context(website=self.website)
        delete_ids = []
        for tag in tag_obj.woo_rpc_get():
            if tag['name'].startswith('[OdooWooConn]'):
                delete_ids.append(tag['id'])
        tag_obj._woo_rpc_delete(delete_ids)

    def reset_woo_data_test_tax(self):
        if not self.ensure_woo():
            return
        tax_obj = self.env['account.tax'].with_context(website=self.website)
        delete_ids = []
        for tax in tax_obj.woo_rpc_get():
            if tax['name'].startswith('[OdooWooConn]'):
                delete_ids.append(tax['id'])
        tax_obj._woo_rpc_delete(delete_ids)

    def reset_woo_data_test_product(self):
        if not self.ensure_woo():
            return
        product_obj = self.product.with_context(website=self.website)
        delete_ids = []
        for product in product_obj.woo_rpc_get():
            if product['name'].startswith('[OdooWooConn]'):
                delete_ids.append(product['id'])
        product_obj._woo_rpc_delete(delete_ids)
