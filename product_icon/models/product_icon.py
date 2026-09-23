###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import fields, models


class ProductIcon(models.Model):
    _name = 'product.icon'
    _description = 'Product icon'
    _inherit = ['image.mixin']

    name = fields.Char(
        string='Name',
        required=True,
    )
    image_1920 = fields.Image(
        string='Image',
        required=True,
    )
