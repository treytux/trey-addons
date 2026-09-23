###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import fields, models


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    sale_type_id = fields.Many2one(
        comodel_name='sale.order.type',
        string='Sale type',
        related='sale_id.type_id',
        store=True,
    )
