###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import fields, models


class ProductProduct(models.Model):
    _inherit = 'product.product'

    is_obsolete = fields.Boolean(
        string='Is obsolete',
    )
