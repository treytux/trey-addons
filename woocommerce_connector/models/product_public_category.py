###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
import base64
import logging

import requests
from odoo import _, api, exceptions, models

_log = logging.getLogger(__name__)


class ProductPublicCategory(models.Model):
    _name = 'product.public.category'
    _inherit = ['product.public.category', 'website.woo.mixin']

    @api.constrains('website_id', 'name', 'parent_id')
    def _check_name(self):
        domain = [
            ('id', '!=', self.id),
            ('parent_id', '=', self.parent_id.id),
            ('name', '=', self.name),
        ]
        if self.website_id:
            domain += [
                '|',
                ('website_id', '=', False),
                ('website_id', '=', self.website_id.id),
            ]
        ids = self.search(domain, order='parent_id ASC, id ASC')
        if not ids:
            return
        if not self.website_id:
            raise exceptions.ValidationError(_(
                'The public category "%s" already created for website "%s",'
                'only can exists one category name by website.'
            ) % (self.name, ids[0].website_id.name))
        raise exceptions.ValidationError(_(
            'The public category "%s" already created, no can\'t exists more '
            'than one category name for the same website or without website'
        ) % (self.name))

    def woo_endpoint_get(self, woo_id=None):
        endpoint = 'products/categories'
        if woo_id:
            endpoint = '%s/%s' % (endpoint, woo_id)
        return endpoint

    def woo_upload_dict_get(self, update_fields=None):
        self.ensure_one()
        parent_id = None
        if self.parent_id:
            if not self.parent_id.woo_get_id():
                self.parent_id.woo_rpc_upload()
            parent_id = self.parent_id.woo_get_id()
        return {
            'name': self.name,
            'parent': parent_id,
            'id_odoo': self.id,
            'wpml_language': self.env.user.lang,
            'menu_order': self.sequence,
        }

    def woo_sync_export_records(self, website, products=None):
        if products:
            categs = products.mapped('public_categ_ids')
            if categs:
                return self.search([
                    ('id', 'child_of', categs.ids),
                ])
            return categs
        return self.env[self._name].search([
            ('website_id', '=', website.id),
        ])

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

        parent = False
        self = self.with_context(website=website)
        if data['parent']:
            parent = self.woo_search_id(data['parent'])
            if not parent:
                parent = self.woo_sync_import(website, woo_id=data['parent'])
        image = data['image'] or {}
        return self.create({
            'website_id': website.id,
            'name': data['name'],
            'parent_id': parent and parent.id or False,
            'sequence': data['menu_order'],
            'image_1920': images_get(image.get('src')),
        })

    def _woo_sync_export_get(self, website, products=None):
        if self._context.get('res_model') == 'product.public.category':
            categs = self.env['product.public.category'].browse(
                self._context['res_ids'])
            return {
                'upload': categs,
                'delete': [],
            }
        return super()._woo_sync_export_get(website, products)

    def _woo_is_upload_exception(self, code, message, data):
        if code == 'woocommerce_rest_term_invalid':
            self.woo_set_id(False)
            self.woo_rpc_upload()
            return False
        if code == 'term_exists':
            self.woo_set_id(data['resource_id'])
            return False
        if code == 'missing_parent':
            if not self.parent_id.woo_get_id():
                return True
            self.parent_id.woo_set_id(False)
            self.parent_id.woo_rpc_upload()
            self.woo_rpc_upload(retry=False)
            return False
        return super()._woo_is_upload_exception(code, message, data)
