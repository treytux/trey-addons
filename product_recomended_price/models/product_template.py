###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import fields, models


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    recomended_price = fields.Monetary(
        string='Recomended price',
        track_visibility='always',
    )
