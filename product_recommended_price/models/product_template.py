###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import fields, models


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    recommended_price = fields.Monetary(
        string='Recommended price',
        tracking=True,
        help='Recommended price for this product',
    )
