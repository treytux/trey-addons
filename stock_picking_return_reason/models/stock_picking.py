###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import fields, models


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    return_reason_id = fields.Many2one(
        comodel_name='stock.picking.return.reason',
        string='Return reason',
    )
