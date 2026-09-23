###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
import json

from odoo import api, fields, models


class ProductTemplate(models.Model):
    _name = 'product.template'
    _inherit = ['product.template', 'website.woo.mixin']

    woo_variant_ids = fields.Text(
        string='Woo IDS',
        compute='_compute_woo_variant_ids',
        help=(
            'This value cannot be modified because it is computed from the '
            'variants. Please modify the variants.'
        ),
        readonly=True,
    )

    @api.depends('woo_ids', 'product_variant_ids.woo_ids')
    def _compute_woo_variant_ids(self):
        for tmpl in self:
            tmpl.woo_variant_ids = json.dumps(
                {v.id: v.woo_ids for v in tmpl.product_variant_ids},
                indent=4, sort_keys=True)

    def woo_upload_dict_get(self, update_fields=None):
        return self.product_variant_id.woo_upload_dict_get(update_fields)

    def woo_rpc_upload(self, update_fields=None):
        return self.product_variant_id.woo_rpc_upload(update_fields)

    def woo_sync_export_records(self, website, products=None):
        if products is None:
            products = self.product_variant_id
        return self.product_variant_id.woo_sync_export_records(
            website, products).mapped('product_tmpl_id')

    def woo_sync_import_record(self, website, data):
        return self.product_variant_id.woo_sync_import_record(website, data)

    def action_woo_upload(self):
        return self.product_variant_id.action_woo_upload()

    def _woo_is_upload_exception(self, code, message, data):
        return self.product_variant_id._woo_is_upload_exception(
            code, message, data)
