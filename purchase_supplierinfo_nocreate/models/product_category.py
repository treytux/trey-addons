###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import fields, models


class ProductCategory(models.Model):
    _inherit = 'product.category'

    disable_supplierinfo_creation = fields.Boolean(
        string='Disable Supplierinfo Creation',
        default=True,
        help='If checked, supplier information will not be created automatically '
             'when confirming purchase orders for products in this category.',
    )
