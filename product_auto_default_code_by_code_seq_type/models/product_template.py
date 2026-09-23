###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import api, fields, models


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    code_seq_type = fields.Selection(
        selection=[
            ('C', '(C) Commercial'),
            ('K', '(K) Kit'),
            ('F', '(F) Manufacturing'),
        ],
        string='Sequence Type',
        default='C',
        required=True,
    )
    default_code = fields.Char(
        string='Default Code',
        compute='_compute_default_code',
        store=True,
    )
    default_code_copy = fields.Char(
        string='Default Code',
        related='default_code',
        readonly=True,
    )
    products_count = fields.Integer(
        string='Variant products count',
        compute='_compute_products_count')

    @api.depends('product_variant_ids')
    def _compute_products_count(self):
        self.products_count = len(self.product_variant_ids.ids)

    @api.depends('product_variant_ids.default_code')
    def _compute_default_code(self):
        if not self.product_variant_ids:
            return
        self.default_code = ','.join(
            list(set([v.default_code for v in self.product_variant_ids
                     if v.default_code and v.active])))
