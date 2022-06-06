###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import fields, models


class EventProduct(models.Model):
    _inherit = 'event.product'

    stock_move_ids = fields.One2many(
        comodel_name='stock.move',
        inverse_name='event_product_id',
        string='Stock move',
    )
