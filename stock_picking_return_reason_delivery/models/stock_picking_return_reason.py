###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import fields, models


class StockPickingReturnReason(models.Model):
    _inherit = 'stock.picking.return.reason'

    carrier_id = fields.Many2one(
        comodel_name='delivery.carrier',
        string='Delivery method',
    )
