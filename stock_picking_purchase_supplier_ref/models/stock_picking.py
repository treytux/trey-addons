###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import fields, models


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    partner_ref = fields.Char(
        related='purchase_id.partner_ref',
        string='Supplier reference',
        store=True,
    )
