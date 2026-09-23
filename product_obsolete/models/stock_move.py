###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import fields, models


class StockMove(models.Model):
    _inherit = 'stock.move'

    product_is_obsolete = fields.Boolean(
        string='Product obsolete',
        related='product_id.is_obsolete',
        store=True,
    )
