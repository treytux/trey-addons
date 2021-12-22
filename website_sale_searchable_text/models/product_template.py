###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
import re

from odoo import api, fields, models


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    searchable_text = fields.Text(
        string='Searchable text',
        help='Products search in website will looks for terms in this field',
        compute='_compute_searchable_text',
        store=True,
        translate=True,
    )
    hidden_mapping = fields.Text(
        string='Hidden mapping',
        help='Add more searchable terms here for website products search',
        translate=True,
    )

    @api.model
    def _get_searchable_fields(self, template):
        list_searchable_fields = [
            template.name or '',
            template.website_description or '',
            template.hidden_mapping or '',
        ]
        list_searchable_fields.append(' '.join(
            str(v) for v in template.product_variant_ids.mapped('default_code')
            if v is not False))
        return list_searchable_fields

    @api.multi
    @api.depends(
        'name',
        'default_code',
        'product_variant_ids.default_code',
        'website_description',
        'hidden_mapping',
    )
    def _compute_searchable_text(self):
        for template in self:
            template.searchable_text = re.sub('<.*?>', '', ' '.join(
                self._get_searchable_fields(template)))
