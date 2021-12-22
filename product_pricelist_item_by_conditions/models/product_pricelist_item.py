###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import fields, models


class ProductPricelistItem(models.Model):
    _inherit = 'product.pricelist.item'

    compute_price = fields.Selection(
        selection_add=[('condition', 'By conditions')],
    )
    condition_ids = fields.One2many(
        comodel_name='product.pricelist.item.condition',
        inverse_name='pricelist_item_id',
        string='Increments/decrements by ranges (%)',
    )
