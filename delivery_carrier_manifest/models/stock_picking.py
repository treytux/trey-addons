###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import fields, models


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    manifest_id = fields.Many2one(
        comodel_name='delivery.carrier.manifest',
        string='Delivery Manifest',
    )
