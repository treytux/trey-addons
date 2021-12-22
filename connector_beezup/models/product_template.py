###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import fields, models


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    export_to_beezup = fields.Boolean(
        related='product_variant_id.export_to_beezup',
        readonly=False,
    )
