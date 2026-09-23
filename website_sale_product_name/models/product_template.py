###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import api, fields, models


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    public_name = fields.Char(
        string='Public name',
        translate=True,
    )
    website_name = fields.Char(
        string='Website name',
        compute='_compute_website_name',
        translate=True,
    )

    @api.depends('public_name', 'name')
    def _compute_website_name(self):
        for product in self:
            product.website_name = product.public_name or product.name

    def _get_combination_info(
            self, combination=False, product_id=False, add_qty=1,
            pricelist=False, parent_combination=False, only_template=False):
        combination_info = super()._get_combination_info(
            combination=combination, product_id=product_id, add_qty=add_qty,
            pricelist=pricelist, parent_combination=parent_combination,
            only_template=only_template)
        product_tmpl_id = combination_info.get('product_template_id', False)
        if not product_tmpl_id:
            return combination_info
        product = self.env['product.template'].browse(product_tmpl_id)
        if not product:
            return combination_info
        combination_info['website_name'] = product.website_name
        return combination_info

    @api.model
    def _search_get_detail(self, website, order, options):
        res = super()._search_get_detail(website, order, options)
        res['search_fields'].append('public_name')
        res['fetch_fields'].append('website_name')
        res['mapping']['name'] = {
            'name': 'website_name', 'type': 'text', 'match': True}
        return res
