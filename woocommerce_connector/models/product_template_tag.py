###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
import logging

from odoo import _, api, exceptions, models

_log = logging.getLogger(__name__)


class ProductTemplateTag(models.Model):
    _name = 'product.template.tag'
    _inherit = ['product.template.tag', 'website.woo.mixin']

    @api.constrains('company_id', 'name')
    def _check_name(self):
        domain = [
            ('id', '!=', self.id),
            ('name', '=', self.name),
        ]
        if self.company_id:
            domain += [
                '|',
                ('company_id', '=', False),
                ('company_id', '=', self.company_id.id),
            ]
        ids = self.search(domain)
        if not ids:
            return
        if not self.company_id:
            raise exceptions.ValidationError(_(
                'The public category "%s" already created for website "%s",'
                'only can exists one category name by website.'
            ) % (self.name, ids[0].company_id.name))
        raise exceptions.ValidationError(_(
            'The public category "%s" already created, no can\'t exists more '
            'than one category name for the same website or without website'
        ) % self.name)

    def woo_endpoint_get(self, woo_id=None):
        endpoint = 'products/tags'
        if woo_id:
            endpoint = '%s/%s' % (endpoint, woo_id)
        return endpoint

    def woo_upload_dict_get(self, update_fields=None):
        self.ensure_one()
        return dict(
            name=self.name,
            id_odoo=self.id,
            wpml_language=self.env.user.lang,
        )

    def woo_sync_export_records(self, website, products=None):
        if not products:
            return self.env[self._name]
        return products.mapped('tag_ids')

    def woo_sync_import_record(self, website, data):
        return self.create({
            'name': data['name'],
        })

    def _woo_is_upload_exception(self, code, message, data):
        if code == 'woocommerce_rest_term_invalid':
            self.woo_set_id(False)
            self.woo_rpc_upload()
            return False
        if code == 'term_exists':
            self.woo_set_id(data['resource_id'])
            return False
        return super()._woo_is_upload_exception(code, message, data)
