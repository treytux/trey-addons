###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import models


class ProductProduct(models.Model):
    _name = 'product.product'
    _inherit = ['product.product', 'ir.translatable.mixin']
