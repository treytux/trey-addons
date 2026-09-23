###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import api, fields, models


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    default_code_template = fields.Char(
        string='Internal Reference',
        compute='_compute_default_code_template',
        store=True,
        readonly=False,
    )

    @api.depends('product_variant_ids', 'product_variant_ids.default_code')
    def _compute_default_code_template(self):
        for template in self:
            if len(template.product_variant_ids) == 1:
                template.default_code_template = template.default_code

    @api.depends('product_variant_ids', 'product_variant_ids.default_code')
    def _compute_default_code(self):
        super()._compute_default_code()
        for template in self:
            if len(template.product_variant_ids) > 1:
                template.default_code = template.default_code_template

    def _set_default_code(self):
        super()._set_default_code()
        for template in self:
            template.default_code_template = template.default_code
