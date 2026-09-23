###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import fields, models


class ProductCategory(models.Model):
    _name = 'product.category'
    _inherit = ['product.category', 'ir.translatable.mixin']

    name = fields.Char(
        string='Name',
        index='trigram',
        required=True,
        translate=True,
    )


class ProductPublicCategory(models.Model):
    _name = 'product.public.category'
    _inherit = ['product.public.category', 'ir.translatable.mixin']
