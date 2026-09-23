###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
import base64
import logging

import requests
from odoo import fields, models, tools
from odoo.tools.float_utils import float_round

_log = logging.getLogger(__name__)


class ProductProduct(models.Model):
    _name = 'product.product'
    _inherit = ['product.product', 'website.woo.mixin']

    website_published = fields.Boolean(
        string='Visible on current website',
        related='is_published',
        readonly=False,
    )

    def woo_endpoint_get(self, woo_id=None):
        endpoint = 'products'
        if woo_id:
            endpoint = '%s/%s' % (endpoint, woo_id)
        return endpoint

    def _woo_convert_dict_images(self, website):
        if not self.image_1920:
            return []
        image_tmpl = (
            '%s/website/image/product.product/%s/image_1920/product.jpg')
        images = [
            {'src': image_tmpl % (website.woo_odoo_url, self.id)},
        ]
        image_tmpl = '%s/website/image/product.image/%s/image_1920/product.jpg'
        for img in self.product_variant_image_ids:
            images.append({'src': image_tmpl % (website.woo_odoo_url, img.id)})
        if tools.config.get('test_enable'):
            images = [{'src': 'https://trey.es/logo.png'}]
        return images

    def _woo_convert_dict_relations(self, field, is_object=True):
        res = []
        for item in self.mapped(field):
            if not item.woo_get_id():
                item.woo_rpc_upload()
            if is_object and item:
                res.append({'id': item.woo_get_id()})
                continue
            id = item.woo_get_id()
            if id:
                res.append(item.woo_get_id())
        return res

    def woo_upload_dict_get(self, update_fields=None):
        self.ensure_one()
        if not update_fields:
            update_fields = ['image_1920', 'product_variant_image_ids']
        if 'qty_available' in update_fields:
            return {
                'stock_quantity': self.virtual_available,
            }
        website = self._website_get()
        data = {}
        if not self.is_published:
            if not self.woo_get_id():
                return {}
            data['status'] = 'draft'
        else:
            if 'website_published' in update_fields:
                data['status'] = 'publish'
            images_fields = ['image_1920', 'product_variant_image_ids']
            if any([f for f in images_fields if f in update_fields]):
                data['images'] = self._woo_convert_dict_images(website)
        if not self.woo_sync_export_records(website=website, products=self):
            return {}
        pricelist = (
            self._context.get('pricelist') or website.get_current_pricelist())
        if isinstance(pricelist, models.BaseModel):
            pricelist_id = pricelist.id
        else:
            pricelist_id = pricelist
        self = self.with_context(pricelist=pricelist_id)
        precision = self.env['decimal.precision'].precision_get(
            'Product Price')
        data.update({
            'sku': self.default_code or 'ID%s' % self.id,
            'meta_data': [
                # Update GTIN for Woocommerce plugin
                # link: https://es.wordpress.org/
                # plugins/product-gtin-ean-upc-isbn-for-woocommerce/
                {
                    'key': '_wpm_gtin_code',
                    'value': self.barcode,
                },
            ],
            # Update EAN for Woocommerce plugin
            # link: https://wordpress.org/plugins/ean-for-woocommerce/
            'ean': self.barcode or '',
            'name': self.name,
            'short_description': self.description_sale or '',
            'description': self.website_description or '',
            'manage_stock': bool(self.type in ['consu', 'product']),
            'stock_quantity': self.virtual_available,
            'weight': str(self.weight),
            'regular_price': str(float_round(
                self._get_contextual_price() or self.lst_price, precision)),
            'categories': self._woo_convert_dict_relations('public_categ_ids'),
            'tags': self._woo_convert_dict_relations('tag_ids'),
            'upsell_ids': self._woo_convert_dict_relations(
                'alternative_product_ids.product_variant_id', False),
            'cross_sell_ids': self._woo_convert_dict_relations(
                'accessory_product_ids', False),
        })
        return data

    def woo_sync_export_records(self, website, products=None):
        domain = []
        if not products:
            domain += [
                ('is_published', '=', True),
                '|',
                ('website_id', '=', website.id),
                ('website_id', '=', False),
            ]
        return self.env['product.product'].search(domain)

    def woo_sync_import_record(self, website, data):
        def images_get(url):
            if not url:
                return False
            try:
                response = requests.get(url)
                return base64.b64encode(response.content)
            except Exception:
                _log.warning('Url image not found for %s.' % url)
            return False

        if data['status'] != 'publish':
            return
        self = self.with_context(website=website)
        upsell_ids = []
        for upsell_id in data['upsell_ids']:
            record = self.woo_search_id(upsell_id)
            if not record:
                record = self.woo_sync_import(website, woo_id=upsell_id)
            upsell_ids.append(record.id)
        cross_ids = []
        for cross_id in data['cross_sell_ids']:
            record = self.woo_search_id(cross_id)
            if not record:
                record = self.woo_sync_import(website, woo_id=cross_id)
            cross_ids.append(record.id)
        images = [(d['src'], d['name']) for d in data['images']]
        if data['sku']:
            product = self.search([('default_code', '=', data['sku'])])
            if product.exists():
                _log.warning(
                    'Product "%s" already exists, ignore for import' % (
                        data['sku']))
                return
        public_categ_obj = self.env['product.public.category']
        categs = []
        for categ_id in [c['id'] for c in data['categories']]:
            record = public_categ_obj.woo_search_id(categ_id)
            if not record:
                record = public_categ_obj.woo_sync_import(
                    website, woo_id=categ_id)
            categs.append(record.id)
        tag_obj = self.env['product.template.tag']
        tags = []
        for tag_id in data['tags']:
            record = tag_obj.woo_search_id(tag_id)
            if not record:
                record = tag_obj.woo_sync_import(website, woo_id=tag_id)
            tags.append(record.id)
        return self.create({
            'is_published': data['status'] == 'publish',
            'website_id': website.id,
            'name': data['name'],
            'default_code': data['sku'],
            'type': data['manage_stock'] and 'product' or 'service',
            'website_description': data['description'],
            'description_sale': data['short_description'],
            'weight': float(data['weight'] or 0),
            'lst_price': float(data['regular_price'] or 0),
            'sale_ok': data['on_sale'],
            'purchase_ok': data['purchasable'],
            'image_1920': images and images_get(images[0][0]) or False,
            'accessory_product_ids': [(6, 0, cross_ids)],
            'public_categ_ids': [(6, 0, categs)],
            'tag_ids': [(6, 0, tags)],
            'product_variant_image_ids': [
                (0, 0, {'image_1920': images_get(im[0]), 'name': im[1]})
                for im in images[1:]
            ],
        })

    def action_woo_upload(self):
        websites = self.env['website'].search([('is_woo', '=', True)])
        products = self.filtered(lambda p: p.is_published)
        for website in websites:
            products = self.filtered(
                lambda p: not p.website_id or website == p.website_id)
            products.woo_upload(website)
        return products

    def _woo_is_upload_exception(self, code, message, data):
        if code == 'product_invalid_sku':
            self.woo_set_id(data['resource_id'])
            return False
        if code == 'woocommerce_rest_product_invalid_id':
            self.woo_set_id(False)
            self.woo_rpc_upload(retry=False)
            return False
        return super()._woo_is_upload_exception(code, message, data)
