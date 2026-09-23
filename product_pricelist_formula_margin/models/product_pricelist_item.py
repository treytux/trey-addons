###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import fields, models


class ProductPricelistItem(models.Model):
    _inherit = 'product.pricelist.item'

    compute_price = fields.Selection(
        selection_add=[
            ('margin', 'Margin'),
        ],
    )
    percent_margin = fields.Float(
        string='Margin (%)',
    )
