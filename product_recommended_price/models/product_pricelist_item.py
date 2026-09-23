###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import fields, models


class ProductPricelistItem(models.Model):
    _inherit = 'product.pricelist.item'

    base = fields.Selection(
        selection_add=[
            ('recommended_price', 'Recommended price'),
        ],
        ondelete={
            'recommended_price': 'set default',
        },
    )
