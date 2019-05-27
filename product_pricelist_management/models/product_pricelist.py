###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import fields, models


class ProductPricelist(models.Model):
    _inherit = 'product.pricelist'

    item_ids = fields.One2many(
        domain=[('product_tmpl_id', '=', False)])
