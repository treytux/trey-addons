###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import fields, models


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    invoice_carrier_id = fields.Many2one(
        comodel_name='account.invoice',
        string='Invoice carrier',
    )
