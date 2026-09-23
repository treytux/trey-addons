###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import fields, models


class ProductCategory(models.Model):
    _name = 'product.category'
    _inherit = ['product.category', 'website.published.mixin']

    is_published = fields.Boolean(
        default=True,
    )
