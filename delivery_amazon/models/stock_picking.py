###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import fields, models


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    amazon_shipment_id = fields.Text(
        string='Amazon Shipment Id',
    )
