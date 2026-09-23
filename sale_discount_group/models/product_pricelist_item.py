###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import fields, models


class ProductPricelistItem(models.Model):
    _inherit = 'product.pricelist.item'

    apply_discount_group = fields.Boolean(
        default=True,
        string='Apply discount group',
    )
