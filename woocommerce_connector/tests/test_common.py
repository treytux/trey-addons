###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
import base64
import os

from odoo.tests.common import HttpCase

# Important note! Launch Docker compose and create consumer key and secret
# Requierement:
# - You must be using WooCommerce 2.1 or newer and the REST API must be enabled
#   go to WooCommerce > Settings > Advanced > Legacy API and check the option
#   for enabling it
# - You must enable pretty permalinks in Settings > Permalinks (default
#   permalinks will not work).


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
            # 'woo_url': 'http://localhost:8080',
            # 'woo_odoo_url': 'http://192.168.16.1:8069',
            # 'woo_version': 'wc/v3',
            # 'woo_consumer_key': 'ck_f11f85db9dbd3b9809cea7501210af0c0d645d44',
            # 'woo_consumer_secret': (
            #     'cs_e8bdd92d641b3ff8ee98b250d30ad138a5cc1ff0'
            # ),
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
            'image': image,
            'product_image_ids': [
                (0, 0, {'image': image}),
                (0, 0, {'image': image}),
            ],
        })

    def ensure_woo(self):
        if not self.website.woo_consumer_key:
            self.skipTest('Without WooCommerce credentials')
            return False
        return True

    def reset_woo_data_test(self):
        self.reset_woo_data_test_categ()
        self.reset_woo_data_test_tag()
        self.reset_woo_data_test_product()

    def reset_woo_data_test_categ(self):
        categ_obj = self.categ.with_context(website=self.website)
        delete_ids = []
        for categ in categ_obj.woo_rpc_get():
            if categ['name'].startswith('[OdooWooConn]'):
                delete_ids.append(categ['id'])
        categ_obj._woo_rpc_delete(delete_ids)

    def reset_woo_data_test_tag(self):
        tag_obj = self.tag_a.with_context(website=self.website)
        delete_ids = []
        for tag in tag_obj.woo_rpc_get():
            if tag['name'].startswith('[OdooWooConn]'):
                delete_ids.append(tag['id'])
        tag_obj._woo_rpc_delete(delete_ids)

    def reset_woo_data_test_tax(self):
        tax_obj = self.env['account.tax'].with_context(website=self.website)
        delete_ids = []
        for tax in tax_obj.woo_rpc_get():
            if tax['name'].startswith('[OdooWooConn]'):
                delete_ids.append(tax['id'])
        tax_obj._woo_rpc_delete(delete_ids)

    def reset_woo_data_test_product(self):
        product_obj = self.product.with_context(website=self.website)
        delete_ids = []
        for product in product_obj.woo_rpc_get():
            if product['name'].startswith('[OdooWooConn]'):
                delete_ids.append(product['id'])
        product_obj._woo_rpc_delete(delete_ids)
