###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import fields, models


class WooCommerceSync(models.TransientModel):
    _name = 'woocommerce.sync'
    _description = 'Wizard for sync data to WooCommerce'

    def _default_website_id(self):
        websites = self.env['website'].search([('is_woo', '=', True)])
        if len(websites) == 1:
            return websites
        return False

    website_id = fields.Many2one(
        comodel_name='website',
        string='Website',
        domain='[("is_woo", "=", True)]',
        default=_default_website_id,
    )
    state = fields.Selection(
        selection=[
            ('step-1', 'To count'),
            ('step-2', 'To sync'),
        ],
        string='State',
        default='step-1',
    )
    method = fields.Selection(
        selection=[
            ('import', 'Import data from WooCommerce'),
            ('export', 'Export data to WooCommerce'),
        ],
        string='Method',
        required=True,
        default='export',
    )
    is_product = fields.Boolean(
        string='Product',
        default=True,
    )
    product_count = fields.Integer(
        string='Products',
    )
    del_product_count = fields.Integer(
        string='Products',
    )
    import_product_count = fields.Integer(
        string='Products',
    )
    is_public_category = fields.Boolean(
        string='Public category',
        default=True,
    )
    public_category_count = fields.Integer(
        string='Categories',
    )
    del_public_category_count = fields.Integer(
        string='Categories',
    )
    import_public_category_count = fields.Integer(
        string='Categories',
    )
    is_product_tag = fields.Boolean(
        string='Product tag',
        default=True,
    )
    product_tag_count = fields.Integer(
        string='Tags',
    )
    del_product_tag_count = fields.Integer(
        string='Tags',
    )
    import_product_tag_count = fields.Integer(
        string='Tags',
    )
    is_tax = fields.Boolean(
        string='Tax',
        default=True,
    )
    import_tax_count = fields.Integer(
        string='Taxs',
    )

    def _reopen_view(self):
        return {
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'view_type': 'form',
            'res_id': self.ids[0],
            'res_model': self._name,
            'target': 'new',
            'context': {},
        }

    def get_products(self):
        if self._context.get('res_model') == 'product.product':
            return self.env['product.product'].browse(self._context['res_ids'])
        if self._context.get('res_model') == 'product.template':
            tmpls = self.env['product.template'].browse(
                self._context['res_ids'])
            return tmpls.mapped('product_variant_ids')
        return None

    def _action_count_import(self):
        def count_model(model, params):
            obj = self.env[model]
            count = 0
            page = 1
            items = []
            while page == 1 or items:
                items = obj.woo_rpc_call(
                    'get', obj.woo_endpoint_get(),
                    {'params': {**params, **{'per_page': 100, 'page': page}}},
                    website=self.website_id)
                count += len(items)
                page += 1
            return count

        if self.is_product:
            self.import_product_count = count_model(
                'product.product', {'status': 'publish'})
        if self.is_product or self.is_public_category:
            self.import_public_category_count = count_model(
                'product.public.category', {'status': 'publish'})
        if self.is_product or self.is_product_tag:
            self.import_product_tag_count = count_model(
                'product.template.tag', {'status': 'publish'})
        if self.is_tax:
            self.import_tax_count = count_model(
                'website.woo.mapp.tax', {})

    def _action_count_export(self):
        products = self.get_products()
        if self.is_product:
            info_products = self.env['product.product']._woo_sync_export_get(
                self.website_id, products)
        else:
            info_products = {'upload': [], 'delete': []}
        if self.is_public_category:
            categ_obj = self.env['product.public.category']
            info_categs = categ_obj._woo_sync_export_get(
                self.website_id, products or info_products['upload'])
        else:
            info_categs = {'upload': [], 'delete': []}
        if self.is_product_tag:
            info_tags = self.env['product.template.tag']._woo_sync_export_get(
                self.website_id, products or info_products['upload'])
        else:
            info_tags = {'upload': [], 'delete': []}
        self.write({
            'product_count': len(info_products['upload']),
            'public_category_count': len(info_categs['upload']),
            'product_tag_count': len(info_tags['upload']),
            'del_product_count': len(info_products['delete']),
            'del_public_category_count': len(info_categs['delete']),
            'del_product_tag_count': len(info_tags['delete']),
        })

    def action_back(self):
        self.state = 'step-1'
        return self._reopen_view()

    def action_count(self):
        self.state = 'step-2'
        if self.method == 'import':
            self._action_count_import()
        elif self.method == 'export':
            self._action_count_export()
        return self._reopen_view()

    def action_sync(self):
        products = self.get_products()

        def sync(model, params=None):
            if self.method == 'import':
                self.env[model].woo_sync_import(self.website_id, params=params)
            elif self.method == 'export':
                self.env[model].woo_sync_export(self.website_id, products)

        if self.is_product or self.is_public_category:
            sync('product.public.category', params={'status': 'publish'})
        if self.is_product or self.is_product_tag:
            sync('product.template.tag', params={'status': 'publish'})
        if self.is_tax and self.method == 'import':
            sync('website.woo.mapp.tax')
        if self.is_product:
            sync('product.product', params={'status': 'publish'})
