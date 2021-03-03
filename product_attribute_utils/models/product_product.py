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
            text = [
                product.name,
                product.description_sale,
                product.default_code,
                product.barcode,
                ' '.join([c.name for c in product.public_categ_ids]),
                ' '.join([a.display_name for a in product.attribute_line_ids]),
                ' '.join([v.name for v in product.attribute_value_ids]),
            ]
            text = [t for t in text if t and t != '']
            text = ' '.join([
                str(t).lower().strip() for t in text if t.strip()])
            product.search_text = text.translate(str.maketrans({
                '"': '',
                "'": '',
                '´': '',
                '`': '',
            }))

    @api.multi
    def _get_attr_value(self, attribute_id):
        self.ensure_one()
        attrs = self.attribute_value_ids.filtered(
            lambda a: a.attribute_id.id == attribute_id)
        return attrs and attrs.ids[0] or 0

    @api.multi
    def _get_color_attr_value(self, color_attr):
        self.ensure_one()
        values = [
            v.id for v in self.attribute_value_ids if
            v.attribute_id == color_attr]
        return values and values[0] or False
