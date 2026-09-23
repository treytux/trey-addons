###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import api, fields, models


class ProductProduct(models.Model):
    _inherit = 'product.product'

    plastic_non_recycled_percentage = fields.Float(
        string='Plastic percentage',
        help='Percentage of plastic in the product',
    )
    plastic_weight = fields.Float(
        string='Plastic weight',
        help='Weight of plastic of the product in kilos',
    )
    plastic_weight_non_recycled = fields.Float(
        compute='_compute_plastic_weight_non_recycled',
        string='Plastic weight non recycled',
        help='Weight of plastic non recycled of the product in kilos',
    )

    @api.depends('plastic_weight', 'plastic_non_recycled_percentage')
    def _compute_plastic_weight_non_recycled(self):
        for product in self:
            if (not product.plastic_non_recycled_percentage
                    or not product.plastic_weight):
                product.plastic_weight_non_recycled = 0.0
            product.plastic_weight_non_recycled = (
                product.plastic_weight
                * (product.plastic_non_recycled_percentage / 100))
