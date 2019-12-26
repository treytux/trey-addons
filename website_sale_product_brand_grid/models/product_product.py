###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import api, fields, models


class ProductProduct(models.Model):
    _inherit = 'product.product'

    search_text = fields.Char(
        string='Search text',
        compute='_compute_search_text')

    @api.multi
    @api.depends(
        'name',
        'description_sale',
        'default_code',
        'barcode',
        'public_categ_ids.name',
        'attribute_line_ids.display_name',
        'attribute_value_ids.name',
    )
    def _compute_search_text(self):
        for product in self:
            product.search_text = '%s %s %s %s %s %s %s' % (
                product.name,
                product.description_sale and product.description_sale or '',
                product.default_code and product.default_code or '',
                product.barcode or '',
                ' '.join([cat.name for cat in product.public_categ_ids]),
                ' '.join([
                    att.display_name for att in product.attribute_line_ids]),
                ' '.join([val.name for val in product.attribute_value_ids]),
            )
            product.search_text = product.search_text.lower()
            product.search_text = product.search_text.translate(str.maketrans({
                '"': '',
                "'": '',
                '´': '',
                '`': '',
            }))
