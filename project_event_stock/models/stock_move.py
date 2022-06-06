###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import fields, models


class StockMove(models.Model):
    _inherit = 'stock.move'

    event_id = fields.Many2one(
        comodel_name='event.event',
        string='Event',
    )
    event_product_id = fields.Many2one(
        comodel_name='event.product',
        string='Event product',
    )
