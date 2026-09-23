###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import api, fields, models, tools


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    searchable_text = fields.Text(
        string='Searchable text',
        help='Website product search will look for terms in this field',
        compute='_compute_searchable_text',
        store=True,
    )
    hidden_mapping = fields.Text(
        string='Hidden mapping',
        help='Add more searchable terms here for website products search',
        translate=True,
    )

    def _get_searchable_fields(self):
        self.ensure_one()
        values = [
            self.name or '',
            tools.html2plaintext(self.website_description or ''),
            self.hidden_mapping or '',
        ]
        codes = self.product_variant_ids.mapped('default_code')
        values.append(' '.join(code for code in codes if code))
        return values

    @api.depends(
        'name',
        'default_code',
        'product_variant_ids.default_code',
        'website_description',
        'hidden_mapping')
    def _compute_searchable_text(self):
        for template in self:
            template.searchable_text = ' '.join(
                template._get_searchable_fields())

    @api.model
    def _search_get_detail(self, website, order, options):
        detail = super()._search_get_detail(website, order, options)
        if 'searchable_text' not in detail['search_fields']:
            detail['search_fields'].append('searchable_text')
        return detail
