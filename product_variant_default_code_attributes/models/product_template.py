###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import api, fields, models


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    default_code_prefix = fields.Char(
        'Internal reference prefix',
        inverse='_set_default_code_prefix',
        store=True,
    )

    @api.one
    def _set_default_code_prefix(self):
        product_variant = self.product_variant_id
        variants = product_variant.product_tmpl_id.product_variant_ids
        condition = (
            self.product_variant_count > 1 and self.default_code_prefix)
        for variant in variants:
            variant.default_code = (
                condition and '%s%s' % (
                    self.default_code_prefix,
                    ''.join(variant.attribute_value_ids.mapped('name')),
                ) or False)
